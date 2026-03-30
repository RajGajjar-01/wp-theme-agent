import logging
import subprocess
import re
from typing import Annotated

from langchain_core.tools import tool

from ._paths import WORKSPACE_ROOT, resolve_workspace

logger = logging.getLogger("wp-agent")

_task_completed = False


@tool
def validate_theme(
    theme_slug: Annotated[str, "Theme folder name to validate"],
) -> dict:
    """Run comprehensive validation on generated theme. Checks required files, PHP syntax, WP hooks, and structure."""
    logger.info(f"[TOOL] validate_theme('{theme_slug}') called")

    workspace = WORKSPACE_ROOT
    theme_dir = resolve_workspace(theme_slug, workspace)

    if not theme_dir or not theme_dir.exists():
        logger.error(f"[TOOL] Theme not found: {theme_slug}")
        return {"ok": False, "error": f"Theme not found: {theme_slug}"}

    results = {
        "ok": True,
        "theme_slug": theme_slug,
        "errors": [],
        "warnings": [],
        "checks_passed": 0,
        "checks_total": 0,
    }

    # Check required files
    logger.info("[TOOL] Checking required files...")
    required = ["style.css", "functions.php", "header.php", "footer.php", "index.php"]
    for f in required:
        results["checks_total"] += 1
        if not (theme_dir / f).exists():
            results["errors"].append(f"Missing required file: {f}")
            results["ok"] = False
            logger.error(f"[TOOL] Missing: {f}")
        else:
            results["checks_passed"] += 1
            logger.info(f"[TOOL] Found: {f}")

    # Check PHP syntax
    logger.info("[TOOL] Checking PHP syntax...")
    php_files = list(theme_dir.rglob("*.php"))
    for php_file in php_files:
        results["checks_total"] += 1
        try:
            res = subprocess.run(
                ["php", "-l", str(php_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode != 0:
                error_msg = res.stdout.strip() or res.stderr.strip()
                results["errors"].append(
                    f"Syntax error in {php_file.name}: {error_msg[:100]}"
                )
                results["ok"] = False
                logger.error(f"[TOOL] PHP error in {php_file.name}")
            else:
                results["checks_passed"] += 1
        except FileNotFoundError:
            results["warnings"].append("PHP not installed, skipping syntax check")
            logger.warning("[TOOL] PHP not installed")
        except Exception as e:
            results["warnings"].append(f"Could not check {php_file.name}: {e}")
            logger.warning(f"[TOOL] Could not check {php_file.name}")

    # Check header.php
    logger.info("[TOOL] Checking header.php...")
    header = theme_dir / "header.php"
    if header.exists():
        content = header.read_text(encoding="utf-8")
        results["checks_total"] += 2
        if "wp_head()" not in content:
            results["errors"].append("header.php: Missing wp_head()")
            results["ok"] = False
            logger.error("[TOOL] header.php missing wp_head()")
        else:
            results["checks_passed"] += 1
            logger.info("[TOOL] header.php has wp_head()")
        if "body_class()" not in content:
            results["errors"].append("header.php: Missing body_class()")
            results["ok"] = False
            logger.error("[TOOL] header.php missing body_class()")
        else:
            results["checks_passed"] += 1
            logger.info("[TOOL] header.php has body_class()")

    # Check footer.php
    logger.info("[TOOL] Checking footer.php...")
    footer = theme_dir / "footer.php"
    if footer.exists():
        content = footer.read_text(encoding="utf-8")
        results["checks_total"] += 1
        if "wp_footer()" not in content:
            results["errors"].append("footer.php: Missing wp_footer()")
            results["ok"] = False
            logger.error("[TOOL] footer.php missing wp_footer()")
        else:
            results["checks_passed"] += 1
            logger.info("[TOOL] footer.php has wp_footer()")

    # Check functions.php
    logger.info("[TOOL] Checking functions.php...")
    functions = theme_dir / "functions.php"
    if functions.exists():
        content = functions.read_text(encoding="utf-8")
        results["checks_total"] += 1
        if "wp_enqueue_scripts" not in content:
            results["warnings"].append("functions.php: No wp_enqueue_scripts action")
            logger.warning("[TOOL] functions.php missing wp_enqueue_scripts")
        else:
            results["checks_passed"] += 1
            logger.info("[TOOL] functions.php has wp_enqueue_scripts")

    # Check for hardcoded content
    logger.info("[TOOL] Checking for hardcoded content...")
    for tmpl in theme_dir.glob("*.php"):
        if tmpl.name in ["header.php", "footer.php", "functions.php", "index.php"]:
            continue
        content = tmpl.read_text(encoding="utf-8")
        if "get_field" not in content and "get_sub_field" not in content:
            hardcoded = re.findall(r">(?![<\?\s])([^<\{\}]+)<", content)
            for text in hardcoded:
                text = text.strip()
                if len(text) > 30:
                    results["warnings"].append(
                        f"{tmpl.name}: Hardcoded content detected"
                    )
                    logger.warning(f"[TOOL] {tmpl.name}: Hardcoded content detected")
                    break

    # Summary
    logger.info("=" * 50)
    logger.info(f"[TOOL] Validation complete for {theme_slug}")
    logger.info(
        f"[TOOL] Checks: {results['checks_passed']}/{results['checks_total']} passed"
    )
    logger.info(f"[TOOL] Errors: {len(results['errors'])}")
    logger.info(f"[TOOL] Warnings: {len(results['warnings'])}")
    logger.info("=" * 50)

    return results


@tool
def task_complete(
    summary: Annotated[str, "Summary of all files created and what was done"],
) -> dict:
    """Call when theme generation is COMPLETE. Stops the agent loop."""
    global _task_completed
    _task_completed = True

    logger.info("=" * 60)
    logger.info("[TOOL] TASK COMPLETE")
    logger.info("=" * 60)
    logger.info(f"[TOOL] Summary: {summary[:500]}...")
    logger.info("[TOOL] Agent should now stop.")

    return {
        "ok": True,
        "complete": True,
        "summary": summary,
        "message": "Theme generation complete. Agent will now stop.",
    }
