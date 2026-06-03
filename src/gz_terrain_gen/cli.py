import argparse
from pathlib import Path

from gz_terrain_gen.gazebo import generate_gazebo_worlds
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


def argparse_world_name(value: str) -> str:
    try:
        return validate_world_name(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


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


def add_common_output_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--world-name",
        required=True,
        type=argparse_world_name,
        help="Gazebo world name and output folder name",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"generated artifact root; world files go under <output-dir>/<world-name> (default: {DEFAULT_OUTPUT_DIR})",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gz-terrain-gen",
        description="Generate tiled Gazebo terrain from OpenTopography DEM data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="download a DEM from OpenTopography")
    add_common_output_arg(download_parser)
    download_parser.add_argument("--output", type=Path, help="DEM output path")
    download_parser.add_argument("--center-lat", type=float, default=DEFAULT_CENTER_LAT)
    download_parser.add_argument("--center-lon", type=float, default=DEFAULT_CENTER_LON)
    download_parser.add_argument("--size-km", type=float, default=DEFAULT_SIZE_KM)

    split_parser = subparsers.add_parser("split", help="split the DEM into GeoTIFF tiles")
    add_common_output_arg(split_parser)
    split_parser.add_argument("--input", type=Path, help="source DEM path")
    split_parser.add_argument("--tiles-dir", type=Path, help="tile output directory")
    split_parser.add_argument("--tile-m", type=int, default=DEFAULT_TILE_M)

    mesh_parser = subparsers.add_parser("mesh", help="convert tile GeoTIFFs to Collada meshes")
    add_common_output_arg(mesh_parser)
    mesh_parser.add_argument("--source-dem", type=Path, help="source DEM path")
    mesh_parser.add_argument("--tiles-dir", type=Path, help="tile directory")
    mesh_parser.add_argument("--manifest", type=Path, help="tile manifest path")
    mesh_parser.add_argument("--mesh-dir", type=Path, help="mesh output directory")

    gazebo_parser = subparsers.add_parser("gazebo", help="create Gazebo models and SDF worlds")
    add_common_output_arg(gazebo_parser)
    gazebo_parser.add_argument("--manifest", type=Path, help="tile manifest path")
    gazebo_parser.add_argument("--mesh-dir", type=Path, help="mesh input directory")
    gazebo_parser.add_argument("--texture", type=Path, default=DEFAULT_TEXTURE)
    gazebo_parser.add_argument("--gz-dir", type=Path, help="Gazebo output directory")

    all_parser = subparsers.add_parser("all", help="run download, split, mesh, and gazebo")
    add_common_output_arg(all_parser)
    all_parser.add_argument("--center-lat", type=float, default=DEFAULT_CENTER_LAT)
    all_parser.add_argument("--center-lon", type=float, default=DEFAULT_CENTER_LON)
    all_parser.add_argument("--size-km", type=float, default=DEFAULT_SIZE_KM)
    all_parser.add_argument("--tile-m", type=int, default=DEFAULT_TILE_M)
    all_parser.add_argument("--texture", type=Path, default=DEFAULT_TEXTURE)

    return parser


def run_download(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir, args.world_name)
    output = args.output or paths["dem"]
    download_dem(output, center_lat=args.center_lat, center_lon=args.center_lon, size_km=args.size_km)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "request": requested_area_metadata(args.center_lat, args.center_lon, args.size_km, DEFAULT_DEM_TYPE),
            "dem": dem_metadata(output),
        },
    )
    print(f"DEM saved to {output}")
    print(f"metadata: {paths['metadata']}")


def run_split(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir, args.world_name)
    dem = args.input or paths["dem"]
    tiles_dir = args.tiles_dir or paths["tiles"]
    tile_count, manifest = split_dem(dem, tiles_dir, args.tile_m)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "dem": dem_metadata(dem),
            "tiles": tile_metadata(tile_count, args.tile_m, tiles_dir, manifest),
        },
    )
    print(f"created {tile_count} tiles")
    print(f"manifest: {manifest}")
    print(f"metadata: {paths['metadata']}")


def run_mesh(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir, args.world_name)
    source_dem = args.source_dem or paths["dem"]
    tiles_dir = args.tiles_dir or paths["tiles"]
    manifest = args.manifest or paths["manifest"]
    mesh_dir = args.mesh_dir or paths["mesh"]
    count = generate_meshes(source_dem, tiles_dir, manifest, mesh_dir)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "dem": dem_metadata(source_dem),
            "mesh": mesh_metadata(count, mesh_dir),
        },
    )
    print(f"created {count} meshes in {mesh_dir}")
    print(f"metadata: {paths['metadata']}")


def run_gazebo(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir, args.world_name)
    manifest = args.manifest or paths["manifest"]
    mesh_dir = args.mesh_dir or paths["mesh"]
    gz_dir = args.gz_dir or paths["gz"]
    count = generate_gazebo_worlds(manifest, mesh_dir, args.texture, gz_dir, args.world_name)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "gazebo": gazebo_metadata(count, gz_dir),
        },
    )
    print(f"created {count} models in {gz_dir / 'models'}")
    print(f"created world: {gz_dir / 'levels_terrain.sdf'}")
    print(f"created single tile world: {gz_dir / 'single_tile_terrain.sdf'}")
    print(f"created travel script: {gz_dir / 'travel_levels.sh'}")
    print(f"metadata: {paths['metadata']}")


def run_all(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir, args.world_name)
    download_dem(paths["dem"], center_lat=args.center_lat, center_lon=args.center_lon, size_km=args.size_km)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "request": requested_area_metadata(args.center_lat, args.center_lon, args.size_km, DEFAULT_DEM_TYPE),
            "dem": dem_metadata(paths["dem"]),
        },
    )
    print(f"DEM saved to {paths['dem']}")
    tile_count, manifest = split_dem(paths["dem"], paths["tiles"], args.tile_m)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "tiles": tile_metadata(tile_count, args.tile_m, paths["tiles"], manifest),
        },
    )
    print(f"created {tile_count} tiles")
    print(f"manifest: {manifest}")
    mesh_count = generate_meshes(paths["dem"], paths["tiles"], paths["manifest"], paths["mesh"])
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "mesh": mesh_metadata(mesh_count, paths["mesh"]),
        },
    )
    print(f"created {mesh_count} meshes in {paths['mesh']}")
    model_count = generate_gazebo_worlds(paths["manifest"], paths["mesh"], args.texture, paths["gz"], args.world_name)
    update_metadata(
        paths["metadata"],
        args.world_name,
        {
            "gazebo": gazebo_metadata(model_count, paths["gz"]),
        },
    )
    print(f"created {model_count} models in {paths['gz'] / 'models'}")
    print(f"created world: {paths['gz'] / 'levels_terrain.sdf'}")
    print(f"metadata: {paths['metadata']}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        run_download(args)
    elif args.command == "split":
        run_split(args)
    elif args.command == "mesh":
        run_mesh(args)
    elif args.command == "gazebo":
        run_gazebo(args)
    elif args.command == "all":
        run_all(args)
    else:
        parser.error(f"unknown command: {args.command}")
