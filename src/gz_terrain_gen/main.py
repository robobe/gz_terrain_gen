import shutil
import shlex
from dataclasses import dataclass
from pathlib import Path

import click
from loguru import logger

from gz_terrain_gen import __version__
from gz_terrain_gen.cli import TerrainGenerationConfig, parse_args
from gz_terrain_gen.dem_source import DemSource, LocalFileDemSource, OpenTopographyDemSource
from gz_terrain_gen.gazebo import GazeboGenerationResult, generate_gazebo_worlds
from gz_terrain_gen.log_config import configure_logging
from gz_terrain_gen.mesh import generate_meshes, open_dem, source_z_offset
from gz_terrain_gen.metadata import (
    MetadataDocument,
    MetadataUpdate,
    RequestMetadata,
    elevation_stats,
    mesh_metadata,
    requested_area_metadata,
    tile_metadata,
    update_metadata,
)
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, WorldPaths, default_paths
from gz_terrain_gen.tiling import split_dem
from gz_terrain_gen.viewer import ViewerGenerationResult, generate_viewer


@dataclass(frozen=True)
class DemStageResult:
    request_metadata: RequestMetadata


@dataclass(frozen=True)
class TileStageResult:
    tile_count: int
    manifest: Path


@dataclass(frozen=True)
class MeshStageResult:
    mesh_count: int
    z_offset_m: float


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


def format_completion_summary(metadata: MetadataDocument, metadata_path: Path) -> str:
    request = metadata.request
    elevation = request.elevation if request else None
    bounds = request.bounds if request else None
    mesh = metadata.mesh
    tiles = metadata.tiles
    size_km = request.size_km if request else None

    return "\n".join(
        [
            "Generation Summary",
            f"World: {metadata.world_name or 'n/a'}",
            f"Area: {format_number(size_km, 3)} km x {format_number(size_km, 3)} km",
            (
                "Center: "
                f"{format_number(request.center_lat if request else None, 6)}, "
                f"{format_number(request.center_lon if request else None, 6)}"
            ),
            (
                "Bounds: "
                f"west={format_number(bounds.west if bounds else None, 6)}, "
                f"south={format_number(bounds.south if bounds else None, 6)}, "
                f"east={format_number(bounds.east if bounds else None, 6)}, "
                f"north={format_number(bounds.north if bounds else None, 6)}"
            ),
            (
                "Elevation: "
                f"min={format_number(elevation.minimum_m if elevation else None, 3)} m, "
                f"max={format_number(elevation.maximum_m if elevation else None, 3)} m, "
                f"mean={format_number(elevation.mean_m if elevation else None, 3)} m"
            ),
            (
                "Z normalization: "
                f"{'enabled' if mesh and mesh.normalized_to_gazebo_z_zero else 'disabled'}, "
                f"offset={format_number(mesh.z_offset_m if mesh else None, 3)} m"
            ),
            f"Tiles: {format_number(tiles.count if tiles else None)} at {format_number(tiles.tile_m if tiles else None)} m",
            f"Meshes: {format_number(mesh.count if mesh else None)}",
            f"Metadata: {metadata_path}",
        ]
    )


def echo_banner(text: str) -> None:
    click.echo()
    click.echo(text)
    click.echo()


def dem_source_from_config(config: TerrainGenerationConfig) -> DemSource:
    if config.dem_file is not None:
        return LocalFileDemSource(config.dem_file)
    return OpenTopographyDemSource(
        center_lat=config.center_lat,
        center_lon=config.center_lon,
        size_km=config.size_km,
    )


def prepare_dem(config: TerrainGenerationConfig, paths: WorldPaths) -> DemStageResult:
    dem_source = dem_source_from_config(config)
    logger.info("preparing DEM for world {} using {}", config.world_name, dem_source.name)
    result = dem_source.prepare(paths.dem)
    logger.info("DEM prepared by {} at {}", result.source_name, result.path)

    stats = elevation_stats(result.path)
    request_metadata = requested_area_metadata(config.center_lat, config.center_lon, config.size_km, stats)
    logger.debug("recorded request metadata using {} DEM source", result.source_name)
    return DemStageResult(request_metadata=request_metadata)


def record_dem_stage(config: TerrainGenerationConfig, paths: WorldPaths, result: DemStageResult) -> MetadataDocument:
    logger.info("updating metadata: {}", paths.metadata)
    return update_metadata(
        paths.metadata,
        config.world_name,
        MetadataUpdate(request=result.request_metadata),
    )


