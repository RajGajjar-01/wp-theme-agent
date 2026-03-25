import subprocess
from pathlib import Path

from ._paths import resolve
from .phpcs_checker import checker

MAX_FILE_SIZE = 1024 * 1024


def write_file(path: str, content: str, workspace: Path) -> dict:
    """Write content to a file in the workspace."""
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
    return {"ok": True, "path": path, "size": len(content), "created": not existed}


def read_file(path: str, workspace: Path, offset: int = 0, limit: int = 1000) -> dict:
    """Read a file from the workspace with pagination."""
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
    """List files in workspace with sizes."""
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


def run_php_lint(path: str, workspace: Path, timeout: int = 30) -> dict:
    """Run php -l (syntax check) on a PHP file."""
    full = resolve(path, workspace)
    if not full or not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    if full.suffix.lower() != ".php":
        return {"ok": False, "error": f"Not a PHP file: {path}"}
    result = subprocess.run(
        ["php", "-l", "-d", "display_errors=1", str(full)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        error = result.stdout.strip() or result.stderr.strip()
        return {"ok": False, "syntax_ok": False, "error": f"Syntax error: {error}"}
    return {
        "ok": True,
        "syntax_ok": True,
        "message": "No syntax errors detected",
        "path": path,
    }


def run_phpcs_check(
    path: str, workspace: Path, standard: str = "WordPress-Core"
) -> dict:
    """Run PHPCS (if available) on a PHP file."""
    full = resolve(path, workspace)
    if not full or not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    if full.suffix.lower() != ".php":
        return {"ok": False, "error": f"Not a PHP file: {path}"}
    if not checker.is_available():
        return {
            "ok": True,
            "phpcs_ok": True,
            "phpcs_skipped": True,
            "message": "PHPCS not available",
            "path": path,
        }
    try:
        result = checker.check(full, standard=standard)
    except Exception as e:
        return {"ok": False, "error": f"PHPCS check failed: {str(e)}", "path": path}
    return {
        "ok": result.get("ok", False),
        "phpcs_ok": result.get("error_count", 0) == 0,
        "error_count": result.get("error_count", 0),
        "warning_count": result.get("warning_count", 0),
        "fixable_count": result.get("fixable_count", 0),
        "errors": result.get("errors", [])[:10],
        "warnings": result.get("warnings", [])[:10],
        "path": path,
    }
