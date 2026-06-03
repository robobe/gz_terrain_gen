import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_ASSETS_DIR = PROJECT_ROOT / "assets"
DEFAULT_TEXTURE = DEFAULT_ASSETS_DIR / "texture" / "soil.jpg"
WORLD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def validate_world_name(value: str) -> str:
    if not WORLD_NAME_PATTERN.fullmatch(value):
        raise ValueError(
            "world name must match ^[A-Za-z0-9][A-Za-z0-9_-]*$"
        )
    return value
