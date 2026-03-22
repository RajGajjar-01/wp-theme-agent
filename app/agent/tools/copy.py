import re
import shutil
from pathlib import Path

from ._paths import resolve, resolve_src


def copy_file(src: str, dest: str, workspace: Path) -> dict:
    """Copy a file efficiently without needing to output its content."""
    src_full = resolve_src(src, workspace)
    if not src_full:
        return {"ok": False, "error": f"Source path blocked: {src}"}
    if not src_full.exists():
        return {"ok": False, "error": f"Source file not found: {src}"}

    dest_full = resolve(dest, workspace)
    if not dest_full:
        return {"ok": False, "error": f"Destination path blocked: {dest}"}

    dest_full.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src_full), str(dest_full))

    return {"ok": True, "src": src, "dest": dest, "size": dest_full.stat().st_size}


def copy_section(
    src_file: str,
    dest_file: str,
    start_pattern: str,
    end_pattern: str,
    workspace: Path,
    mode: str = "append",
) -> dict:
    """Extract a section between regex patterns from a source file and append/overwrite a destination file."""
    src_full = resolve_src(src_file, workspace)
    if not src_full:
        return {"ok": False, "error": f"Source path blocked: {src_file}"}
    if not src_full.exists():
        return {"ok": False, "error": f"Source file not found: {src_file}"}

    dest_full = resolve(dest_file, workspace)
    if not dest_full:
        return {"ok": False, "error": f"Destination path blocked: {dest_file}"}

    try:
        content = src_full.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"ok": False, "error": f"Cannot read binary file: {src_file}"}

    try:
        start_match = re.search(start_pattern, content)
        if not start_match:
            return {"ok": False, "error": f"Start pattern not found: {start_pattern}"}

        remaining = content[start_match.start() :]
        end_match = re.search(end_pattern, remaining[len(start_match.group()) :])

        if not end_match:
            section = remaining
        else:
            end_pos = len(start_match.group()) + end_match.end()
            section = remaining[:end_pos]

    except re.error as e:
        return {"ok": False, "error": f"Invalid regex: {e}"}

    dest_full.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append" and dest_full.exists():
        existing = dest_full.read_text(encoding="utf-8")
        dest_full.write_text(existing + "\n" + section, encoding="utf-8")
    else:
        dest_full.write_text(section, encoding="utf-8")

    return {
        "ok": True,
        "src": src_file,
        "dest": dest_file,
        "section_size": len(section),
        "mode": mode,
    }
