import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.agent.graph import agent
from app.core.config import settings
from app.models import ConvertRequest, SessionStatus

router = APIRouter()

logger = logging.getLogger(__name__)

sessions: dict[str, dict] = {}


def _load_uploaded_files(session_id: str) -> dict[str, str]:
    session_dir = settings.upload_path / session_id
    if not session_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found — upload files first.")

    uploaded: dict[str, str] = {}
    for filepath in sorted(session_dir.iterdir()):
        if filepath.is_file() and filepath.suffix in (".html", ".css", ".js"):
            try:
                uploaded[filepath.name] = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.warning("Skipping %s: %s", filepath.name, e)

    if not uploaded:
        raise HTTPException(status_code=400, detail="No valid files found in session upload directory.")

    return uploaded


@router.post("/convert")
async def convert_theme(request: ConvertRequest) -> StreamingResponse:
    uploaded_files = _load_uploaded_files(request.session_id)

    initial_state = {
        "session_id": request.session_id,
        "theme_name": request.theme_name,
        "theme_slug": request.theme_slug,
        "author": request.author,
        "uploaded_files": uploaded_files,
        "global_analysis": None,
        "pages": [],
        "plan": [],
        "generated_files": {},
        "validation_results": {},
        "written_files": [],
        "zip_path": "",
        "pages_xml": "",
        "deploy_status": None,
        "errors": [],
        "messages": [],
    }

    sessions[request.session_id] = {
        "phase": "starting",
        "errors": [],
        "files_generated": 0,
        "files_validated": 0,
        "zip_ready": False,
        "zip_url": None,
    }

    async def event_stream():
        try:
            async for event in agent.astream(
                initial_state,
                stream_mode="custom",
                config={"configurable": {"thread_id": request.session_id}},
            ):
                sessions[request.session_id]["phase"] = event.get("node", "unknown")

                if event.get("status") == "complete" and event.get("node") == "writer":
                    sessions[request.session_id]["zip_ready"] = True
                    sessions[request.session_id]["zip_url"] = f"/api/download/{request.session_id}"

                sse_data = json.dumps(event, default=str)
                yield f"data: {sse_data}\n\n"

            final_event = {
                "node": "pipeline",
                "status": "done",
                "message": "Theme conversion complete",
                "zip_url": f"/api/download/{request.session_id}",
            }
            yield f"data: {json.dumps(final_event)}\n\n"

            sessions[request.session_id]["phase"] = "done"
            sessions[request.session_id]["zip_ready"] = True
            sessions[request.session_id]["zip_url"] = f"/api/download/{request.session_id}"

        except Exception as e:
            logger.error("Pipeline error: %s", e)
            error_event = {
                "node": "pipeline",
                "status": "error",
                "message": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            sessions[request.session_id]["phase"] = "error"
            sessions[request.session_id]["errors"].append(str(e))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/download/{session_id}")
async def download_theme(session_id: str) -> FileResponse:
    output_dir = settings.output_path / session_id
    if not output_dir.is_dir():
        raise HTTPException(status_code=404, detail="Session output not found.")

    zip_files = list(output_dir.glob("*.zip"))
    if not zip_files:
        raise HTTPException(status_code=404, detail="ZIP file not ready yet.")

    zip_path = zip_files[0]
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_path.name,
    )


@router.get("/status/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str) -> SessionStatus:
    session = sessions.get(session_id)
    if not session:
        zip_exists = any((settings.output_path / session_id).glob("*.zip")) if (settings.output_path / session_id).is_dir() else False
        return SessionStatus(
            session_id=session_id,
            phase="done" if zip_exists else "unknown",
            zip_ready=zip_exists,
            zip_url=f"/api/download/{session_id}" if zip_exists else None,
        )

    return SessionStatus(
        session_id=session_id,
        phase=session.get("phase", "unknown"),
        files_generated=session.get("files_generated", 0),
        files_validated=session.get("files_validated", 0),
        errors=session.get("errors", []),
        zip_ready=session.get("zip_ready", False),
        zip_url=session.get("zip_url"),
    )
