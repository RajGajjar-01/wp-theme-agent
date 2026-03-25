import re
from pathlib import Path

from ._paths import resolve


def _simple_replace(
    content: str, old: str, new: str, replace_all: bool
) -> tuple[str | None, int]:
    """Exact string match and replace."""
    count = content.count(old)
    if count == 0:
        return None, 0
    return (
        content.replace(old, new) if replace_all else content.replace(old, new, 1)
    ), count


def _line_trimmed_replace(
    content: str, old: str, new: str, replace_all: bool
) -> tuple[str | None, int]:
    """Strip trailing whitespace from each line before matching."""

    def _trim_lines(text: str) -> str:
        return "\n".join(line.rstrip() for line in text.splitlines())

    norm_content = _trim_lines(content)
    norm_old = _trim_lines(old)
    count = norm_content.count(norm_old)
    if count == 0:
        return None, 0
    norm_new = _trim_lines(new)
    result = (
        norm_content.replace(norm_old, norm_new)
        if replace_all
        else norm_content.replace(norm_old, norm_new, 1)
    )
    return result, count


def _whitespace_normalized_replace(
    content: str, old: str, new: str, replace_all: bool
) -> tuple[str | None, int]:
    """Collapse all whitespace runs to a single space for matching."""

    def _collapse(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    norm_content = _collapse(content)
    norm_old = _collapse(old)
    if not norm_old or norm_old not in norm_content:
        return None, 0
    count = norm_content.count(norm_old)
    norm_new = _collapse(new)
    result = (
        norm_content.replace(norm_old, norm_new)
        if replace_all
        else norm_content.replace(norm_old, norm_new, 1)
    )
    return result, count


_STRATEGIES = [
    ("SimpleReplacer", _simple_replace),
    ("LineTrimmedReplacer", _line_trimmed_replace),
    ("WhitespaceNormalizedReplacer", _whitespace_normalized_replace),
]


def edit_file(path: str, edits: list[dict], workspace: Path) -> dict:
    """Apply a list of search-and-replace edits to an existing file."""
    full = resolve(path, workspace)
    if full is None:
        return {"ok": False, "error": f"Path escape blocked: {path}"}
    if not full.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    try:
        content = full.read_text(encoding="utf-8")
    except Exception as exc:
        return {"ok": False, "error": f"Cannot read file: {exc}"}
    edits_applied = 0
    for i, edit in enumerate(edits):
        old_text = edit.get("old_text", "")
        new_text = edit.get("new_text", "")
        replace_all: bool = bool(edit.get("replace_all", False))
        if not old_text:
            return {"ok": False, "error": f"Edit #{i + 1}: 'old_text' is empty"}
        matched = False
        for strategy_name, strategy_fn in _STRATEGIES:
            result, count = strategy_fn(content, old_text, new_text, replace_all)
            if result is None or count == 0:
                continue
            if not replace_all and count > 1:
                return {
                    "ok": False,
                    "error": f"Edit #{i + 1}: Found {count} matches using {strategy_name}. Provide more context in 'old_text' or set replace_all=true.",
                }
            content = result
            edits_applied += 1
            matched = True
            break
        if not matched:
            return {
                "ok": False,
                "error": f"Edit #{i + 1}: 'old_text' not found in {path} (tried SimpleReplacer, LineTrimmedReplacer, WhitespaceNormalizedReplacer)",
            }
    if edits_applied > 0:
        try:
            full.write_text(content, encoding="utf-8")
        except Exception as exc:
            return {"ok": False, "error": f"Cannot write file: {exc}"}
    return {"ok": True, "path": path, "edits_applied": edits_applied}
