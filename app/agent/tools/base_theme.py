import re
import shutil
from pathlib import Path

from ._paths import BASE_THEME_DIR, resolve_base_theme


def list_base_theme_files() -> dict:
    """List all files in the _s base theme."""
    if not BASE_THEME_DIR.exists():
        return {
            "ok": False,
            "error": "Base theme not found. Run scripts/download_s.sh first.",
        }
    files = []
    for p in sorted(BASE_THEME_DIR.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(BASE_THEME_DIR))
            files.append({"path": f"base_theme/{rel}", "size": p.stat().st_size})
    return {"ok": True, "files": files}


def read_base_theme_file(path: str) -> dict:
    """Read a file from the _s base theme."""
    full = resolve_base_theme(path)
    if not full:
        return {"ok": False, "error": f"Path escape blocked: {path}"}
    if not full.exists():
        return {"ok": False, "error": f"Base theme file not found: {path}"}
    try:
        content = full.read_text(encoding="utf-8")
        return {"ok": True, "content": content, "size": len(content)}
    except UnicodeDecodeError:
        return {"ok": False, "error": f"Cannot read binary file: {path}"}


def seed_workspace_with_base_theme(
    workspace: Path, theme_name: str, theme_slug: str, author: str
) -> dict:
    """Copy the _s base theme into output/ and replace slugs."""
    if not BASE_THEME_DIR.exists():
        return {
            "ok": False,
            "error": "Base theme not found. Run scripts/download_s.sh first.",
        }
    output_dir = workspace / theme_slug
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(str(BASE_THEME_DIR), str(output_dir))
    func_prefix = theme_slug.replace("-", "_")
    version_const = f"{func_prefix.upper()}_VERSION"
    replacements = [
        ("_S_VERSION", version_const),
        ("'_s'", f"'{theme_slug}'"),
        ("_s_", f"{func_prefix}_"),
        (" _s", f" {theme_name}"),
        ("_s-", f"{theme_slug}-"),
    ]
    files_modified = 0
    skip_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pot"}
    for filepath in output_dir.rglob("*"):
        if not filepath.is_file() or filepath.suffix in skip_exts:
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
            original = content
            for old, new in replacements:
                content = content.replace(old, new)
            if filepath.name == "style.css":
                content = re.sub(
                    r"Theme Name:\s*.*", f"Theme Name: {theme_name}", content
                )
                content = re.sub(
                    r"Author:\s*.*\n", f"Author: {author}\n", content, count=1
                )
                content = re.sub(r"Author URI:\s*.*", "Author URI: ", content)
                content = re.sub(r"Theme URI:\s*.*", "Theme URI: ", content)
                content = re.sub(
                    r"Text Domain:\s*.*", f"Text Domain: {theme_slug}", content
                )
                content = re.sub(
                    r"Description:\s*Hi\..*?(?=\n[A-Z])",
                    "Description: A custom WordPress theme converted from an HTML website.",
                    content,
                    flags=re.DOTALL,
                )
            if content != original:
                filepath.write_text(content, encoding="utf-8")
                files_modified += 1
        except UnicodeDecodeError, PermissionError:
            continue
    total_files = sum(1 for _ in output_dir.rglob("*") if _.is_file())
    return {
        "ok": True,
        "output_dir": str(output_dir),
        "total_files": total_files,
        "files_modified": files_modified,
    }
