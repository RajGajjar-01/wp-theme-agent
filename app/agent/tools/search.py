import re
from pathlib import Path

from ._paths import resolve_src

MAX_FILE_SIZE = 1024 * 512
MAX_MATCHES_PER_FILE = 50
MAX_FILES_TO_SEARCH = 50


def search_in_file(path: str, pattern: str, workspace: Path, context: int = 0) -> dict:
    """Search for a regex pattern in a single file and return matching lines."""
    full = resolve_src(path, workspace)
    if not full:
        return {"ok": False, "error": f"Path blocked: {path}"}
    if not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    if full.stat().st_size > MAX_FILE_SIZE:
        return {
            "ok": False,
            "error": f"File too large: {full.stat().st_size} bytes (max {MAX_FILE_SIZE})",
        }
    try:
        content = full.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"ok": False, "error": f"Cannot read binary file: {path}"}
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return {"ok": False, "error": f"Invalid regex: {e}"}
    lines = content.splitlines()
    matches = []
    for i, line in enumerate(lines, 1):
        if compiled.search(line):
            match_data = {"line": i, "content": line.rstrip()}
            if context > 0:
                start = max(0, i - context - 1)
                end = min(len(lines), i + context)
                match_data["context"] = {
                    "before": lines[start : i - 1] if i > 1 else [],
                    "after": lines[i:end],
                }
            matches.append(match_data)
    return {
        "ok": True,
        "file": path,
        "pattern": pattern,
        "match_count": len(matches),
        "matches": matches[:MAX_MATCHES_PER_FILE],
    }


def grep_workspace(
    pattern: str,
    workspace: Path,
    file_glob: str = "*",
    exclude_dirs: list = None,
    limit: int = 20,
) -> dict:
    """Search across all workspace files for a regex pattern."""
    if not workspace.exists():
        return {"ok": True, "results": [], "total_matches": 0}
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return {"ok": False, "error": f"Invalid regex: {e}"}
    if exclude_dirs is None:
        exclude_dirs = [".git", "node_modules", "vendor", "__pycache__", ".cache"]
    results = []
    total_matches = 0
    files_searched = 0
    for filepath in sorted(workspace.rglob(file_glob)):
        if files_searched >= MAX_FILES_TO_SEARCH:
            break
        if not filepath.is_file():
            continue
        if any(excluded in filepath.parts for excluded in exclude_dirs):
            continue
        if filepath.stat().st_size > MAX_FILE_SIZE:
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        file_matches = []
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if compiled.search(line):
                file_matches.append({"line": i, "content": line.rstrip()})
                if len(file_matches) >= 10:
                    break
        if file_matches:
            results.append(
                {
                    "file": str(filepath.relative_to(workspace)),
                    "match_count": len(file_matches),
                    "matches": file_matches,
                }
            )
            total_matches += len(file_matches)
            files_searched += 1
    return {
        "ok": True,
        "pattern": pattern,
        "file_glob": file_glob,
        "files_matched": len(results),
        "total_matches": total_matches,
        "results": results[:limit],
        "limit": limit,
        "files_searched": files_searched,
        "truncated": len(results) > limit,
    }
