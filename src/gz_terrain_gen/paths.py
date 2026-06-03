from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_ASSETS_DIR = PROJECT_ROOT / "assets"
DEFAULT_TEXTURE = DEFAULT_ASSETS_DIR / "texture" / "soil.jpg"
