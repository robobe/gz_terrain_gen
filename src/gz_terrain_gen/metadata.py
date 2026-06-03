import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from loguru import logger

from gz_terrain_gen.opentopo import bounds_for_square

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_metadata(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    logger.debug("wrote metadata file: {}", path)


def update_metadata(path: Path, world_name: str, sections: dict[str, Any]) -> dict[str, Any]:
    logger.debug("updating metadata sections {} for world {}", sorted(sections), world_name)
    data = read_metadata(path)
    now = utc_now()
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("world_name", world_name)
    data.setdefault("created_at", now)
    data["schema_version"] = SCHEMA_VERSION
    data["world_name"] = world_name
    data["updated_at"] = now

    for key, value in sections.items():
        data[key] = value

    write_metadata(path, data)
    return data


def requested_area_metadata(
    center_lat: float,
    center_lon: float,
    size_km: float,
    dem_type: str,
) -> dict[str, Any]:
    return {
        "center_lat": center_lat,
        "center_lon": center_lon,
        "size_km": size_km,
        "dem_type": dem_type,
        "bounds": bounds_for_square(center_lat, center_lon, size_km),
    }


def dem_metadata(path: Path) -> dict[str, Any]:
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        valid = data.compressed()
        if valid.size == 0:
            elevation = {
                "minimum_m": None,
                "maximum_m": None,
                "mean_m": None,
            }
        else:
            elevation = {
                "minimum_m": float(np.min(valid)),
                "maximum_m": float(np.max(valid)),
                "mean_m": float(np.mean(valid)),
            }

        bounds = {
            "west": float(src.bounds.left),
            "south": float(src.bounds.bottom),
            "east": float(src.bounds.right),
            "north": float(src.bounds.top),
        }

        return {
            "path": str(path),
            "bounds": bounds,
            "center": {
                "lat": (bounds["south"] + bounds["north"]) / 2.0,
                "lon": (bounds["west"] + bounds["east"]) / 2.0,
            },
            "crs": str(src.crs) if src.crs else None,
            "width_px": src.width,
            "height_px": src.height,
            "nodata": src.nodata,
            "elevation": elevation,
        }


def tile_metadata(tile_count: int, tile_m: int, tiles_dir: Path, manifest_path: Path) -> dict[str, Any]:
    return {
        "tile_m": tile_m,
        "count": tile_count,
        "tiles_dir": str(tiles_dir),
        "manifest_path": str(manifest_path),
    }


def mesh_metadata(mesh_count: int, mesh_dir: Path) -> dict[str, Any]:
    return {
        "count": mesh_count,
        "mesh_dir": str(mesh_dir),
    }


def gazebo_metadata(model_count: int, gz_dir: Path) -> dict[str, Any]:
    return {
        "model_count": model_count,
        "gz_dir": str(gz_dir),
        "models_dir": str(gz_dir / "models"),
        "levels_sdf": str(gz_dir / "levels_terrain.sdf"),
        "single_tile_sdf": str(gz_dir / "single_tile_terrain.sdf"),
        "travel_script": str(gz_dir / "travel_levels.sh"),
    }


def viewer_metadata(viewer_info: dict[str, Any]) -> dict[str, Any]:
    return {
        "viewer_dir": str(viewer_info["viewer_dir"]),
        "glb_path": str(viewer_info["glb_path"]),
        "html_path": str(viewer_info["html_path"]),
        "vertex_count": viewer_info["vertex_count"],
        "face_count": viewer_info["face_count"],
    }
