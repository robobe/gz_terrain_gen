from dataclasses import dataclass
from pathlib import Path

import click

from gz_terrain_gen.gazebo import DEFAULT_LEVEL_Z_SIZE_M
from gz_terrain_gen.log_config import LOG_LEVELS
from gz_terrain_gen.opentopo import DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON, DEFAULT_SIZE_KM
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, DEFAULT_TEXTURE, default_paths, validate_world_name
from gz_terrain_gen.tiling import DEFAULT_TILE_M

DEFAULT_WORLD_NAME = "terrain_world"


@dataclass(frozen=True)
class TerrainGenerationConfig:
    log_level: str
    world_name: str
    output_dir: Path
    center_lat: float
    center_lon: float
    size_km: float
    tile_m: int
    level_z_size_m: float
    dem_file: Path | None
    texture: Path


def click_world_name(_ctx: click.Context, _param: click.Parameter, value: str) -> str:
    try:
        return validate_world_name(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc)) from exc


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
    "--level-z-size-m",
    type=float,
    default=DEFAULT_LEVEL_Z_SIZE_M,
    show_default=True,
    help="Z size in meters for each Gazebo level geometry box.",
)
@click.option(
    "--dem-file",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Use an existing GeoTIFF DEM instead of downloading one.",
    default=None,
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
    level_z_size_m: float,
    dem_file: Path | None,
    texture: Path,
) -> TerrainGenerationConfig:
    return TerrainGenerationConfig(
        log_level=log_level.upper(),
        world_name=world_name,
        output_dir=output_dir,
        center_lat=center_lat,
        center_lon=center_lon,
        size_km=size_km,
        tile_m=tile_m,
        level_z_size_m=level_z_size_m,
        dem_file=dem_file,
        texture=texture,
    )


def parse_args(args: list[str] | None = None) -> TerrainGenerationConfig:
    return cli.main(args=args, standalone_mode=False)
