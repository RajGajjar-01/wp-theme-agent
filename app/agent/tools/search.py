import re
from pathlib import Path

from ._paths import resolve_src


def search_in_file(path: str, pattern: str, workspace: Path) -> dict:
    """Search for a regex pattern in a single file and return matching lines."""
    full = resolve_src(path, workspace)
    if not full:
        return {"ok": False, "error": f"Path blocked: {path}"}
    if not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    try:
        content = full.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"ok": False, "error": f"Cannot read binary file: {path}"}

    matches = []
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
        for i, line in enumerate(content.splitlines(), 1):
            if compiled.search(line):
                matches.append({"line": i, "content": line.rstrip()})
    except re.error as e:
        return {"ok": False, "error": f"Invalid regex: {e}"}

    return {
        "ok": True,
        "file": path,
        "pattern": pattern,
        "match_count": len(matches),
        "matches": matches[:50],
    }


def grep_workspace(pattern: str, workspace: Path, file_glob: str = "*") -> dict:
    """Search across all workspace files for a regex pattern."""
    if not workspace.exists():
        return {"ok": True, "results": [], "total_matches": 0}

    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return {"ok": False, "error": f"Invalid regex: {e}"}

    results = []
    total_matches = 0

    for filepath in sorted(workspace.rglob(file_glob)):
        if not filepath.is_file():
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        file_matches = []
        for i, line in enumerate(content.splitlines(), 1):
            if compiled.search(line):
                file_matches.append({"line": i, "content": line.rstrip()})

        if file_matches:
            rel = str(filepath.relative_to(workspace))
            results.append(
                {
                    "file": rel,
                    "match_count": len(file_matches),
                    "matches": file_matches[:10],
                }
            )
            total_matches += len(file_matches)

    return {
        "ok": True,
        "pattern": pattern,
        "file_glob": file_glob,
        "files_matched": len(results),
        "total_matches": total_matches,
        "results": results[:20],
    }
