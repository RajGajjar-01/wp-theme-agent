import json
import logging
import zipfile
from pathlib import Path

from langgraph.config import get_stream_writer

from app.agent.models import DeployStatus, PageAnalysis
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


def _generate_pages_xml(pages: list[PageAnalysis], theme_name: str) -> str:
    static_pages = [p for p in pages if p.page_type == "static_page" and p.wp_page_slug]
    if not static_pages:
        return ""

    items = []
    for page in static_pages:
        items.append(f"""    <item>
      <title>{page.title}</title>
      <wp:post_type>page</wp:post_type>
      <wp:post_name>{page.wp_page_slug}</wp:post_name>
      <wp:status>publish</wp:status>
      <content:encoded><![CDATA[<!-- content managed by {page.wp_template} template -->]]></content:encoded>
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
    xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:wp="http://wordpress.org/export/1.2/">
  <channel>
    <title>{theme_name}</title>
    <wp:wxr_version>1.2</wp:wxr_version>
{chr(10).join(items)}
  </channel>
</rss>"""


async def writer_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    generated_files: dict[str, str] = dict(state.get("generated_files", {}))
    pages: list[PageAnalysis] = state.get("pages", [])
    errors: list[str] = list(state.get("errors", []))

    session_id = state["session_id"]
    theme_slug = state["theme_slug"]
    theme_name = state["theme_name"]

    output_dir: Path = settings.output_path / session_id / theme_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    writer({"node": "writer", "status": "running", "message": f"Writing {len(generated_files)} files to output/..."})

    # Generate pages.xml if not already in generated_files
    if "pages.xml" not in generated_files:
        pages_xml_content = _generate_pages_xml(pages, theme_name)
        if pages_xml_content:
            generated_files["pages.xml"] = pages_xml_content

    written_files: list[str] = []

    for filepath, content in sorted(generated_files.items()):
        full_path = output_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            full_path.write_text(content, encoding="utf-8")
            written_files.append(filepath)
        except Exception as e:
            logger.error("Failed to write %s: %s", filepath, e)
            errors.append(f"Failed to write {filepath}: {e}")

    writer({"node": "writer", "status": "running", "message": f"Written {len(written_files)} files, creating ZIP..."})

    # Create ZIP
    zip_dir = settings.output_path / session_id
    zip_path = zip_dir / f"{theme_slug}.zip"

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath in written_files:
                full_path = output_dir / filepath
                arcname = f"{theme_slug}/{filepath}"
                zf.write(full_path, arcname)

        writer({"node": "writer", "status": "running", "message": f"ZIP created: {zip_path.name}"})
    except Exception as e:
        logger.error("ZIP creation failed: %s", e)
        errors.append(f"ZIP creation failed: {e}")
        zip_path = Path("")

    # Store pages.xml content for state
    pages_xml = generated_files.get("pages.xml", "")

    writer({
        "node": "writer",
        "status": "complete",
        "message": f"{len(written_files)} files written, ZIP ready for download",
        "files_written": written_files,
        "zip_path": str(zip_path),
    })

    return {
        "written_files": written_files,
        "zip_path": str(zip_path),
        "pages_xml": pages_xml,
        "deploy_status": DeployStatus(method="zip", success=True, message="Theme packaged as ZIP"),
        "errors": errors,
    }
