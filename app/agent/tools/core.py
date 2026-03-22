import subprocess
from pathlib import Path

from ._paths import resolve


def write_file(path: str, content: str, workspace: Path) -> dict:
    """Write content to a file in the workspace."""
    full = resolve(path, workspace)
    if not full:
        return {"ok": False, "error": f"Path escape blocked: {path}"}
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "size": len(content)}


def read_file(path: str, workspace: Path) -> dict:
    """Read a file from the workspace (uploads/ or output/)."""
    full = resolve(path, workspace)
    if not full:
        return {"ok": False, "error": f"Path escape blocked: {path}"}
    if not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    try:
        content = full.read_text(encoding="utf-8")
        return {"ok": True, "content": content, "size": len(content)}
    except UnicodeDecodeError:
        return {"ok": False, "error": f"Cannot read binary file as text: {path}"}


def list_files(workspace: Path) -> dict:
    """List all files in the workspace with sizes."""
    if not workspace.exists():
        return {"ok": True, "files": []}
    files = []
    for p in sorted(workspace.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(workspace))
            files.append({"path": rel, "size": p.stat().st_size})
    return {"ok": True, "files": files}


def run_php_lint(path: str, workspace: Path) -> dict:
    """Run php -l on a PHP file to check for syntax errors."""
    full = resolve(path, workspace)
    if not full or not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    result = subprocess.run(
        ["php", "-l", str(full)], capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        return {"ok": True, "message": "No syntax errors detected"}
    error = result.stdout.strip() or result.stderr.strip()
    return {"ok": False, "error": error}
