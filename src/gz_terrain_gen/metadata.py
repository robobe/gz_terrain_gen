from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from loguru import logger

from gz_terrain_gen.opentopo import bounds_for_square

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class GeoBounds:
    west: float
    south: float
    east: float
    north: float


@dataclass(frozen=True)
class ElevationStats:
    minimum_m: float | None
    maximum_m: float | None
    mean_m: float | None


@dataclass(frozen=True)
class RequestMetadata:
    center_lat: float
    center_lon: float
    size_km: float
    bounds: GeoBounds
    elevation: ElevationStats


@dataclass(frozen=True)
class TileMetadata:
    tile_m: int
    count: int


@dataclass(frozen=True)
class MeshMetadata:
    count: int
    normalized_to_gazebo_z_zero: bool
    z_offset_m: float


@dataclass(frozen=True)
class MetadataUpdate:
    request: RequestMetadata | None = None
    tiles: TileMetadata | None = None
    mesh: MeshMetadata | None = None


@dataclass(frozen=True)
class MetadataDocument:
    schema_version: int = SCHEMA_VERSION
    world_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    request: RequestMetadata | None = None
    tiles: TileMetadata | None = None
    mesh: MeshMetadata | None = None
    extra: dict[str, Any] | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _omit_none(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _omit_none(asdict(value))
    if isinstance(value, dict):
        return {key: _omit_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_omit_none(item) for item in value]
    return value


def metadata_to_dict(document: MetadataDocument) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if document.extra:
        data.update(document.extra)

    for field in fields(MetadataDocument):
        if field.name == "extra":
            continue
        value = getattr(document, field.name)
        if value is not None:
            data[field.name] = _omit_none(value)

    return data


def _geo_bounds_from_dict(data: dict[str, Any]) -> GeoBounds:
    return GeoBounds(
        west=float(data["west"]),
        south=float(data["south"]),
        east=float(data["east"]),
        north=float(data["north"]),
    )


def _elevation_stats_from_dict(data: dict[str, Any]) -> ElevationStats:
    return ElevationStats(
        minimum_m=data.get("minimum_m"),
        maximum_m=data.get("maximum_m"),
        mean_m=data.get("mean_m"),
    )


def _request_from_dict(data: dict[str, Any]) -> RequestMetadata:
    return RequestMetadata(
        center_lat=float(data["center_lat"]),
        center_lon=float(data["center_lon"]),
        size_km=float(data["size_km"]),
        bounds=_geo_bounds_from_dict(data["bounds"]),
        elevation=_elevation_stats_from_dict(data["elevation"]),
    )


def _tiles_from_dict(data: dict[str, Any]) -> TileMetadata:
    return TileMetadata(
        tile_m=int(data["tile_m"]),
        count=int(data["count"]),
    )


def _mesh_from_dict(data: dict[str, Any]) -> MeshMetadata:
    return MeshMetadata(
        count=int(data["count"]),
        normalized_to_gazebo_z_zero=bool(data["normalized_to_gazebo_z_zero"]),
        z_offset_m=float(data["z_offset_m"]),
    )


def metadata_from_dict(data: dict[str, Any]) -> MetadataDocument:
    known_keys = {field.name for field in fields(MetadataDocument) if field.name != "extra"}
    extra = {key: value for key, value in data.items() if key not in known_keys}
    return MetadataDocument(
        schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        world_name=data.get("world_name"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        request=_request_from_dict(data["request"]) if data.get("request") else None,
        tiles=_tiles_from_dict(data["tiles"]) if data.get("tiles") else None,
        mesh=_mesh_from_dict(data["mesh"]) if data.get("mesh") else None,
        extra=extra or None,
    )


def read_metadata(path: Path) -> MetadataDocument:
    if not path.exists():
        return MetadataDocument()
    return metadata_from_dict(json.loads(path.read_text()))


def write_metadata(path: Path, document: MetadataDocument) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata_to_dict(document), indent=2, sort_keys=True) + "\n")
    logger.debug("wrote metadata file: {}", path)


def update_metadata(path: Path, world_name: str, update: MetadataUpdate) -> MetadataDocument:
    updated_sections = [field.name for field in fields(MetadataUpdate) if getattr(update, field.name) is not None]
    logger.debug("updating metadata sections {} for world {}", sorted(updated_sections), world_name)
    document = read_metadata(path)
    now = utc_now()
    updated = replace(
        document,
        schema_version=SCHEMA_VERSION,
        world_name=world_name,
        created_at=document.created_at or now,
        updated_at=now,
    )

    for field in fields(MetadataUpdate):
        value = getattr(update, field.name)
        if value is not None:
            updated = replace(updated, **{field.name: value})

    write_metadata(path, updated)
    return updated


def elevation_stats(path: Path) -> ElevationStats:
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        valid = data.compressed()
        if valid.size == 0:
            return ElevationStats(minimum_m=None, maximum_m=None, mean_m=None)
        return ElevationStats(
            minimum_m=float(np.min(valid)),
            maximum_m=float(np.max(valid)),
            mean_m=float(np.mean(valid)),
        )


def requested_area_metadata(
    center_lat: float,
    center_lon: float,
    size_km: float,
    elevation: ElevationStats,
) -> RequestMetadata:
    bounds = bounds_for_square(center_lat, center_lon, size_km)
    return RequestMetadata(
        center_lat=center_lat,
        center_lon=center_lon,
        size_km=size_km,
        bounds=_geo_bounds_from_dict(bounds),
        elevation=elevation,
    )


def tile_metadata(tile_count: int, tile_m: int) -> TileMetadata:
    return TileMetadata(
        tile_m=tile_m,
        count=tile_count,
    )


def mesh_metadata(mesh_count: int, z_offset_m: float = 0.0) -> MeshMetadata:
    return MeshMetadata(
        count=mesh_count,
        normalized_to_gazebo_z_zero=True,
        z_offset_m=z_offset_m,
    )
