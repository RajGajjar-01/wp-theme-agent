import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import settings
from app.models import UploadResponse

router = APIRouter()

# Only allow these file extensions
ALLOWED_EXTENSIONS: set[str] = {".html", ".css", ".js"}


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile]) -> UploadResponse:
    """
    Accept uploaded HTML, CSS, and JS files.

    Generates a unique session_id, saves valid files, and returns
    the list of accepted filenames.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    session_id = uuid.uuid4().hex
    session_dir: Path = settings.upload_path / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[str] = []

    for upload_file in files:
        if upload_file.filename is None:
            continue

        # Flatten folder paths — keep only the filename
        filename = Path(upload_file.filename).name
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            continue  # silently skip non-HTML/CSS/JS files

        dest = session_dir / filename
        content = await upload_file.read()

        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        saved_files.append(filename)

    if not saved_files:
        raise HTTPException(
            status_code=400,
            detail="No valid files found. Only .html, .css, and .js files are accepted.",
        )

    return UploadResponse(
        session_id=session_id,
        files=saved_files,
        file_count=len(saved_files),
    )
