import shutil
import shlex
from pathlib import Path

import click
from loguru import logger

from gz_terrain_gen import __version__
from gz_terrain_gen.cli import TerrainGenerationConfig, parse_args
from gz_terrain_gen.gazebo import generate_gazebo_worlds
from gz_terrain_gen.log_config import configure_logging
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
from gz_terrain_gen.opentopo import DEFAULT_DEM_TYPE, download_dem
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, WorldPaths, default_paths
from gz_terrain_gen.tiling import split_dem
from gz_terrain_gen.viewer import generate_viewer


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


def run_pipeline(config: TerrainGenerationConfig) -> WorldPaths:
    paths = default_paths(config.output_dir, config.world_name)
    logger.info("starting full terrain pipeline for world {}", config.world_name)
    logger.debug("resolved world output directory: {}", paths.world)
    logger.debug("download request center=({}, {}) size_km={}", config.center_lat, config.center_lon, config.size_km)

    if config.dem_file is None:
        logger.info("starting DEM download for world {}", config.world_name)
        download_dem(paths.dem, center_lat=config.center_lat, center_lon=config.center_lon, size_km=config.size_km)
        logger.info("completed DEM download: {}", paths.dem)
        request_metadata = requested_area_metadata(
            config.center_lat,
            config.center_lon,
            config.size_km,
            DEFAULT_DEM_TYPE,
            source="opentopography",
        )
        click.echo(f"DEM saved to {paths.dem}")
    else:
        logger.info("using existing DEM file for world {}: {}", config.world_name, config.dem_file)
        paths.dem.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config.dem_file, paths.dem)
        logger.info("copied DEM from {} to {}", config.dem_file, paths.dem)
        request_metadata = requested_area_metadata(
            config.center_lat,
            config.center_lon,
            config.size_km,
            DEFAULT_DEM_TYPE,
            source="local_file",
            source_path=config.dem_file,
        )
        click.echo(f"DEM copied from {config.dem_file} to {paths.dem}")

    logger.info("updating metadata: {}", paths.metadata)
    metadata = update_metadata(
        paths.metadata,
        config.world_name,
        {
            "request": request_metadata,
            "dem": dem_metadata(paths.dem),
        },
    )

    logger.info("starting DEM split for world {}", config.world_name)
    logger.debug("tile output directory: {}", paths.tiles)
    tile_count, manifest = split_dem(paths.dem, paths.tiles, config.tile_m)
    logger.info("completed DEM split: {} tiles", tile_count)
    logger.info("updating metadata: {}", paths.metadata)
    metadata = update_metadata(
        paths.metadata,
        config.world_name,
        {
            "tiles": tile_metadata(tile_count, config.tile_m, paths.tiles, manifest),
        },
    )
    click.echo(f"created {tile_count} tiles")
    click.echo(f"manifest: {manifest}")

    logger.info("starting mesh generation for world {}", config.world_name)
    logger.debug("mesh output directory: {}", paths.mesh)
    mesh_count = generate_meshes(paths.dem, paths.tiles, paths.manifest, paths.mesh)
    z_offset_m = source_z_offset(open_dem(paths.dem))
    logger.info("normalized mesh Z values by subtracting {:.3f} m", z_offset_m)
    logger.info("completed mesh generation: {} meshes", mesh_count)
    logger.info("updating metadata: {}", paths.metadata)
    metadata = update_metadata(
        paths.metadata,
        config.world_name,
        {
            "mesh": mesh_metadata(mesh_count, paths.mesh, z_offset_m),
        },
    )
    click.echo(f"created {mesh_count} meshes in {paths.mesh}")

    logger.info("starting Gazebo generation for world {}", config.world_name)
    logger.debug("Gazebo output directory: {}", paths.gz)
    gazebo_info = generate_gazebo_worlds(
        paths.manifest,
        paths.mesh,
        config.texture,
        paths.gz,
        config.world_name,
        config.level_z_size_m,
    )
    model_count = int(gazebo_info.model_count)
    logger.info("completed Gazebo generation: {} models", model_count)
    logger.info("updating metadata: {}", paths.metadata)
    metadata = update_metadata(
        paths.metadata,
        config.world_name,
        {
            "gazebo": gazebo_metadata(model_count, paths.gz, gazebo_info),
        },
    )
    click.echo(f"created {model_count} models in {paths.gz / 'models'}")
    click.echo(f"created world: {paths.gz / 'levels_terrain.sdf'}")

    logger.info("starting browser viewer generation for world {}", config.world_name)
    viewer_info = generate_viewer(paths.dem, paths.tiles, paths.manifest, paths.viewer)
    logger.info("completed browser viewer generation for world {}", config.world_name)
    logger.info("updating metadata: {}", paths.metadata)
    metadata = update_metadata(
        paths.metadata,
        config.world_name,
        {
            "viewer": viewer_metadata(viewer_info),
        },
    )
    click.echo(f"created viewer: {paths.viewer / 'index.html'}")
    click.echo(f"serve viewer: {viewer_command(config.world_name, config.output_dir)}")
    click.echo(f"metadata: {paths.metadata}")
    echo_banner(format_completion_summary(metadata, paths.metadata))
    logger.info("completed full terrain pipeline for world {}", config.world_name)
    return paths


def run_application(config: TerrainGenerationConfig) -> WorldPaths:
    configure_logging(config.log_level)
    paths = default_paths(config.output_dir, config.world_name)
    reset_existing_world_output(paths.world)
    echo_banner(format_start_banner(__version__, config.world_name, paths.world))
    return run_pipeline(config)


def main(args: list[str] | None = None) -> None:
    try:
        config = parse_args(args)
    except click.ClickException as exc:
        exc.show()
        raise SystemExit(exc.exit_code) from exc
    except click.exceptions.Exit as exc:
        raise SystemExit(exc.exit_code) from exc

    if not isinstance(config, TerrainGenerationConfig):
        raise SystemExit(config)

    run_application(config)
