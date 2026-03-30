import logging
import shutil
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from ._paths import (
    BASE_THEME_ROOT,
    WORKSPACE_ROOT,
    resolve_base_theme,
    resolve_workspace,
)

logger = logging.getLogger("wp-agent")

_seeded_themes = set()


@tool
def list_base_theme_files() -> dict:
    """List all files in the _s base theme. Use to see available files to copy or reference."""
    logger.info("[TOOL] list_base_theme_files() called")

    if not BASE_THEME_ROOT.exists():
        logger.error("[TOOL] Base theme not found")
        return {"ok": False, "error": "Base theme not found", "files": []}

    files = []
    for p in sorted(BASE_THEME_ROOT.rglob("*")):
        if p.is_file():
            files.append(
                {
                    "path": str(p.relative_to(BASE_THEME_ROOT)),
                    "size": p.stat().st_size,
                }
            )

    logger.info(f"[TOOL] Found {len(files)} base theme files")
    return {"ok": True, "files": files, "total": len(files)}


@tool
def read_base_theme_file(
    path: Annotated[
        str, "Path within base theme (e.g. 'header.php', 'inc/template-tags.php')"
    ],
) -> dict:
    """Read a file from the _s base theme. Use to understand base structure before modifying."""
    logger.info(f"[TOOL] read_base_theme_file('{path}') called")

    full = resolve_base_theme(path)
    if not full or not full.exists():
        logger.error(f"[TOOL] Base theme file not found: {path}")
        return {"ok": False, "error": f"Base theme file not found: {path}"}
    try:
        content = full.read_text(encoding="utf-8")
        logger.info(f"[TOOL] Read {path} ({len(content)} chars)")
        return {"ok": True, "content": content, "size": len(content)}
    except UnicodeDecodeError:
        logger.error(f"[TOOL] Cannot read binary file: {path}")
        return {"ok": False, "error": f"Cannot read binary file: {path}"}


@tool
def seed_base_theme(
    theme_slug: Annotated[str, "Theme folder name (e.g. 'my-theme')"],
) -> dict:
    """Copy _s base theme to workspace with slug replacements. Call ONCE at the start."""
    logger.info(f"[TOOL] seed_base_theme('{theme_slug}') called")

    workspace = WORKSPACE_ROOT

    if not BASE_THEME_ROOT.exists():
        logger.error("[TOOL] Base theme not found")
        return {"ok": False, "error": "Base theme not found"}

    dest = workspace / theme_slug

    # Check if already seeded
    if theme_slug in _seeded_themes:
        logger.info(f"[TOOL] Theme already seeded: {theme_slug}")
        return {
            "ok": True,
            "theme_slug": theme_slug,
            "path": str(dest.relative_to(workspace)),
            "already_seeded": True,
            "message": f"Theme {theme_slug} was already seeded. Continue with other tasks.",
        }

    if dest.exists():
        logger.info(f"[TOOL] Removing existing theme folder: {dest}")
        shutil.rmtree(dest)

    logger.info(f"[TOOL] Copying base theme to {dest}")
    shutil.copytree(BASE_THEME_ROOT, dest)

    # Generate prefixes - CRITICAL: underscores for PHP function names
    text_domain = theme_slug  # e.g., "rapidflow-plumbing" (hyphens OK for text domain)
    func_prefix = theme_slug.replace(
        "-", "_"
    )  # e.g., "rapidflow_plumbing" (undersrops for functions)
    class_prefix = func_prefix.title().replace("_", "")  # e.g., "RapidflowPlumbing"
    const_prefix = func_prefix.upper()  # e.g., "RAPIDFLOW_PLUMBING"

    # ORDER MATTERS! Do more specific replacements first
    # CRITICAL: Never use a catch-all that replaces bare "_s" - it corrupts WordPress core functions
    # like after_setup_theme, wp_enqueue_scripts, etc.
    replacements = [
        # Function names (must have underscores, not hyphens)
        ("_s_", f"{func_prefix}_"),  # _s_setup -> rapidflow_plumbing_setup
        (
            "function _s(",
            f"function {func_prefix}(",
        ),  # function _s( -> function rapidflow_plumbing(
        # Constants (uppercase with underscores)
        (
            "_S_VERSION",
            f"{const_prefix}_VERSION",
        ),  # _S_VERSION -> RAPIDFLOW_PLUMBING_VERSION
        ("_S_", f"{const_prefix}_"),  # Other constants
        # Class names (PascalCase)
        ("_S", class_prefix),  # _S for class names -> RapidflowPlumbing
        # Package names and comments (can have hyphens)
        ("@package _s", f"@package {text_domain}"),
        ("@package _S", f"@package {text_domain}"),
        # Text domain in quotes (can have hyphens)
        ("'_s'", f"'{text_domain}'"),  # load_theme_textdomain('_s')
        ('"_s"', f'"{text_domain}"'),
        # CSS prefixes and handle names
        ("_s-", f"{text_domain}-"),  # CSS prefixes like _s-style
        ("'_s-", f"'{text_domain}-"),  # Script handles
        ('"_s-', f'"{text_domain}-'),  # Script handles
        # Variable names (use underscores)
        ("$_s_", f"${func_prefix}_"),  # $_s_description -> $rapidflow_plumbing_description
        # DO NOT add a bare "_s" catch-all - it breaks WordPress core functions!
    ]

    logger.info(f"[TOOL] Text domain: {text_domain}")
    logger.info(f"[TOOL] Function prefix: {func_prefix}")
    logger.info(f"[TOOL] Class prefix: {class_prefix}")

    files_modified = 0
    errors = []

    for p in dest.rglob("*"):
        if not p.is_file() or p.suffix in [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".ico",
            ".svg",
        ]:
            continue
        try:
            content = p.read_text(encoding="utf-8")
            original = content
            for old, new in replacements:
                content = content.replace(old, new)
            if content != original:
                p.write_text(content, encoding="utf-8")
                files_modified += 1
        except Exception as e:
            errors.append(f"{p.name}: {e}")
            continue

    # Remove readme
    readme = dest / "readme.txt"
    if readme.exists():
        readme.unlink()

    _seeded_themes.add(theme_slug)

    logger.info(f"[TOOL] Base theme seeded: {files_modified} files modified")

    # Run PHP lint on all files to verify
    import subprocess

    php_errors = []
    for php_file in dest.rglob("*.php"):
        try:
            result = subprocess.run(
                ["php", "-l", str(php_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                php_errors.append(f"{php_file.name}: {result.stdout.strip()[:100]}")
        except:
            pass

    if php_errors:
        logger.error(f"[TOOL] PHP syntax errors after seeding: {php_errors}")
        return {
            "ok": False,
            "theme_slug": theme_slug,
            "path": str(dest.relative_to(workspace)),
            "files_modified": files_modified,
            "php_errors": php_errors,
            "message": f"Theme seeded but has PHP errors. Check replacement logic.",
        }

    logger.info("[TOOL] All PHP files passed syntax check")
    logger.info(
        "[TOOL] DO NOT call seed_base_theme again. Continue with modifying files."
    )

    return {
        "ok": True,
        "theme_slug": theme_slug,
        "path": str(dest.relative_to(workspace)),
        "files_modified": files_modified,
        "text_domain": text_domain,
        "func_prefix": func_prefix,
        "message": f"Base theme seeded to {theme_slug}/. Use function prefix '{func_prefix}_' in PHP. DO NOT call this tool again.",
    }
