"""Residents per populated grid cell: read a population raster over Penang, assign cells to districts, rescale to DOSM totals."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
import shapely
from rasterio.transform import xy
from rasterio.windows import Window, from_bounds
from shapely.geometry.base import BaseGeometry

from .load import DISTRICTS, Bounds
from .sources import META_MEMBER


@dataclass(frozen=True)
class Cells:
    lon: np.ndarray  # cell centres
    lat: np.ndarray
    people: np.ndarray  # residents, after rescaling to the district totals
    district: np.ndarray  # index into DISTRICTS


def meta_path(zip_path: Path) -> str:
    """GDAL path that reads the Meta GeoTIFF inside its zip in place, so the 17.4 GB file is never extracted."""
    return f"/vsizip/{zip_path}/{META_MEMBER}"


def window_for(src: rasterio.DatasetReader, bounds: Bounds) -> Window:
    """Whole-cell window covering bounds, clipped to the raster."""
    w = from_bounds(*bounds, transform=src.transform)
    col0, row0 = math.floor(w.col_off), math.floor(w.row_off)
    col1, row1 = math.ceil(w.col_off + w.width), math.ceil(w.row_off + w.height)
    return Window(col0, row0, col1 - col0, row1 - row0).intersection(Window(0, 0, src.width, src.height))


def read_populated(raster: str, bounds: Bounds) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Centre lon, centre lat and value of every cell above zero in the window. Nodata, including NaN, counts as zero."""
    with rasterio.open(raster) as src:
        window = window_for(src, bounds)
        values = np.nan_to_num(src.read(1, window=window, masked=True).astype(np.float64).filled(0.0), nan=0.0)
        transform = src.window_transform(window)
    rows, cols = np.nonzero(values > 0)
    lon, lat = xy(transform, rows, cols, offset="center")
    return np.asarray(lon, dtype=np.float64), np.asarray(lat, dtype=np.float64), values[rows, cols]


def read_cells(raster: str, districts: Sequence[BaseGeometry], totals: Sequence[int]) -> Cells:
    """Populated cells whose centre lies in a district, each district rescaled so its cells sum to its DOSM total."""
    lon, lat, values = read_populated(raster, shapely.union_all(list(districts)).bounds)
    district = np.full(len(values), -1)
    for i, geom in enumerate(districts):
        district[(district == -1) & shapely.contains_xy(geom, lon, lat)] = i
    keep = district >= 0
    lon, lat, values, district = lon[keep], lat[keep], values[keep], district[keep]
    people = np.zeros(len(values))
    for i, total in enumerate(totals):
        mask = district == i
        if not mask.any():
            raise ValueError(f"{DISTRICTS[i].name} has no populated cells in {raster}")
        people[mask] = values[mask] * (total / values[mask].sum())
    return Cells(lon=lon, lat=lat, people=people, district=district)
