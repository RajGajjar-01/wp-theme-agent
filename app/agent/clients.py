from openai import AsyncOpenAI

from app.core.config import settings

glm_client = AsyncOpenAI(
    api_key=settings.ZAI_API_KEY,
    base_url=settings.ZAI_BASE_URL,
)

minimax_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

GLM_MODEL = settings.GLM_MODEL
MINIMAX_MODEL = settings.MINIMAX_MODEL
