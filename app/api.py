import asyncio
import json
import logging
import re
import shutil
import uuid
import sys
from pathlib import Path
from threading import Thread

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.agent.loop import run_agent

router = APIRouter()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("api")


WORKSPACE_ROOT = Path("/home/rajgajjar04/Projects/wp-theme-workspace/sessions")
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

# Text-based extensions the agent can read
TEXT_EXTS = {".html", ".htm", ".css", ".js", ".json", ".txt", ".md", ".svg", ".xml"}

# Image/binary assets — copied verbatim to theme-slug/assets/
ASSET_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".mp4",
    ".webm",
}

# HTML-role keyword mapping for page detection
PAGE_ROLE_HINTS = {
    "about": "about",
    "contact": "contact",
    "service": "services",
    "home": "home",
    "index": "home",
    "portfolio": "portfolio",
    "work": "portfolio",
    "blog": "blog",
    "news": "blog",
    "404": "404",
    "error": "404",
    "search": "search",
    "privacy": "privacy",
    "terms": "terms",
}


# {
#   session_id: str,
#   status: 'pending'|'running'|'completed'|'error'|'stopped',
#   theme_name: str | None,
#   theme_slug: str | None,
#   author: str | None,
#   uploaded_files: { relative_path: text_content },   # text files only
#   asset_files: { relative_path: absolute_path },     # binary assets
#   page_map: { filename: detected_role },             # HTML page analysis
#   file_tree: [ { path, type, size } ],               # full upload tree
#   workspace: Path,
#   zip_path: Path | None,
#   error: str | None,
#   queue: asyncio.Queue | None,
# }
SESSIONS: dict[str, dict] = {}


class ConvertRequest(BaseModel):
    session_id: str
    theme_name: str
    theme_slug: str
    author: str


def _detect_page_role(filename: str) -> str:
    """Guess the WordPress role of an HTML file from its name."""
    stem = Path(filename).stem.lower()
    for kw, role in PAGE_ROLE_HINTS.items():
        if kw in stem:
            return role
    return "page"  # generic custom page


