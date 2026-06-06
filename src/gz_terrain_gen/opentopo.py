"""OpenTopography DEM request helpers for terrain generation.

See docs/application_flow.md for where DEM preparation fits in the pipeline.
"""

import math
import os
from pathlib import Path

import requests


DEFAULT_CENTER_LAT = 30.611505
DEFAULT_CENTER_LON = 34.808504
DEFAULT_SIZE_KM = 2.0
DEFAULT_DEM_TYPE = "COP30"
OPENTOPOGRAPHY_URL = "https://portal.opentopography.org/API/globaldem"


def bounds_for_square(center_lat: float, center_lon: float, size_km: float) -> dict[str, float]:
    half_km = size_km / 2.0
    dlat = half_km / 111.32
    dlon = half_km / (111.32 * math.cos(math.radians(center_lat)))
    return {
        "south": center_lat - dlat,
        "north": center_lat + dlat,
        "west": center_lon - dlon,
        "east": center_lon + dlon,
    }


def download_dem(
    output_path: Path,
    api_key: str | None = None,
    center_lat: float = DEFAULT_CENTER_LAT,
    center_lon: float = DEFAULT_CENTER_LON,
    size_km: float = DEFAULT_SIZE_KM,
    dem_type: str = DEFAULT_DEM_TYPE,
) -> Path:
    api_key = api_key or os.environ.get("OPENTOPOGRAPHY_API_KEY")
    if not api_key:
        raise RuntimeError("missing OPENTOPOGRAPHY_API_KEY")

    params = {
        "demtype": dem_type,
        **bounds_for_square(center_lat, center_lon, size_km),
        "outputFormat": "GTiff",
        "API_Key": api_key,
    }

    response = requests.get(OPENTOPOGRAPHY_URL, params=params, timeout=120)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return output_path
