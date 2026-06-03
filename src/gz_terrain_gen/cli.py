import shutil
import shlex
from pathlib import Path

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
    viewer_metadata,
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
from gz_terrain_gen.viewer import generate_viewer

DEFAULT_WORLD_NAME = "terrain_world"


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
        "dem": world_dir / "dem.tif",
        "tiles": world_dir / "tiles",
        "manifest": world_dir / "tiles" / "tiles.csv",
        "mesh": world_dir / "mesh",
        "gz": world_dir / "gz",
        "viewer": world_dir / "viewer",
    }


def reset_existing_world_output(world_dir: Path) -> None:
    if not world_dir.exists():
        return

    click.confirm(
        f"Output folder {world_dir} already exists. Remove it and continue?",
        abort=True,
    )
    logger.info("removing existing world output folder: {}", world_dir)
    shutil.rmtree(world_dir)


def viewer_command(world_name: str, output_dir: Path) -> str:
    command = f"uv run gz-terrain-gen-viewer --world-name {world_name}"
    if output_dir != DEFAULT_OUTPUT_DIR:
        command += f" --output-dir {shlex.quote(str(output_dir))}"
    return command


def run_pipeline(
    world_name: str,
    output_dir: Path,
    center_lat: float,
    center_lon: float,
    size_km: float,
    tile_m: int,
    texture: Path,
) -> dict[str, Path]:
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

    logger.info("starting browser viewer generation for world {}", world_name)
    viewer_info = generate_viewer(paths["dem"], paths["tiles"], paths["manifest"], paths["viewer"])
    logger.info("completed browser viewer generation for world {}", world_name)
    logger.info("updating metadata: {}", paths["metadata"])
    update_metadata(
        paths["metadata"],
        world_name,
        {
            "viewer": viewer_metadata(viewer_info),
        },
    )
    click.echo(f"created viewer: {paths['viewer'] / 'index.html'}")
    click.echo(f"serve viewer: {viewer_command(world_name, output_dir)}")
    click.echo(f"metadata: {paths['metadata']}")
    logger.info("completed full terrain pipeline for world {}", world_name)
    return paths


@click.command(help="Generate a Gazebo terrain world from OpenTopography DEM data.")
@click.option(
    "--log-level",
    type=click.Choice(LOG_LEVELS, case_sensitive=False),
    default="INFO",
    show_default=True,
    help="Application log level.",
)
@click.option(
    "--world-name",
    callback=click_world_name,
    default=DEFAULT_WORLD_NAME,
    show_default=True,
    help="Gazebo world name and output folder name.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Generated artifact root; world files go under <output-dir>/<world-name>.",
)
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
def cli(
    log_level: str,
    world_name: str,
    output_dir: Path,
    center_lat: float,
    center_lon: float,
    size_km: float,
    tile_m: int,
    texture: Path,
) -> None:
    configure_logging(log_level)
    paths = default_paths(output_dir, world_name)
    reset_existing_world_output(paths["world"])
    run_pipeline(world_name, output_dir, center_lat, center_lon, size_km, tile_m, texture)
