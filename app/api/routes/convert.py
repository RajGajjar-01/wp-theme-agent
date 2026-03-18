from fastapi import APIRouter

from app.models import ConvertRequest, SessionStatus

router = APIRouter()


@router.post("/convert")
async def convert_theme(request: ConvertRequest):  # noqa: ARG001
    """
    Trigger the LangGraph agent to convert uploaded files into a WP theme.

    Streams SSE events in real time. Full implementation in Step 5–6.
    """
    # TODO: Implement in Step 5 (graph wiring) + Step 6 (SSE streaming)
    return {"message": "Convert endpoint stub — will stream SSE events after graph wiring."}


@router.get("/download/{session_id}")
async def download_theme(session_id: str):  # noqa: ARG001
    """
    Download the generated theme ZIP.

    Full implementation in Step 6.
    """
    # TODO: Implement in Step 6
    return {"message": "Download endpoint stub — will serve ZIP after writer node is wired."}


@router.get("/status/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str) -> SessionStatus:
    """
    Polling fallback — returns current session state.

    Full implementation in Step 6.
    """
    # TODO: Implement in Step 6
    return SessionStatus(session_id=session_id, phase="pending")
