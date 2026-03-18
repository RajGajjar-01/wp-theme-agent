import json
import logging

from app.agent.clients import GLM_MODEL, glm_client
from app.agent.llm_utils import llm_parse_list
from app.agent.models import GlobalAnalysis, PageAnalysis, PlanItem
from app.agent.prompts.planner import PLANNER_SYSTEM
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def _build_planner_context(
    global_analysis: GlobalAnalysis,
    pages: list[PageAnalysis],
    theme_name: str,
    theme_slug: str,
    author: str,
) -> str:
    ga_dict = global_analysis.model_dump()
    ga_dict.pop("shared_header_html", None)
    ga_dict.pop("shared_footer_html", None)

    pages_summary = [p.model_dump() for p in pages]

    return (
        f"Theme Name: {theme_name}\n"
        f"Theme Slug: {theme_slug}\n"
        f"Author: {author}\n\n"
        f"━━━ GLOBAL ANALYSIS ━━━\n{json.dumps(ga_dict, indent=2)}\n\n"
        f"━━━ PER-PAGE ANALYSIS ━━━\n{json.dumps(pages_summary, indent=2)}"
    )


async def planner_node(state: AgentState, writer) -> dict:
    global_analysis: GlobalAnalysis = state["global_analysis"]
    pages: list[PageAnalysis] = state["pages"]
    errors: list[str] = list(state.get("errors", []))

    writer({"node": "planner", "status": "running", "message": "Planning WordPress file structure..."})

    context = _build_planner_context(
        global_analysis,
        pages,
        state["theme_name"],
        state["theme_slug"],
        state["author"],
    )

    try:
        plan = await llm_parse_list(
            client=glm_client,
            model=GLM_MODEL,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user", "content": context},
            ],
            item_model=PlanItem,
        )
    except Exception as e:
        logger.error("Planner failed: %s", e)
        errors.append(f"Planner failed: {e}")
        plan = _fallback_plan(global_analysis, pages)

    shared = sum(1 for p in plan if p.source == "global" and p.type == "php")
    page_templates = sum(
        1 for p in plan
        if p.source not in ("global", "css_files", "generated", "pages")
        and p.file.endswith(".php")
        and "template-parts" not in p.file
        and "inc/" not in p.file
    )
    template_parts = sum(1 for p in plan if "template-parts" in p.file)
    inc_files = sum(1 for p in plan if "inc/" in p.file)
    assets = sum(1 for p in plan if p.type in ("css", "js"))
    other = len(plan) - shared - page_templates - template_parts - inc_files - assets

    writer({
        "node": "planner",
        "status": "complete",
        "message": (
            f"{len(plan)} files planned: {shared} shared, {page_templates} page templates, "
            f"{template_parts} template-parts, {inc_files} inc, {assets} assets"
            + (f", {other} other" if other > 0 else "")
        ),
    })

    return {
        "plan": plan,
        "errors": errors,
    }


def _fallback_plan(
    global_analysis: GlobalAnalysis,
    pages: list[PageAnalysis],
) -> list[PlanItem]:
    plan: list[PlanItem] = [
        PlanItem(file="style.css", source="css_files", type="css", description="Theme header and all CSS"),
        PlanItem(file="functions.php", source="global", type="php", description="Theme setup and configuration"),
        PlanItem(file="header.php", source="global", type="php", description="Site header with navigation"),
        PlanItem(file="footer.php", source="global", type="php", description="Site footer"),
        PlanItem(file="sidebar.php", source="global", type="php", description="Widget area"),
        PlanItem(file="index.php", source="global", type="php", description="Main blog listing template"),
        PlanItem(file="page.php", source="global", type="php", description="Generic page template"),
        PlanItem(file="single.php", source="global", type="php", description="Single post template"),
        PlanItem(file="archive.php", source="global", type="php", description="Archive template"),
        PlanItem(file="search.php", source="global", type="php", description="Search results template"),
        PlanItem(file="404.php", source="global", type="php", description="Not found page"),
    ]

    for page in pages:
        if page.page_type == "homepage":
            plan.append(PlanItem(
                file="front-page.php",
                source=page.source_file,
                type="php",
                description=f"Homepage template from {page.source_file}",
            ))
        elif page.page_type == "static_page" and page.wp_page_slug:
            plan.append(PlanItem(
                file=f"page-{page.wp_page_slug}.php",
                source=page.source_file,
                type="php",
                description=f"{page.title} page template from {page.source_file}",
            ))

    for comp in global_analysis.repeating_components:
        plan.append(PlanItem(
            file=comp.template_part,
            source=comp.found_in[0] if comp.found_in else "global",
            type="php",
            description=comp.description,
        ))

    plan.append(PlanItem(file="template-parts/content-none.php", source="global", type="php", description="No posts found message"))
    plan.append(PlanItem(file="inc/enqueue.php", source="global", type="php", description="Enqueue scripts and styles"))
    plan.append(PlanItem(file="inc/template-functions.php", source="global", type="php", description="Helper functions"))
    plan.append(PlanItem(file="js/navigation.js", source="generated", type="js", description="Mobile navigation toggle"))

    static_pages = [p for p in pages if p.page_type == "static_page" and p.wp_page_slug]
    if static_pages:
        plan.append(PlanItem(file="pages.xml", source="pages", type="xml", description="WordPress WXR import file"))

    return plan
