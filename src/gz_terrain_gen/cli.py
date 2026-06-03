import shutil
import shlex
from pathlib import Path

import click
from loguru import logger

from gz_terrain_gen import __version__
from gz_terrain_gen.gazebo import generate_gazebo_worlds
from gz_terrain_gen.log_config import LOG_LEVELS, configure_logging
from gz_terrain_gen.mesh import generate_meshes, open_dem, source_z_offset
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


def format_start_banner(version: str, world_name: str, world_dir: Path) -> str:
    return "\n".join(
        [
            "GZ Terrain Generator",
            f"Version: {version}",
            f"World: {world_name}",
            f"Output: {world_dir}",
        ]
    )


def format_number(value: object, precision: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{precision}f}"
    return str(value)


def format_completion_summary(metadata: dict, metadata_path: Path) -> str:
    request = metadata.get("request", {})
    dem = metadata.get("dem", {})
    elevation = dem.get("elevation", {})
    bounds = request.get("bounds", {})
    mesh = metadata.get("mesh", {})
    tiles = metadata.get("tiles", {})
    gazebo = metadata.get("gazebo", {})
    viewer = metadata.get("viewer", {})
    size_km = request.get("size_km")

    return "\n".join(
        [
            "Generation Summary",
            f"World: {metadata.get('world_name', 'n/a')}",
            f"Area: {format_number(size_km, 3)} km x {format_number(size_km, 3)} km",
            f"Center: {format_number(request.get('center_lat'), 6)}, {format_number(request.get('center_lon'), 6)}",
            (
                "Bounds: "
                f"west={format_number(bounds.get('west'), 6)}, "
                f"south={format_number(bounds.get('south'), 6)}, "
                f"east={format_number(bounds.get('east'), 6)}, "
                f"north={format_number(bounds.get('north'), 6)}"
            ),
            (
                "Elevation: "
                f"min={format_number(elevation.get('minimum_m'), 3)} m, "
                f"max={format_number(elevation.get('maximum_m'), 3)} m, "
                f"mean={format_number(elevation.get('mean_m'), 3)} m"
            ),
            (
                "Z normalization: "
                f"{'enabled' if mesh.get('normalized_to_gazebo_z_zero') else 'disabled'}, "
                f"offset={format_number(mesh.get('z_offset_m'), 3)} m"
            ),
            f"Tiles: {format_number(tiles.get('count'))} at {format_number(tiles.get('tile_m'))} m",
            f"Meshes: {format_number(mesh.get('count'))}",
            f"Gazebo models: {format_number(gazebo.get('model_count'))}",
            f"Viewer: {viewer.get('html_path', 'n/a')}",
            f"Metadata: {metadata_path}",
        ]
    )


def echo_banner(text: str) -> None:
    click.echo()
    click.echo(text)
    click.echo()


def run_pipeline(
    world_name: str,
    output_dir: Path,
    center_lat: float,
    center_lon: float,
    size_km: float,
    tile_m: int,
    texture: Path,
    dem_file: Path | None = None,
) -> dict[str, Path]:
    paths = default_paths(output_dir, world_name)
    logger.info("starting full terrain pipeline for world {}", world_name)
    logger.debug("resolved world output directory: {}", paths["world"])
    logger.debug("download request center=({}, {}) size_km={}", center_lat, center_lon, size_km)

    if dem_file is None:
        logger.info("starting DEM download for world {}", world_name)
        download_dem(paths["dem"], center_lat=center_lat, center_lon=center_lon, size_km=size_km)
        logger.info("completed DEM download: {}", paths["dem"])
        request_metadata = requested_area_metadata(
            center_lat,
            center_lon,
            size_km,
            DEFAULT_DEM_TYPE,
            source="opentopography",
        )
        click.echo(f"DEM saved to {paths['dem']}")
    else:
        logger.info("using existing DEM file for world {}: {}", world_name, dem_file)
        paths["dem"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dem_file, paths["dem"])
        logger.info("copied DEM from {} to {}", dem_file, paths["dem"])
        request_metadata = requested_area_metadata(
            center_lat,
            center_lon,
            size_km,
            DEFAULT_DEM_TYPE,
            source="local_file",
            source_path=dem_file,
        )
        click.echo(f"DEM copied from {dem_file} to {paths['dem']}")

    logger.info("updating metadata: {}", paths["metadata"])
    metadata = update_metadata(
        paths["metadata"],
        world_name,
        {
            "request": request_metadata,
            "dem": dem_metadata(paths["dem"]),
        },
    )

    logger.info("starting DEM split for world {}", world_name)
    logger.debug("tile output directory: {}", paths["tiles"])
    tile_count, manifest = split_dem(paths["dem"], paths["tiles"], tile_m)
    logger.info("completed DEM split: {} tiles", tile_count)
    logger.info("updating metadata: {}", paths["metadata"])
    metadata = update_metadata(
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
    z_offset_m = source_z_offset(open_dem(paths["dem"]))
    logger.info("normalized mesh Z values by subtracting {:.3f} m", z_offset_m)
    logger.info("completed mesh generation: {} meshes", mesh_count)
    logger.info("updating metadata: {}", paths["metadata"])
    metadata = update_metadata(
        paths["metadata"],
        world_name,
        {
            "mesh": mesh_metadata(mesh_count, paths["mesh"], z_offset_m),
        },
    )
    click.echo(f"created {mesh_count} meshes in {paths['mesh']}")

    logger.info("starting Gazebo generation for world {}", world_name)
    logger.debug("Gazebo output directory: {}", paths["gz"])
    model_count = generate_gazebo_worlds(paths["manifest"], paths["mesh"], texture, paths["gz"], world_name)
    logger.info("completed Gazebo generation: {} models", model_count)
    logger.info("updating metadata: {}", paths["metadata"])
    metadata = update_metadata(
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
    metadata = update_metadata(
        paths["metadata"],
        world_name,
        {
            "viewer": viewer_metadata(viewer_info),
        },
    )
    click.echo(f"created viewer: {paths['viewer'] / 'index.html'}")
    click.echo(f"serve viewer: {viewer_command(world_name, output_dir)}")
    click.echo(f"metadata: {paths['metadata']}")
    echo_banner(format_completion_summary(metadata, paths["metadata"]))
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
    "--dem-file",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Use an existing GeoTIFF DEM instead of downloading one.",
)
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
    dem_file: Path | None,
    texture: Path,
) -> None:
    configure_logging(log_level)
    paths = default_paths(output_dir, world_name)
    reset_existing_world_output(paths["world"])
    echo_banner(format_start_banner(__version__, world_name, paths["world"]))
    run_pipeline(world_name, output_dir, center_lat, center_lon, size_km, tile_m, texture, dem_file)
