import json
import logging

from langgraph.config import get_stream_writer

from app.agent.clients import GLM_MODEL, glm_client
from app.agent.llm_utils import llm_parse
from app.agent.models import GlobalAnalysis, PageAnalysis
from app.agent.prompts.analyzer import GLOBAL_ANALYSIS_SYSTEM, PAGE_ANALYSIS_SYSTEM
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def _build_files_context(uploaded_files: dict[str, str]) -> str:
    parts: list[str] = []
    for filename, content in sorted(uploaded_files.items()):
        parts.append(f"━━━ FILE: {filename} ━━━\n{content}\n")
    return "\n".join(parts)


async def analyzer_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    uploaded_files = state["uploaded_files"]
    errors: list[str] = list(state.get("errors", []))

    html_files = {k: v for k, v in uploaded_files.items() if k.endswith(".html")}
    all_context = _build_files_context(uploaded_files)

    writer({
        "node": "analyzer",
        "status": "running",
        "message": f"Detected {len(html_files)} HTML page(s), {len(uploaded_files) - len(html_files)} asset file(s)",
    })

    # --- Level 1: Global Analysis ---
    writer({"node": "analyzer", "status": "running", "message": "Running global analysis across all files..."})

    try:
        global_analysis = await llm_parse(
            client=glm_client,
            model=GLM_MODEL,
            messages=[
                {"role": "system", "content": GLOBAL_ANALYSIS_SYSTEM},
                {"role": "user", "content": all_context},
            ],
            response_model=GlobalAnalysis,
        )
    except Exception as e:
        logger.error("Global analysis failed: %s", e)
        errors.append(f"Global analysis failed: {e}")
        global_analysis = GlobalAnalysis(summary="Analysis failed — using defaults")

    components_count = len(global_analysis.repeating_components)
    writer({
        "node": "analyzer",
        "status": "running",
        "message": f"Found {components_count} repeating component(s), {len(global_analysis.shared_nav_items)} nav item(s)",
    })

    # --- Level 2: Per-Page Analysis ---
    pages: list[PageAnalysis] = []

    for filename in sorted(html_files.keys()):
        writer({"node": "analyzer", "status": "running", "message": f"Analyzing {filename}..."})

        page_context = (
            f"Filename: {filename}\n\n"
            f"━━━ THIS PAGE HTML ━━━\n{html_files[filename]}\n\n"
            f"━━━ KNOWN REPEATING COMPONENTS ━━━\n"
            f"{json.dumps([c.model_dump() for c in global_analysis.repeating_components], indent=2)}"
        )

        try:
            page = await llm_parse(
                client=glm_client,
                model=GLM_MODEL,
                messages=[
                    {"role": "system", "content": PAGE_ANALYSIS_SYSTEM},
                    {"role": "user", "content": page_context},
                ],
                response_model=PageAnalysis,
            )
            page.source_file = filename
            pages.append(page)

            writer({
                "node": "analyzer",
                "status": "running",
                "message": f"  → {filename} → {page.page_type} ({page.wp_template})",
            })
        except Exception as e:
            logger.error("Page analysis failed for %s: %s", filename, e)
            errors.append(f"Page analysis failed for {filename}: {e}")

    page_summary = ", ".join(f"{p.source_file}→{p.wp_template}" for p in pages)
    writer({
        "node": "analyzer",
        "status": "complete",
        "message": f"{len(pages)} page(s) analyzed, {components_count} template part(s) identified. Mapping: {page_summary}",
    })

    return {
        "global_analysis": global_analysis,
        "pages": pages,
        "errors": errors,
    }