def split_tiles_stage(config: TerrainGenerationConfig, paths: WorldPaths) -> TileStageResult:
    logger.info("Starting DEM split for world {}", config.world_name)
    logger.debug("tile output directory: {}", paths.tiles)
    tile_count, manifest = split_dem(paths.dem, paths.tiles, config.tile_m)
    logger.info("completed DEM split: {} tiles", tile_count)
    logger.info("csv manifest: {}", manifest)
    logger.info("End DEM split for world {}", config.world_name)
    return TileStageResult(tile_count=tile_count, manifest=manifest)


def record_tile_stage(config: TerrainGenerationConfig, paths: WorldPaths, result: TileStageResult) -> MetadataDocument:
    logger.info("updating metadata: {}", paths.metadata)
    return update_metadata(
        paths.metadata,
        config.world_name,
        MetadataUpdate(tiles=tile_metadata(result.tile_count, config.tile_m)),
    )


def generate_mesh_stage(config: TerrainGenerationConfig, paths: WorldPaths) -> MeshStageResult:
    logger.info("Starting mesh generation for world {}", config.world_name)
    logger.debug("mesh output directory: {}", paths.mesh)
    mesh_count = generate_meshes(paths.dem, paths.tiles, paths.manifest, paths.mesh)
    z_offset_m = source_z_offset(open_dem(paths.dem))
    logger.info("normalized mesh Z values by subtracting {:.3f} m", z_offset_m)
    logger.info("created {} meshes in {}", mesh_count, paths.mesh)
    logger.info("End mesh generation for world {}", config.world_name)
    return MeshStageResult(mesh_count=mesh_count, z_offset_m=z_offset_m)


def record_mesh_stage(config: TerrainGenerationConfig, paths: WorldPaths, result: MeshStageResult) -> MetadataDocument:
    logger.info("updating metadata: {}", paths.metadata)
    return update_metadata(
        paths.metadata,
        config.world_name,
        MetadataUpdate(mesh=mesh_metadata(result.mesh_count, result.z_offset_m)),
    )


def generate_gazebo_stage(config: TerrainGenerationConfig, paths: WorldPaths) -> GazeboGenerationResult:
    logger.info("Starting Gazebo generation for world {}", config.world_name)
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
    logger.info("created {} models in {}", model_count, paths.gz / "models")
    logger.info("created world: {}", paths.gz / "levels_terrain.sdf")
    logger.info("End Gazebo generation for world {}", config.world_name)
    return gazebo_info


def generate_viewer_stage(config: TerrainGenerationConfig, paths: WorldPaths) -> ViewerGenerationResult:
    logger.info("Starting browser viewer generation for world {}", config.world_name)
    viewer_info = generate_viewer(paths.dem, paths.tiles, paths.manifest, paths.viewer)
    logger.info("created viewer: {}", paths.viewer / "index.html")
    logger.info("End browser viewer generation for world {}", config.world_name)
    return viewer_info


def print_pipeline_completion(config: TerrainGenerationConfig, paths: WorldPaths, metadata: MetadataDocument) -> None:
    click.echo(f"serve viewer: {viewer_command(config.world_name, config.output_dir)}")
    click.echo(f"metadata: {paths.metadata}")
    echo_banner(format_completion_summary(metadata, paths.metadata))


def run_pipeline(config: TerrainGenerationConfig) -> WorldPaths:
    paths = default_paths(config.output_dir, config.world_name)
    logger.info("starting full terrain pipeline for world {}", config.world_name)
    logger.debug("resolved world output directory: {}", paths.world)
    logger.debug("download request center=({}, {}) size_km={}", config.center_lat, config.center_lon, config.size_km)

    # fetch DEM data
    dem_result = prepare_dem(config, paths)
    record_dem_stage(config, paths, dem_result)

    # split DEM into tiles 
    tile_result = split_tiles_stage(config, paths)
    record_tile_stage(config, paths, tile_result)

    # generate meshes from tiles
    mesh_result = generate_mesh_stage(config, paths)
    metadata = record_mesh_stage(config, paths, mesh_result)

    # generate Gazebo world and models
    gazebo_info = generate_gazebo_stage(config, paths)
    logger.debug("Gazebo metadata section omitted from application metadata: {} models", gazebo_info.model_count)

    # generate mesh viewer using browser-based WebGL
    viewer_info = generate_viewer_stage(config, paths)
    logger.debug("Viewer metadata section omitted from application metadata: {}", viewer_info.html_path)

    # print summary 
    print_pipeline_completion(config, paths, metadata)
    logger.info("completed full terrain pipeline for world {}", config.world_name)
    return paths


def run_application(config: TerrainGenerationConfig) -> None:
    configure_logging(config.log_level)
    paths = default_paths(config.output_dir, config.world_name)
    reset_existing_world_output(paths.world)
    echo_banner(format_start_banner(__version__, config.world_name, paths.world))
    run_pipeline(config)


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
