import asyncio
import json
import logging
import re
from pathlib import Path

from langgraph.config import get_stream_writer

from app.agent.clients import MINIMAX_MODEL, minimax_client
from app.agent.models import GlobalAnalysis, PageAnalysis, PlanItem
from app.agent.prompts.generator import GENERATOR_SYSTEM, WP_RULES
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def _determine_wp_rules(item: PlanItem, theme_slug: str, theme_name: str, author: str, function_prefix: str) -> str:
    file = item.file
    rules_key = "generic"

    if file == "style.css":
        rules_key = "style_css"
    elif file == "functions.php":
        rules_key = "functions"
    elif file == "header.php":
        rules_key = "header"
    elif file == "footer.php":
        rules_key = "footer"
    elif file == "sidebar.php":
        rules_key = "sidebar"
    elif file == "search.php":
        rules_key = "search"
    elif file == "archive.php":
        rules_key = "archive"
    elif file == "404.php":
        rules_key = "404"
    elif file == "single.php":
        rules_key = "single_post"
    elif file in ("index.php",) and item.source != "global":
        rules_key = "blog_listing"
    elif file == "index.php":
        rules_key = "blog_listing"
    elif file.startswith("template-parts/"):
        rules_key = "template_part"
    elif file.startswith("page-") or file == "front-page.php":
        rules_key = "page_template"
    elif file == "inc/enqueue.php":
        rules_key = "enqueue"
    elif file == "inc/template-functions.php":
        rules_key = "template_functions"
    elif file == "js/navigation.js":
        rules_key = "navigation_js"
    elif file == "pages.xml":
        rules_key = "pages_xml"

    raw = WP_RULES.get(rules_key, WP_RULES["generic"])
    return raw.replace("{theme_slug}", theme_slug).replace(
        "{theme_name}", theme_name
    ).replace("{author}", author).replace("{function_prefix}", function_prefix)


def _build_source_html(item: PlanItem, uploaded_files: dict[str, str], global_analysis: GlobalAnalysis) -> str:
    if item.source in uploaded_files:
        return uploaded_files[item.source]
    elif item.source == "css_files":
        css_parts = [
            uploaded_files[f] for f in global_analysis.css_files if f in uploaded_files
        ]
        return "\n\n".join(css_parts) if css_parts else "No CSS files found — generate clean, modern CSS."
    elif item.source == "global":
        return "No specific source — generate from global context."
    elif item.source == "generated":
        return "No specific source — generate from scratch."
    elif item.source == "pages":
        return "Generate from page analysis data."
    else:
        return f"Source: {item.source} (not found in uploads)"


def _build_template_parts_list(plan: list[PlanItem]) -> str:
    parts = [p.file for p in plan if p.file.startswith("template-parts/")]
    if not parts:
        return "No template parts planned."
    return "\n".join(f"- {p}" for p in parts)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:php|css|javascript|js|xml|html)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


async def generator_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    # LangGraph serializes Pydantic models to dicts - re-validate them
    plan: list[PlanItem] = [
        PlanItem(**p) if isinstance(p, dict) else p for p in state["plan"]
    ]
    uploaded_files = state["uploaded_files"]
    global_analysis_raw = state["global_analysis"]
    global_analysis: GlobalAnalysis = (
        GlobalAnalysis(**global_analysis_raw) if isinstance(global_analysis_raw, dict) else global_analysis_raw
    )
    pages: list[PageAnalysis] = [
        PageAnalysis(**p) if isinstance(p, dict) else p for p in state["pages"]
    ]
    errors: list[str] = list(state.get("errors", []))

    theme_name = state["theme_name"]
    theme_slug = state["theme_slug"]
    author = state["author"]
    function_prefix = theme_slug.replace("-", "_")

    colors_str = json.dumps(global_analysis.colors.model_dump())
    fonts_str = json.dumps(global_analysis.fonts.model_dump())
    nav_str = json.dumps(global_analysis.shared_nav_items)
    js_libs_str = json.dumps(global_analysis.js_libraries)
    template_parts_list = _build_template_parts_list(plan)

    # Build pages context for pages.xml generation
    pages_context = json.dumps([p.model_dump() for p in pages], indent=2)

    generated_files: dict[str, str] = dict(state.get("generated_files", {}))
    total = len(plan)

    async def _generate_single_file(item: PlanItem, i: int) -> tuple[str, str] | None:
        writer({"node": "generator", "status": "running", "message": f"Generating {item.file} ({i}/{total})..."})

        source_html = _build_source_html(item, uploaded_files, global_analysis)
        wp_rules = _determine_wp_rules(item, theme_slug, theme_name, author, function_prefix)

        # For pages.xml, add pages data to source
        if item.file == "pages.xml":
            source_html = f"Pages to create:\n{pages_context}"

        base_file_content = "Not applicable (create action or base file missing)."
        if item.action == "modify":
            base_path = Path("app/agent/base_theme") / item.file
            if base_path.is_file():
                try:
                    with open(base_path, "r", encoding="utf-8") as bf:
                        base_file_content = bf.read()
                except Exception as e:
                    logger.warning("Could not read base file %s: %s", item.file, e)

        prompt = GENERATOR_SYSTEM.format(
            file_path=item.file,
            file_type=item.type,
            action=item.action,
            base_file_content=base_file_content,
            source_html=source_html,
            theme_name=theme_name,
            theme_slug=theme_slug,
            function_prefix=function_prefix,
            author=author,
            colors=colors_str,
            fonts=fonts_str,
            nav_items=nav_str,
            js_libraries=js_libs_str,
            template_parts_list=template_parts_list,
            wp_rules=wp_rules,
        )

        try:
            resp = await minimax_client.chat.completions.create(
                model=MINIMAX_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Generate the complete content for: {item.file}\nDescription: {item.description}"},
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content or ""
            content = _strip_fences(content)
            return item.file, content
        except Exception as e:
            logger.error("Generation failed for %s: %s", item.file, e)
            errors.append(f"Generation failed for {item.file}: {e}")
            return item.file, f"<!-- Generation failed: {e} -->"

    gen_tasks = [_generate_single_file(item, i) for i, item in enumerate(plan, 1)]
    gen_results = await asyncio.gather(*gen_tasks)
    
    for res in gen_results:
        if res:
            file_path, content = res
            generated_files[file_path] = content

    writer({
        "node": "generator",
        "status": "complete",
        "message": f"All {total} files generated",
    })

    return {
        "generated_files": generated_files,
        "errors": errors,
    }