def _ext_category(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in {".html", ".htm"}:
        return "html"
    if ext == ".css":
        return "css"
    if ext == ".js":
        return "js"
    if ext in ASSET_EXTS:
        return (
            "image"
            if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
            else "asset"
        )
    return "other"


def _safe_relative(filename: str) -> str:
    """Strip leading slashes/dots so paths are always relative."""
    # Handles both flat names and folder-prefixed names like 'css/styles.css'
    clean = filename.lstrip("/").lstrip("\\")
    # Remove any ../ components
    parts = [p for p in Path(clean).parts if p not in ("..", ".")]
    return str(Path(*parts)) if parts else clean


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Accept HTML/CSS/JS/image files from a single or multi-page site and return session info."""
    if not files:
        raise HTTPException(400, "No files uploaded")

    session_id = uuid.uuid4().hex
    workspace = WORKSPACE_ROOT / session_id
    workspace.mkdir(parents=True, exist_ok=True)
    uploads_dir = workspace / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"New session: {session_id} — receiving {len(files)} file(s)")

    uploaded_text: dict[str, str] = {}  # relative_path → text content
    asset_paths: dict[str, str] = {}  # relative_path → abs disk path
    file_tree: list[dict] = []

    for file in files:
        if not file.filename:
            continue

        rel_path = _safe_relative(file.filename)
        ext = Path(rel_path).suffix.lower()
        raw = await file.read()

        dest = uploads_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        if ext in ASSET_EXTS:
            # Binary asset — write bytes directly
            dest.write_bytes(raw)
            asset_paths[rel_path] = str(dest)
            cat = _ext_category(rel_path)
            file_tree.append({"path": rel_path, "type": cat, "size": len(raw)})
            logger.info(f"  [asset] {rel_path} ({len(raw)} bytes)")

        else:
            # Text file — decode and store content
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = raw.decode("latin-1", errors="replace")

            dest.write_text(text, encoding="utf-8")
            uploaded_text[rel_path] = text
            cat = _ext_category(rel_path)
            file_tree.append({"path": rel_path, "type": cat, "size": len(raw)})
            logger.info(f"  [text]  {rel_path} ({len(text)} chars)")

    if not uploaded_text and not asset_paths:
        raise HTTPException(400, "No readable files uploaded")

    # Detect HTML pages and their WP roles
    html_files = {
        p: _detect_page_role(p)
        for p in uploaded_text
        if Path(p).suffix.lower() in {".html", ".htm"}
    }
    page_map = html_files

    # Sort file_tree by type then path
    type_order = {"html": 0, "css": 1, "js": 2, "image": 3, "asset": 4, "other": 5}
    file_tree.sort(key=lambda f: (type_order.get(f["type"], 5), f["path"]))

    SESSIONS[session_id] = {
        "session_id": session_id,
        "status": "pending",
        "theme_name": None,
        "theme_slug": None,
        "author": None,
        "uploaded_files": uploaded_text,
        "asset_files": asset_paths,
        "page_map": page_map,
        "file_tree": file_tree,
        "workspace": workspace,
        "zip_path": None,
        "error": None,
        "queue": None,
    }

    return {
        "session_id": session_id,
        "file_count": len(file_tree),
        "text_count": len(uploaded_text),
        "asset_count": len(asset_paths),
        "html_pages": len(html_files),
        "page_map": page_map,
        "file_tree": file_tree,
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "session_id": session_id,
        "status": session["status"],
        "file_tree": session["file_tree"],
        "page_map": session["page_map"],
        "html_pages": len(session["page_map"]),
        "text_count": len(session["uploaded_files"]),
        "asset_count": len(session["asset_files"]),
    }


@router.post("/convert")
async def convert(req: ConvertRequest):
    """Start the agent loop and stream SSE events back."""

    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if session["status"] == "running":
        raise HTTPException(400, "Session already running")

    # Validate slug
    if not re.match(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$", req.theme_slug):
        raise HTTPException(
            400, "Theme slug must be lowercase letters, numbers, and hyphens only"
        )

    session["theme_name"] = req.theme_name
    session["theme_slug"] = req.theme_slug
    session["author"] = req.author
    session["status"] = "running"

    logger.info(f"Starting conversion: {req.session_id} → {req.theme_slug}")

    queue = asyncio.Queue()
    session["queue"] = queue
    loop = asyncio.get_event_loop()

    def emit(node: str, status: str, message: str = "", extra: dict = None):
        if message:
            logger.info(f"[{node}] {status}: {message}")
        event = {"node": node, "status": status, "message": message}
        if extra:
            event.update(extra)
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    def run_in_thread():
        workspace = session["workspace"]
        try:
            # Copy binary assets into theme-slug/assets/ before agent starts
            _seed_assets(session["asset_files"], workspace, emit, req.theme_slug)

            run_agent(
                uploaded_files=session["uploaded_files"],
                theme_name=req.theme_name,
                theme_slug=req.theme_slug,
                author=req.author,
                workspace=workspace,
                emit=emit,
            )

            zip_path = _create_zip(workspace, req.theme_slug)
            session["zip_path"] = zip_path
            session["status"] = "completed"
            logger.info(f"Completed: {req.session_id}")

            emit(
                "pipeline",
                "done",
                "Theme ready!",
                {"zip_url": f"/api/download/{req.session_id}"},
            )

        except Exception as e:
            logger.error(f"Error in {req.session_id}: {e}", exc_info=True)
            session["status"] = "error"
            session["error"] = str(e)
            emit("pipeline", "error", str(e))

        finally:
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)

    Thread(target=run_in_thread, daemon=True).start()

    return StreamingResponse(
        _sse_generator(queue, req.session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _seed_assets(
    asset_files: dict[str, str], workspace: Path, emit, theme_slug: str
) -> None:
    """Copy uploaded binary assets (images, fonts) into theme-slug/assets/."""
    if not asset_files:
        return
    assets_out = workspace / theme_slug / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    for rel_path, abs_src in asset_files.items():
        # Preserve subfolder structure inside assets/
        subpath = Path(rel_path)
        # Remove leading directory if it looks like 'images/logo.png' → keep as-is
        dest = assets_out / subpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(abs_src, str(dest))
        emit("agent", "complete", f"Copied asset: {theme_slug}/assets/{rel_path}")
    emit(
        "agent",
        "complete",
        f"Assets seeded: {len(asset_files)} file(s) → {theme_slug}/assets/",
    )


async def _sse_generator(queue: asyncio.Queue, session_id: str):
    """Pull events from queue and format as SSE."""
    try:
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=45.0)
            if event is None:
                break
            session = SESSIONS.get(session_id)
            if session and session["status"] == "stopped":
                yield _sse(
                    {
                        "node": "pipeline",
                        "status": "stopped",
                        "message": "Session stopped",
                    }
                )
                break
            yield _sse(event)
    except asyncio.TimeoutError:
        yield _sse({"node": "heartbeat", "status": "heartbeat", "message": "..."})
    except Exception:
        pass


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/stop/{session_id}")
async def stop_session(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    session["status"] = "stopped"
    logger.info(f"Stopping: {session_id}")
    return {"ok": True}


@router.get("/download/{session_id}")
async def download(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session["zip_path"] or not session["zip_path"].exists():
        raise HTTPException(404, "ZIP not ready")
    logger.info(f"Download: {session_id}")
    return FileResponse(
        path=session["zip_path"],
        filename=session["zip_path"].name,
        media_type="application/zip",
    )


@router.get("/sessions")
async def list_sessions():
    return {
        "sessions": [
            {
                "session_id": s["session_id"],
                "status": s["status"],
                "theme_name": s["theme_name"],
                "html_pages": len(s.get("page_map", {})),
                "error": s["error"],
            }
            for s in SESSIONS.values()
        ]
    }


def _create_zip(workspace: Path, theme_slug: str) -> Path:
    """Create a WordPress-ready ZIP with theme-slug as root folder."""
    theme_output = workspace / theme_slug
    zip_path = workspace / f"{theme_slug}.zip"
    shutil.make_archive(
        str(zip_path.with_suffix("")),
        "zip",
        workspace,
        theme_slug,
    )
    return zip_path
