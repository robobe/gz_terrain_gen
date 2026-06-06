"""DEM source abstractions for preparing the canonical pipeline DEM.

See docs/dem_source.md for the source class hierarchy and docs/application_flow.md
for where DEM preparation fits in the pipeline.
"""

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from gz_terrain_gen.opentopo import DEFAULT_DEM_TYPE, download_dem


@dataclass(frozen=True)
class DemSourceResult:
    path: Path
    source_name: str


class DemSource(ABC):
    name: str

    @abstractmethod
    def prepare(self, output_path: Path) -> DemSourceResult:
        """Write or copy a readable GeoTIFF DEM to output_path."""


@dataclass(frozen=True)
class OpenTopographyDemSource(DemSource):
    center_lat: float
    center_lon: float
    size_km: float
    dem_type: str = DEFAULT_DEM_TYPE
    api_key: str | None = None

    name = "opentopography"

    def prepare(self, output_path: Path) -> DemSourceResult:
        path = download_dem(
            output_path,
            api_key=self.api_key,
            center_lat=self.center_lat,
            center_lon=self.center_lon,
            size_km=self.size_km,
            dem_type=self.dem_type,
        )
        return DemSourceResult(path=path, source_name=self.name)


@dataclass(frozen=True)
class LocalFileDemSource(DemSource):
    source_path: Path

    name = "local_file"

    def prepare(self, output_path: Path) -> DemSourceResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.source_path, output_path)
        return DemSourceResult(path=output_path, source_name=self.name)
