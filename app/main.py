import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

# ── Paths ───────────────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # ── CORS ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API routes ──────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api")

    # ── Frontend serving ────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def serve_frontend() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    # Mount frontend static assets (CSS, JS, images) if the dir exists
    if FRONTEND_DIR.is_dir():
        app.mount(
            "/static",
            StaticFiles(directory=str(FRONTEND_DIR)),
            name="frontend-static",
        )

    # ── Startup / Shutdown ──────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        """Ensure upload and output directories exist."""
        settings.upload_path.mkdir(parents=True, exist_ok=True)
        settings.output_path.mkdir(parents=True, exist_ok=True)

    return app


# ── App instance (used by uvicorn) ──────────────────────────────────────────
app = create_app()
