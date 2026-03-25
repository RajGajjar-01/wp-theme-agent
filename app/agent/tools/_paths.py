from pathlib import Path

BASE_THEME_DIR = Path(__file__).parent.parent / "base_theme"


def resolve(path: str, workspace: Path) -> Path | None:
    """Resolve a path safely inside the workspace."""
    full = (workspace / path).resolve()
    if not str(full).startswith(str(workspace.resolve())):
        return None
    return full


def resolve_base_theme(path: str) -> Path | None:
    """Resolve a path safely inside the base_theme folder."""
    full = (BASE_THEME_DIR / path).resolve()
    if not str(full).startswith(str(BASE_THEME_DIR.resolve())):
        return None
    return full


def resolve_src(path: str, workspace: Path, theme_slug: str = "output") -> Path | None:
    """Resolve a source path from base_theme, uploads, or theme folder."""
    if path.startswith("base_theme/"):
        relative = path[len("base_theme/") :]
        return resolve_base_theme(relative)
    return resolve(path, workspace)
