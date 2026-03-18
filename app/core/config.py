from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Project root (two levels up from app/core/config.py) ────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    All settings are validated by Pydantic at startup.
    Invalid or missing required values will raise a clear error immediately.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # ── Project metadata ────────────────────────────────────────────────
    PROJECT_NAME: str = "WP Theme Agent"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ── GLM-4.7 via Z.ai (analyzer + planner nodes) ────────────────────
    ZAI_API_KEY: str = ""
    ZAI_BASE_URL: str = "https://api.z.ai/api/paas/v4/"
    GLM_MODEL: str = "glm-4.7"

    # ── MiniMax M2.5 via OpenRouter (generator + validator self-heal) ───
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MINIMAX_MODEL: str = "minimax/minimax-m2.5"

    # ── PHP CLI path on VPS ─────────────────────────────────────────────
    PHP_CLI_PATH: str = "php"

    # ── Theme delivery — Option 1: Direct filesystem path (local dev) ──
    WP_THEME_PATH: str = ""

    # ── Theme delivery — Option 2: Auto-deploy via companion plugin ────
    WP_SITE_URL: str = ""
    WP_SECRET_TOKEN: str = ""

    # ── File storage ────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "output"

    # ── Validator config ────────────────────────────────────────────────
    MAX_VALIDATOR_RETRIES: int = Field(default=3, ge=1, le=10)

    # ── CORS ────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]

    # ── Computed paths (resolved relative to project root) ──────────────
    @computed_field  # type: ignore[prop-decorator]
    @property
    def upload_path(self) -> Path:
        return PROJECT_ROOT / self.UPLOAD_DIR

    @computed_field  # type: ignore[prop-decorator]
    @property
    def output_path(self) -> Path:
        return PROJECT_ROOT / self.OUTPUT_DIR


# ── Singleton settings instance ─────────────────────────────────────────────
settings = Settings()
