import logging
import shutil
import json
import subprocess
from typing import Annotated

from langchain_core.tools import tool

from ._paths import WORKSPACE_ROOT, resolve_workspace

logger = logging.getLogger("wp-agent")


def _find_phpcs() -> str | None:
    for cmd in ["phpcs", "vendor/bin/phpcs"]:
        path = shutil.which(cmd)
        if path:
            return path
    return None


PHPCS_PATH = _find_phpcs()


@tool
def run_php_lint(
    path: Annotated[str, "Path to PHP file (e.g. 'rapidflow-plumbing/header.php')"],
) -> dict:
    """Check PHP file for syntax errors (php -l). Call after writing any PHP file."""
    logger.info(f"[TOOL] run_php_lint('{path}') called")

    workspace = WORKSPACE_ROOT
    full = resolve_workspace(path, workspace)

    if not full:
        logger.error(f"[TOOL] Invalid path: {path}")
        return {"ok": False, "error": f"Invalid path: {path}"}
    if not full.exists():
        logger.error(f"[TOOL] File not found: {path}")
        return {"ok": False, "error": f"File not found: {path}"}
    if full.suffix.lower() != ".php":
        logger.error(f"[TOOL] Not a PHP file: {path}")
        return {"ok": False, "error": f"Not a PHP file: {path}"}

    try:
        result = subprocess.run(
            ["php", "-l", "-d", "display_errors=1", str(full)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        logger.error("[TOOL] PHP not installed")
        return {"ok": False, "error": "PHP not installed"}
    except subprocess.TimeoutExpired:
        logger.error("[TOOL] PHP lint timeout")
        return {"ok": False, "error": "PHP lint timeout"}

    if result.returncode != 0:
        error = result.stdout.strip() or result.stderr.strip()
        logger.error(f"[TOOL] PHP syntax error in {path}: {error[:100]}")
        return {"ok": False, "syntax_ok": False, "error": error}

    logger.info(f"[TOOL] PHP lint passed: {path}")
    return {"ok": True, "syntax_ok": True, "message": "No syntax errors"}
