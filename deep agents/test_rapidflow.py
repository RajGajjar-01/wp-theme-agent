"""Test script for RapidFlow Plumbing website.

Usage:
    cd "deep agents"
    python test_rapidflow.py
"""

import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent

# Load .env from both locations
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "generation.log", mode="w"),
    ],
)

# Also enable LangChain debug logging
os.environ["LANGCHAIN_DEBUG"] = "true"

logger = logging.getLogger("test")

sys.path.insert(0, str(ROOT))

from agents import generate_theme

RAPIDFLOW_DIR = ROOT.parent / "examples" / "upload" / "uploads"


def load_rapidflow_files() -> dict[str, str]:
    """Load all HTML, CSS, JS files from rapidflow folder."""
    files = {}

    for html_file in RAPIDFLOW_DIR.glob("*.html"):
        files[html_file.name] = html_file.read_text(encoding="utf-8")
        logger.info(f"Loaded: {html_file.name} ({len(files[html_file.name])} chars)")

    for css_file in (RAPIDFLOW_DIR / "css").glob("*.css"):
        files[f"css/{css_file.name}"] = css_file.read_text(encoding="utf-8")
        logger.info(
            f"Loaded: css/{css_file.name} ({len(files[f'css/{css_file.name}'])} chars)"
        )

    for js_file in (RAPIDFLOW_DIR / "js").glob("*.js"):
        files[f"js/{js_file.name}"] = js_file.read_text(encoding="utf-8")
        logger.info(
            f"Loaded: js/{js_file.name} ({len(files[f'js/{js_file.name}'])} chars)"
        )

    return files


def test_rapidflow():
    """Generate WordPress theme from RapidFlow Plumbing website."""
    logger.info("=" * 70)
    logger.info("RAPIDFLOW PLUMBING THEME GENERATION TEST")
    logger.info("=" * 70)

    if not RAPIDFLOW_DIR.exists():
        logger.error(f"RapidFlow folder not found at {RAPIDFLOW_DIR}")
        return None

    logger.info("Loading source files...")
    uploaded_files = load_rapidflow_files()

    if not uploaded_files:
        logger.error("No files loaded")
        return None

    logger.info(f"Total files loaded: {len(uploaded_files)}")

    # Show file sizes
    total_chars = sum(len(c) for c in uploaded_files.values())
    logger.info(
        f"Total content size: {total_chars:,} chars (~{total_chars // 4:,} tokens estimated)"
    )

    logger.info("-" * 70)
    logger.info("STARTING THEME GENERATION...")
    logger.info("-" * 70)

    result = generate_theme(
        theme_name="RapidFlow Plumbing",
        theme_slug="rapidflow-plumbing",
        author="Deep Agents Test",
        uploaded_files=uploaded_files,
        use_sub_agents=False,
    )

    logger.info("-" * 70)
    logger.info(f"RESULT: {'SUCCESS' if result['ok'] else 'FAILED'}")
    logger.info(f"Theme path: {result['theme_path']}")
    logger.info("-" * 70)

    theme_dir = Path(result["theme_path"])
    if theme_dir.exists():
        logger.info("Generated files:")
        file_count = 0
        for f in sorted(theme_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(theme_dir)
                size = f.stat().st_size
                logger.info(f"  {rel} ({size:,} bytes)")
                file_count += 1
        logger.info(f"Total files generated: {file_count}")
    else:
        logger.warning("Theme directory not created!")

    logger.info("=" * 70)
    logger.info("Log file saved to: generation.log")
    logger.info("=" * 70)

    return result


if __name__ == "__main__":
    test_rapidflow()
