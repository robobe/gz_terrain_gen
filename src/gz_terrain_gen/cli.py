from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

import click
from loguru import logger

from gz_terrain_gen.gazebo import generate_gazebo_worlds
from gz_terrain_gen.log_config import LOG_LEVELS, configure_logging
from gz_terrain_gen.mesh import generate_meshes
from gz_terrain_gen.metadata import (
    dem_metadata,
    gazebo_metadata,
    mesh_metadata,
    requested_area_metadata,
    tile_metadata,
    update_metadata,
)
from gz_terrain_gen.opentopo import (
    DEFAULT_CENTER_LAT,
    DEFAULT_CENTER_LON,
    DEFAULT_DEM_TYPE,
    DEFAULT_SIZE_KM,
    download_dem,
)
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, DEFAULT_TEXTURE, validate_world_name
from gz_terrain_gen.tiling import DEFAULT_TILE_M, split_dem

F = TypeVar("F", bound=Callable[..., Any])


def click_world_name(_ctx: click.Context, _param: click.Parameter, value: str) -> str:
    try:
        return validate_world_name(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc)) from exc


def default_paths(output_dir: Path, world_name: str) -> dict[str, Path]:
    world_dir = output_dir / validate_world_name(world_name)
    return {
        "world": world_dir,
        "metadata": world_dir / "metadata.json",
        "dem": world_dir / "dem_1km.tif",
        "tiles": world_dir / "tiles",
        "manifest": world_dir / "tiles" / "tiles.csv",
        "mesh": world_dir / "mesh",
        "gz": world_dir / "gz",
    }


def common_output_options(func: F) -> F:
    @click.option(
        "--output-dir",
        type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
        default=DEFAULT_OUTPUT_DIR,
        show_default=True,
        help="Generated artifact root; world files go under <output-dir>/<world-name>.",
    )
    @click.option(
        "--world-name",
        required=True,
        callback=click_world_name,
        help="Gazebo world name and output folder name.",
    )
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@click.group(help="Generate tiled Gazebo terrain from OpenTopography DEM data.")
@click.option(
    "--log-level",
    type=click.Choice(LOG_LEVELS, case_sensitive=False),
    default="INFO",
    show_default=True,
    help="Application log level.",
)
def main(log_level: str) -> None:
    configure_logging(log_level)


@main.command(help="Download a DEM from OpenTopography.")
@common_output_options
@click.option("--output", "output_path", type=click.Path(path_type=Path, dir_okay=False), help="DEM output path.")
@click.option("--center-lat", type=float, default=DEFAULT_CENTER_LAT, show_default=True)
@click.option("--center-lon", type=float, default=DEFAULT_CENTER_LON, show_default=True)
@click.option("--size-km", type=float, default=DEFAULT_SIZE_KM, show_default=True)
def download(
    world_name: str,
    output_dir: Path,
    output_path: Path | None,
    center_lat: float,
    center_lon: float,
    size_km: float,
) -> None:
    paths = default_paths(output_dir, world_name)
    output = output_path or paths["dem"]
    logger.info("starting DEM download for world {}", world_name)
    logger.debug("download output path: {}", output)
    logger.debug("download request center=({}, {}) size_km={}", center_lat, center_lon, size_km)
    download_dem(output, center_lat=center_lat, center_lon=center_lon, size_km=size_km)
    logger.info("completed DEM download: {}", output)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "request": requested_area_metadata(center_lat, center_lon, size_km, DEFAULT_DEM_TYPE),
            "dem": dem_metadata(output),
        },
    )
    click.echo(f"DEM saved to {output}")
    click.echo(f"metadata: {paths['metadata']}")


