import csv
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


def write_dae(path: Path, name: str, vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]) -> None:
    flat_vertices = " ".join(f"{x:.6f} {y:.6f} {z:.6f}" for x, y, z in vertices)
    flat_faces = " ".join(str(index) for face in faces for index in face)
    vertex_count = len(vertices)
    triangle_count = len(faces)
    safe_name = escape(name)

    dae = f"""<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <unit name="meter" meter="1"/>
    <up_axis>Z_UP</up_axis>
  </asset>
  <library_geometries>
    <geometry id="{safe_name}-mesh" name="{safe_name}">
      <mesh>
        <source id="{safe_name}-positions">
          <float_array id="{safe_name}-positions-array" count="{vertex_count * 3}">
            {flat_vertices}
          </float_array>
          <technique_common>
            <accessor source="#{safe_name}-positions-array" count="{vertex_count}" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="{safe_name}-vertices">
          <input semantic="POSITION" source="#{safe_name}-positions"/>
        </vertices>
        <triangles count="{triangle_count}">
          <input semantic="VERTEX" source="#{safe_name}-vertices" offset="0"/>
          <p>{flat_faces}</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="{safe_name}" name="{safe_name}">
        <instance_geometry url="#{safe_name}-mesh"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>
"""
    path.write_text(dae)


def open_dem(path: Path) -> tuple[Any, Any, float | None, tuple[float, ...]]:
    from osgeo import gdal

    dataset = gdal.Open(str(path))
    if dataset is None:
        raise FileNotFoundError(path)

    band = dataset.GetRasterBand(1)
    elevation = band.ReadAsArray().astype(float)
    nodata = band.GetNoDataValue()
    inverse_transform = gdal.InvGeoTransform(dataset.GetGeoTransform())
    return dataset, elevation, nodata, inverse_transform


def sample_dem(elevation: Any, nodata: float | None, inverse_transform: tuple[float, ...], lon: float, lat: float) -> float:
    px = inverse_transform[0] + inverse_transform[1] * lon + inverse_transform[2] * lat
    py = inverse_transform[3] + inverse_transform[4] * lon + inverse_transform[5] * lat

    height, width = elevation.shape
    px = min(max(px, 0.0), width - 1.0)
    py = min(max(py, 0.0), height - 1.0)

    x0 = int(px)
    y0 = int(py)
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)
    tx = px - x0
    ty = py - y0

    samples = [
        (elevation[y0, x0], (1.0 - tx) * (1.0 - ty)),
        (elevation[y0, x1], tx * (1.0 - ty)),
        (elevation[y1, x0], (1.0 - tx) * ty),
        (elevation[y1, x1], tx * ty),
    ]

    weighted_sum = 0.0
    weight_sum = 0.0
    for value, weight in samples:
        if nodata is not None and value == nodata:
            continue
        weighted_sum += value * weight
        weight_sum += weight

    if weight_sum == 0.0:
        return 0.0
    return weighted_sum / weight_sum


def tile_shape(tile_path: Path) -> tuple[int, int]:
    from osgeo import gdal

    dataset = gdal.Open(str(tile_path))
    if dataset is None:
        raise FileNotFoundError(tile_path)
    return dataset.RasterXSize, dataset.RasterYSize


def tile_to_mesh(tile: dict[str, str], source: tuple[Any, Any, float | None, tuple[float, ...]], tiles_dir: Path) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    _dem_dataset, elevation, nodata, inverse_transform = source
    tile_path = tiles_dir / tile["file"]
    cols, rows = tile_shape(tile_path)

    west = float(tile["west"])
    south = float(tile["south"])
    east = float(tile["east"])
    north = float(tile["north"])
    width_m = (float(tile["gazebo_center_x_m"]) - float(tile["gazebo_corner_x_m"])) * 2.0
    height_m = (float(tile["gazebo_center_y_m"]) - float(tile["gazebo_corner_y_m"])) * 2.0

    vertices = []
    for row in range(rows + 1):
        v = row / rows
        lat = north - (v * (north - south))
        y = (height_m / 2.0) - (v * height_m)

        for col in range(cols + 1):
            u = col / cols
            lon = west + (u * (east - west))
            x = (-width_m / 2.0) + (u * width_m)
            z = sample_dem(elevation, nodata, inverse_transform, lon, lat)
            vertices.append((x, y, z))

    faces = []
    stride = cols + 1
    for row in range(rows):
        for col in range(cols):
            i00 = row * stride + col
            i10 = row * stride + col + 1
            i01 = (row + 1) * stride + col
            i11 = (row + 1) * stride + col + 1
            faces.append((i00, i01, i10))
            faces.append((i10, i01, i11))

    return vertices, faces


def generate_meshes(source_dem: Path, tiles_dir: Path, manifest_path: Path, mesh_dir: Path) -> int:
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing tile manifest: {manifest_path}")
    if not source_dem.exists():
        raise FileNotFoundError(f"missing DEM: {source_dem}")

    mesh_dir.mkdir(parents=True, exist_ok=True)
    with manifest_path.open(newline="") as manifest:
        rows = list(csv.DictReader(manifest))
    source = open_dem(source_dem)

    for row in rows:
        mesh_name = Path(row["file"]).stem
        mesh_path = mesh_dir / f"{mesh_name}.dae"
        vertices, faces = tile_to_mesh(row, source, tiles_dir)
        write_dae(mesh_path, mesh_name, vertices, faces)

    return len(rows)
