from pathlib import Path

ROOT = Path(__file__).parent.parent
BASE_THEME_ROOT = ROOT / "base_theme"
WORKSPACE_ROOT = ROOT / "workspaces"


def resolve_workspace(path: str, workspace: Path) -> Path | None:
    """Resolve and validate a path within workspace."""
    full = (workspace / path).resolve()
    try:
        full.relative_to(workspace)
        return full
    except ValueError:
        return None


def resolve_base_theme(path: str) -> Path | None:
    """Resolve and validate a path within base_theme."""
    full = (BASE_THEME_ROOT / path).resolve()
    try:
        full.relative_to(BASE_THEME_ROOT)
        return full
    except ValueError:
        return None