@main.command(help="Split the DEM into GeoTIFF tiles.")
@common_output_options
@click.option("--input", "input_path", type=click.Path(path_type=Path, dir_okay=False), help="Source DEM path.")
@click.option("--tiles-dir", type=click.Path(path_type=Path, file_okay=False), help="Tile output directory.")
@click.option("--tile-m", type=int, default=DEFAULT_TILE_M, show_default=True)
def split(
    world_name: str,
    output_dir: Path,
    input_path: Path | None,
    tiles_dir: Path | None,
    tile_m: int,
) -> None:
    paths = default_paths(output_dir, world_name)
    dem = input_path or paths["dem"]
    tile_output_dir = tiles_dir or paths["tiles"]
    logger.info("starting DEM split for world {}", world_name)
    logger.debug("split input DEM: {}", dem)
    logger.debug("tile output directory: {}", tile_output_dir)
    tile_count, manifest = split_dem(dem, tile_output_dir, tile_m)
    logger.info("completed DEM split: {} tiles", tile_count)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "dem": dem_metadata(dem),
            "tiles": tile_metadata(tile_count, tile_m, tile_output_dir, manifest),
        },
    )
    click.echo(f"created {tile_count} tiles")
    click.echo(f"manifest: {manifest}")
    click.echo(f"metadata: {paths['metadata']}")


@main.command(help="Convert tile GeoTIFFs to Collada meshes.")
@common_output_options
@click.option("--source-dem", type=click.Path(path_type=Path, dir_okay=False), help="Source DEM path.")
@click.option("--tiles-dir", type=click.Path(path_type=Path, file_okay=False), help="Tile directory.")
@click.option("--manifest", type=click.Path(path_type=Path, dir_okay=False), help="Tile manifest path.")
@click.option("--mesh-dir", type=click.Path(path_type=Path, file_okay=False), help="Mesh output directory.")
def mesh(
    world_name: str,
    output_dir: Path,
    source_dem: Path | None,
    tiles_dir: Path | None,
    manifest: Path | None,
    mesh_dir: Path | None,
) -> None:
    paths = default_paths(output_dir, world_name)
    dem = source_dem or paths["dem"]
    tile_dir = tiles_dir or paths["tiles"]
    manifest_path = manifest or paths["manifest"]
    mesh_output_dir = mesh_dir or paths["mesh"]
    logger.info("starting mesh generation for world {}", world_name)
    logger.debug("mesh source DEM: {}", dem)
    logger.debug("mesh tiles directory: {}", tile_dir)
    logger.debug("mesh manifest path: {}", manifest_path)
    logger.debug("mesh output directory: {}", mesh_output_dir)
    count = generate_meshes(dem, tile_dir, manifest_path, mesh_output_dir)
    logger.info("completed mesh generation: {} meshes", count)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "dem": dem_metadata(dem),
            "mesh": mesh_metadata(count, mesh_output_dir),
        },
    )
    click.echo(f"created {count} meshes in {mesh_output_dir}")
    click.echo(f"metadata: {paths['metadata']}")


@main.command(help="Create Gazebo models and SDF worlds.")
@common_output_options
@click.option("--manifest", type=click.Path(path_type=Path, dir_okay=False), help="Tile manifest path.")
@click.option("--mesh-dir", type=click.Path(path_type=Path, file_okay=False), help="Mesh input directory.")
@click.option(
    "--texture",
    type=click.Path(path_type=Path, dir_okay=False),
    default=DEFAULT_TEXTURE,
    show_default=True,
)
@click.option("--gz-dir", type=click.Path(path_type=Path, file_okay=False), help="Gazebo output directory.")
def gazebo(
    world_name: str,
    output_dir: Path,
    manifest: Path | None,
    mesh_dir: Path | None,
    texture: Path,
    gz_dir: Path | None,
) -> None:
    paths = default_paths(output_dir, world_name)
    manifest_path = manifest or paths["manifest"]
    mesh_input_dir = mesh_dir or paths["mesh"]
    gazebo_dir = gz_dir or paths["gz"]
    logger.info("starting Gazebo generation for world {}", world_name)
    logger.debug("Gazebo manifest path: {}", manifest_path)
    logger.debug("Gazebo mesh input directory: {}", mesh_input_dir)
    logger.debug("Gazebo output directory: {}", gazebo_dir)
    count = generate_gazebo_worlds(manifest_path, mesh_input_dir, texture, gazebo_dir, world_name)
    logger.info("completed Gazebo generation: {} models", count)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "gazebo": gazebo_metadata(count, gazebo_dir),
        },
    )
    click.echo(f"created {count} models in {gazebo_dir / 'models'}")
    click.echo(f"created world: {gazebo_dir / 'levels_terrain.sdf'}")
    click.echo(f"created single tile world: {gazebo_dir / 'single_tile_terrain.sdf'}")
    click.echo(f"created travel script: {gazebo_dir / 'travel_levels.sh'}")
    click.echo(f"metadata: {paths['metadata']}")


