# Application Flow

This diagram shows the main terrain-generation application blocks and how data
moves between them. The application starts with CLI input, creates terrain
artifacts under the selected world output folder, records the reduced
application metadata shape, and prints a final summary.

```mermaid
flowchart LR
    CLI["CLI"]
    Main["Main Orchestrator"]
    DEM["DEM Preparation"]
    Metadata["Metadata Request"]
    Tiling["DEM Tiling"]
    Mesh["Mesh Generation"]
    Gazebo["Gazebo Generation"]
    Viewer["Viewer Generation"]
    Outputs["Outputs"]

    CLI --> Main
    Main --> DEM
    DEM --> Metadata
    DEM --> Tiling
    Tiling --> Metadata
    Tiling --> Mesh
    Tiling --> Gazebo
    Tiling --> Viewer
    Mesh --> Metadata
    Mesh --> Gazebo
    Mesh --> Viewer
    Gazebo --> Outputs
    Viewer --> Outputs
    Metadata --> Outputs
```

## Block Summaries

- `CLI`: parses world name, coordinates, area size, optional DEM file, output
  directory, tile size, texture path, and log level.
- `Main Orchestrator`: configures logging, confirms output-folder reset, prints
  start/completion banners, and runs the pipeline stages in order.
- `DEM Preparation`: downloads a DEM from OpenTopography or copies the local
  `--dem-file` into the world output folder as `dem.tif`.
- `Metadata Request`: records the reduced application metadata: world name,
  requested center/size, requested bounds, elevation stats, tile count, mesh
  count, and Z normalization.
- `DEM Tiling`: splits the DEM into tile rasters and writes `tiles.csv`, which
  later stages use for placement and sizing.
- `Mesh Generation`: converts tile data into normalized Collada terrain meshes
  and records mesh count plus Z offset.
- `Gazebo Generation`: creates Gazebo terrain models, worlds, levels, GUI
  camera setup, and the level probe model. These outputs are generated but are
  not first-class metadata sections.
- `Viewer Generation`: creates the combined browser-viewable `terrain.glb` and
  `index.html`. These outputs are generated but are not first-class metadata
  sections.
- `Outputs`: stores generated artifacts under `outputs/<world-name>/`, including
  DEM, tiles, meshes, Gazebo files, viewer files, and application metadata.

## Execution Order

```mermaid
flowchart TD
    Parse["Parse CLI"]
    Reset["Reset output folder"]
    PrepareDem["Prepare DEM"]
    RequestMeta["Write request metadata"]
    SplitTiles["Split tiles"]
    TileMeta["Write tile metadata"]
    GenerateMeshes["Generate meshes"]
    MeshMeta["Write mesh metadata"]
    GenerateGazebo["Generate Gazebo"]
    GenerateViewer["Generate viewer"]
    PrintSummary["Print summary"]

    Parse --> Reset
    Reset --> PrepareDem
    PrepareDem --> RequestMeta
    RequestMeta --> SplitTiles
    SplitTiles --> TileMeta
    TileMeta --> GenerateMeshes
    GenerateMeshes --> MeshMeta
    MeshMeta --> GenerateGazebo
    GenerateGazebo --> GenerateViewer
    GenerateViewer --> PrintSummary
```
