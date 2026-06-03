import argparse
from pathlib import Path

from gz_terrain_gen.gazebo import generate_gazebo_worlds
from gz_terrain_gen.mesh import generate_meshes
from gz_terrain_gen.opentopo import DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON, DEFAULT_SIZE_KM, download_dem
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, DEFAULT_TEXTURE
from gz_terrain_gen.tiling import DEFAULT_TILE_M, split_dem


def default_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "dem": output_dir / "dem_1km.tif",
        "tiles": output_dir / "tiles",
        "manifest": output_dir / "tiles" / "tiles.csv",
        "mesh": output_dir / "mesh",
        "gz": output_dir / "gz",
    }


def add_common_output_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"generated artifact root (default: {DEFAULT_OUTPUT_DIR})",
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
    paths = default_paths(args.output_dir)
    output = args.output or paths["dem"]
    download_dem(output, center_lat=args.center_lat, center_lon=args.center_lon, size_km=args.size_km)
    print(f"DEM saved to {output}")


def run_split(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir)
    dem = args.input or paths["dem"]
    tiles_dir = args.tiles_dir or paths["tiles"]
    tile_count, manifest = split_dem(dem, tiles_dir, args.tile_m)
    print(f"created {tile_count} tiles")
    print(f"manifest: {manifest}")


def run_mesh(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir)
    source_dem = args.source_dem or paths["dem"]
    tiles_dir = args.tiles_dir or paths["tiles"]
    manifest = args.manifest or paths["manifest"]
    mesh_dir = args.mesh_dir or paths["mesh"]
    count = generate_meshes(source_dem, tiles_dir, manifest, mesh_dir)
    print(f"created {count} meshes in {mesh_dir}")


def run_gazebo(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir)
    manifest = args.manifest or paths["manifest"]
    mesh_dir = args.mesh_dir or paths["mesh"]
    gz_dir = args.gz_dir or paths["gz"]
    count = generate_gazebo_worlds(manifest, mesh_dir, args.texture, gz_dir)
    print(f"created {count} models in {gz_dir / 'models'}")
    print(f"created world: {gz_dir / 'levels_terrain.sdf'}")
    print(f"created single tile world: {gz_dir / 'single_tile_terrain.sdf'}")
    print(f"created travel script: {gz_dir / 'travel_levels.sh'}")


def run_all(args: argparse.Namespace) -> None:
    paths = default_paths(args.output_dir)
    download_dem(paths["dem"], center_lat=args.center_lat, center_lon=args.center_lon, size_km=args.size_km)
    print(f"DEM saved to {paths['dem']}")
    tile_count, manifest = split_dem(paths["dem"], paths["tiles"], args.tile_m)
    print(f"created {tile_count} tiles")
    print(f"manifest: {manifest}")
    mesh_count = generate_meshes(paths["dem"], paths["tiles"], paths["manifest"], paths["mesh"])
    print(f"created {mesh_count} meshes in {paths['mesh']}")
    model_count = generate_gazebo_worlds(paths["manifest"], paths["mesh"], args.texture, paths["gz"])
    print(f"created {model_count} models in {paths['gz'] / 'models'}")
    print(f"created world: {paths['gz'] / 'levels_terrain.sdf'}")


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