@main.command(help="Run download, split, mesh, and gazebo.")
@common_output_options
@click.option("--center-lat", type=float, default=DEFAULT_CENTER_LAT, show_default=True)
@click.option("--center-lon", type=float, default=DEFAULT_CENTER_LON, show_default=True)
@click.option("--size-km", type=float, default=DEFAULT_SIZE_KM, show_default=True)
@click.option("--tile-m", type=int, default=DEFAULT_TILE_M, show_default=True)
@click.option(
    "--texture",
    type=click.Path(path_type=Path, dir_okay=False),
    default=DEFAULT_TEXTURE,
    show_default=True,
)
def all(
    world_name: str,
    output_dir: Path,
    center_lat: float,
    center_lon: float,
    size_km: float,
    tile_m: int,
    texture: Path,
) -> None:
    paths = default_paths(output_dir, world_name)
    logger.info("starting full terrain pipeline for world {}", world_name)
    logger.debug("resolved world output directory: {}", paths["world"])
    logger.debug("download request center=({}, {}) size_km={}", center_lat, center_lon, size_km)

    logger.info("starting DEM download for world {}", world_name)
    download_dem(paths["dem"], center_lat=center_lat, center_lon=center_lon, size_km=size_km)
    logger.info("completed DEM download: {}", paths["dem"])
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "request": requested_area_metadata(center_lat, center_lon, size_km, DEFAULT_DEM_TYPE),
            "dem": dem_metadata(paths["dem"]),
        },
    )
    click.echo(f"DEM saved to {paths['dem']}")

    logger.info("starting DEM split for world {}", world_name)
    logger.debug("tile output directory: {}", paths["tiles"])
    tile_count, manifest = split_dem(paths["dem"], paths["tiles"], tile_m)
    logger.info("completed DEM split: {} tiles", tile_count)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "tiles": tile_metadata(tile_count, tile_m, paths["tiles"], manifest),
        },
    )
    click.echo(f"created {tile_count} tiles")
    click.echo(f"manifest: {manifest}")

    logger.info("starting mesh generation for world {}", world_name)
    logger.debug("mesh output directory: {}", paths["mesh"])
    mesh_count = generate_meshes(paths["dem"], paths["tiles"], paths["manifest"], paths["mesh"])
    logger.info("completed mesh generation: {} meshes", mesh_count)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "mesh": mesh_metadata(mesh_count, paths["mesh"]),
        },
    )
    click.echo(f"created {mesh_count} meshes in {paths['mesh']}")

    logger.info("starting Gazebo generation for world {}", world_name)
    logger.debug("Gazebo output directory: {}", paths["gz"])
    model_count = generate_gazebo_worlds(paths["manifest"], paths["mesh"], texture, paths["gz"], world_name)
    logger.info("completed Gazebo generation: {} models", model_count)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "gazebo": gazebo_metadata(model_count, paths["gz"]),
        },
    )
    click.echo(f"created {model_count} models in {paths['gz'] / 'models'}")
    click.echo(f"created world: {paths['gz'] / 'levels_terrain.sdf'}")
    click.echo(f"metadata: {paths['metadata']}")
    logger.info("completed full terrain pipeline for world {}", world_name)
