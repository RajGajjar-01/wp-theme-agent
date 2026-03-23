import subprocess
from pathlib import Path

from ._paths import resolve
from .phpcs_checker import checker

MAX_FILE_SIZE = 1024 * 1024  # 1MB limit


def write_file(path: str, content: str, workspace: Path) -> dict:
    """Write content to a file in the workspace.

    Creates parent directories if needed, returns file size on success."""
    if len(content) > MAX_FILE_SIZE:
        return {
            "ok": False,
            "error": f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE})",
        }

    full = resolve(path, workspace)
    if not full:
        return {"ok": False, "error": f"Path escape blocked: {path}"}

    existed = full.exists()
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "path": path,
        "size": len(content),
        "created": not existed,
    }


def read_file(path: str, workspace: Path, offset: int = 0, limit: int = 1000) -> dict:
    """Read a file from the workspace with pagination.

    Returns content, size, and line range information."""
    full = resolve(path, workspace)
    if not full:
        return {"ok": False, "error": f"Path escape blocked: {path}"}
    if not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    try:
        content = full.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = None
        for enc in ["latin-1", "cp1252"]:
            try:
                content = full.read_text(encoding=enc)
                break
            except Exception:
                continue

        if content is None:
            return {"ok": False, "error": f"Cannot read binary file as text: {path}"}

    lines = content.splitlines()
    total_lines = len(lines)
    paginated = lines[offset : offset + limit]

    return {
        "ok": True,
        "content": "\n".join(paginated),
        "size": len(content),
        "total_lines": total_lines,
        "showing": f"{offset + 1}-{min(offset + limit, total_lines)}",
    }


def list_files(workspace: Path, glob: str = "*", max_results: int = 100) -> dict:
    """List files in workspace with sizes.

    Supports filtering with glob pattern, sorted by modification time."""
    if not workspace.exists():
        return {"ok": True, "files": [], "total": 0}

    files = []
    for p in sorted(
        workspace.rglob(glob), key=lambda x: x.stat().st_mtime, reverse=True
    ):
        if not p.is_file():
            continue
        files.append(
            {
                "path": str(p.relative_to(workspace)),
                "size": p.stat().st_size,
                "modified": p.stat().st_mtime,
            }
        )
        if len(files) >= max_results:
            break

    return {
        "ok": True,
        "files": files,
        "total": len(files),
        "truncated": len(files) >= max_results,
    }


def run_php_lint(
    path: str, workspace: Path, timeout: int = 30, auto_fix: bool = True
) -> dict:
    """Run php -l and PHPCS (if available) on a PHP file."""
    full = resolve(path, workspace)
    if not full or not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    if full.suffix.lower() != ".php":
        return {"ok": False, "error": f"Not a PHP file: {path}"}

    # Step 1: Syntax check (php -l)
    result = subprocess.run(
        ["php", "-l", "-d", "display_errors=1", str(full)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        error = result.stdout.strip() or result.stderr.strip()
        return {"ok": False, "syntax_ok": False, "error": f"Syntax error: {error}"}

    # Step 2: PHPCS check (if available)
    if not checker.is_available():
        return {
            "ok": True,
            "syntax_ok": True,
            "phpcs_ok": True,
            "phpcs_skipped": True,
            "message": "No syntax errors detected (PHPCS not available)",
            "path": path,
        }

    # Run PHPCS with auto-fix
    phpcs_result = checker.check_and_fix(
        full, standard="WordPress-Core", auto_fix=auto_fix
    )

    if phpcs_result.get("skipped"):
        return {
            "ok": True,
            "syntax_ok": True,
            "phpcs_ok": True,
            "message": "No syntax errors detected",
            "path": path,
        }

    return {
        "ok": phpcs_result.get("ok", False),
        "syntax_ok": True,
        "phpcs_ok": phpcs_result.get("remaining_errors", 0) == 0,
        "fixed": phpcs_result.get("fixed", 0),
        "remaining_errors": phpcs_result.get("remaining_errors", 0),
        "remaining_warnings": phpcs_result.get("remaining_warnings", 0),
        "issues": phpcs_result.get("issues", [])[:10],  # Limit for tokens
        "path": path,
    }
