import shutil

from fastapi import APIRouter

from app.core.config import settings
from app.models import HealthResponse, ModelsInfo

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return server health including php-cli availability and model info."""
    php_available = shutil.which(settings.PHP_CLI_PATH) is not None

    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        php_cli=php_available,
        models=ModelsInfo(
            analyzer=settings.GLM_MODEL,
            planner=settings.GLM_MODEL,
            generator=settings.MINIMAX_MODEL,
            validator_healer=settings.MINIMAX_MODEL,
        ),
    )
