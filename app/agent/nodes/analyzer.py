import asyncio
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
    all_context = _build_files_context(html_files)

    logger.info("Analyzer node started. Detected %d HTML files out of %d total files.", len(html_files), len(uploaded_files))

    writer({
        "node": "analyzer",
        "status": "running",
        "message": f"Detected {len(html_files)} HTML page(s), {len(uploaded_files) - len(html_files)} asset file(s)",
    })

    # --- Level 1: Global Analysis ---
    logger.info("Starting Global Analysis to identify repeating components...")
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
    nav_count = len(global_analysis.shared_nav_items)
    logger.info("Global Analysis completed. Found %d repeating components, %d navigation items.", components_count, nav_count)
    writer({
        "node": "analyzer",
        "status": "running",
        "message": f"Found {components_count} repeating component(s), {nav_count} nav item(s)",
    })

    # --- Level 2: Per-Page Analysis ---
    pages: list[PageAnalysis] = []

    semaphore = asyncio.Semaphore(1)

    async def _analyze_single_page(filename: str) -> PageAnalysis | None:
        logger.info("Queueing Per-Page Analysis for: %s", filename)
        async with semaphore:
            await asyncio.sleep(2)  # Add a 2s delay between requests to respect strict API rate limits
            logger.info("Started processing: %s", filename)
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
                logger.info("Completed analysis for '%s' -> Type: %s, Template: %s", filename, page.page_type, page.wp_template)
                writer({
                    "node": "analyzer",
                    "status": "running",
                    "message": f"  → {filename} → {page.page_type} ({page.wp_template})",
                })
                return page
            except Exception as e:
                logger.error("Page analysis failed for %s: %s", filename, e)
                errors.append(f"Page analysis failed for {filename}: {e}")
                return None

    page_tasks = [_analyze_single_page(fname) for fname in sorted(html_files.keys())]
    page_results = await asyncio.gather(*page_tasks)
    pages = [p for p in page_results if p is not None]

    page_summary = ", ".join(f"{p.source_file}→{p.wp_template}" for p in pages)
    logger.info("Analyzer node completed successfully. Analyzed %d pages.", len(pages))
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
