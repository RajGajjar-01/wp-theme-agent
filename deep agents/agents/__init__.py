import os
import logging
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("wp-agent")


class RateLimitCallback(BaseCallbackHandler):
    """Callback to add delay between LLM calls to avoid rate limiting."""

    def __init__(self, delay_seconds: float = 3.0):
        self.delay_seconds = delay_seconds
        self._last_call_time = 0.0

    def on_llm_end(self, response, **kwargs):
        """Add delay after each LLM call."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            logger.info(f"Rate limiting: sleeping for {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self._last_call_time = time.time()

from deepagents import create_deep_agent

from tools import WP_TOOLS
from prompts import build_system_prompt
from .sub_agents import (
    create_analyzer_agent,
    create_generator_agent,
    create_acf_agent,
    create_validator_agent,
)

ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = ROOT / "workspaces"


def create_wp_agent(
    theme_name: str = "My Theme",
    theme_slug: str = "my-theme",
    author: str = "Developer",
    uploaded_files: dict[str, str] | None = None,
    model_name: str = "accounts/fireworks/models/glm-5",
    use_sub_agents: bool = False,
) -> Any:
    """Create a WordPress theme generation agent."""
    uploaded_files = uploaded_files or {}

    logger.info(f"Creating agent for theme: {theme_name} ({theme_slug})")
    logger.info(f"Model: {model_name}")
    logger.info(f"Tools available: {[t.name for t in WP_TOOLS]}")

    system_prompt = build_system_prompt(
        uploaded_files=uploaded_files,
        theme_name=theme_name,
        theme_slug=theme_slug,
        author=author,
    )
    logger.info(f"System prompt length: {len(system_prompt)} chars")

    model = ChatOpenAI(
        model=model_name,
        api_key=os.getenv("FIREWORKS_API_KEY"),
        base_url="https://api.fireworks.ai/inference/v1",
        temperature=0.7,
        callbacks=[RateLimitCallback(delay_seconds=3.0)],
    )

    agent = create_deep_agent(
        model=model,
        tools=WP_TOOLS,
        system_prompt=system_prompt,
    )

    logger.info("Agent created successfully")

    return agent


def generate_theme(
    theme_name: str,
    theme_slug: str,
    author: str,
    uploaded_files: dict[str, str],
    use_sub_agents: bool = False,
) -> dict:
    """Generate a WordPress theme from uploaded files."""
    logger.info("=" * 60)
    logger.info("STARTING THEME GENERATION")
    logger.info("=" * 60)
    logger.info(f"Theme: {theme_name}")
    logger.info(f"Slug: {theme_slug}")
    logger.info(f"Author: {author}")
    logger.info(f"Files: {len(uploaded_files)}")

    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    logger.info(f"Workspace: {WORKSPACE_ROOT}")

    logger.info("Writing uploaded files to workspace...")
    for filename, content in uploaded_files.items():
        uploads_dir = WORKSPACE_ROOT / "uploads"
        file_path = uploads_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"  Written: {filename} ({len(content)} chars)")

    logger.info("Creating agent...")
    agent = create_wp_agent(
        theme_name=theme_name,
        theme_slug=theme_slug,
        author=author,
        uploaded_files=uploaded_files,
        use_sub_agents=use_sub_agents,
    )

    file_listing = ", ".join(
        f"{name} ({len(content)} chars)" for name, content in uploaded_files.items()
    )

    if use_sub_agents:
        task_prompt = f"""Generate WordPress theme '{theme_name}' (slug: {theme_slug}) using sub-agents:

1. Use write_todos to plan: analyze, generate, acf, validate
2. Spawn ANALYZER sub-agent to extract structure from: {file_listing}
3. Spawn GENERATOR sub-agent to create PHP templates
4. Spawn ACF sub-agent to create editable fields
5. Spawn VALIDATOR sub-agent to check the theme
6. Fix any issues and finalize
Author: {author}"""
        logger.info("Using multi-agent mode (sub-agents enabled)")
    else:
        task_prompt = f"""Generate WordPress theme '{theme_name}' (slug: {theme_slug}) from these files: {file_listing}. 
Author: {author}. 

Workflow:
1. Call seed_base_theme('{theme_slug}') to initialize
2. Analyze uploaded files
3. Modify header.php and footer.php
4. Create front-page.php template
5. Add CSS to style.css
6. Generate ACF fields for all content
7. Run PHP lint on all files
8. Validate theme structure"""
        logger.info("Using single-agent mode")

    logger.info("-" * 60)
    logger.info("INVOKING AGENT...")
    logger.info("-" * 60)

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": task_prompt,
                }
            ]
        }
    )

    logger.info("-" * 60)
    logger.info("AGENT COMPLETED")
    logger.info("-" * 60)

    # Log the final messages
    if "messages" in result:
        for i, msg in enumerate(result["messages"]):
            msg_type = type(msg).__name__
            content_preview = (
                str(msg.content)[:200] if hasattr(msg, "content") else str(msg)[:200]
            )
            logger.info(f"Message {i}: {msg_type} - {content_preview}...")

    return {
        "ok": True,
        "theme_slug": theme_slug,
        "theme_path": str(WORKSPACE_ROOT / theme_slug),
        "result": result,
    }


__all__ = [
    "create_wp_agent",
    "generate_theme",
    "create_analyzer_agent",
    "create_generator_agent",
    "create_acf_agent",
    "create_validator_agent",
    "logger",
]
