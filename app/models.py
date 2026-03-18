from pydantic import BaseModel, Field


# ── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response after files are uploaded."""
    session_id: str
    files: list[str]
    file_count: int


# ── Convert ─────────────────────────────────────────────────────────────────

class ConvertRequest(BaseModel):
    """Request body for the /convert endpoint."""
    session_id: str
    theme_name: str = Field(..., min_length=1, max_length=200)
    theme_slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    author: str = Field(..., min_length=1, max_length=200)


# ── Health ──────────────────────────────────────────────────────────────────

class ModelsInfo(BaseModel):
    """LLM model identifiers."""
    analyzer: str
    planner: str
    generator: str
    validator_healer: str


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""
    status: str = "ok"
    version: str
    php_cli: bool
    models: ModelsInfo


# ── Status ──────────────────────────────────────────────────────────────────

class SessionStatus(BaseModel):
    """Polling fallback: current state of a session."""
    session_id: str
    phase: str = "unknown"
    files_generated: int = 0
    files_validated: int = 0
    errors: list[str] = Field(default_factory=list)
    zip_ready: bool = False
    zip_url: str | None = None


# ── SSE Events ──────────────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    """Server-Sent Event payload streamed during /convert."""
    node: str
    status: str  # running | complete | passed | warning | error | heartbeat
    message: str
    data: dict | None = None
