from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api import router

app = FastAPI(title="WP Theme Agent")

# API routes under /api
app.include_router(router, prefix="/api")

# Serve the UI HTML file at root
UI_FILE = Path("ui/index.html")


@app.get("/")
async def serve_ui():
    return FileResponse(UI_FILE)
