"""Lectura de las descargas de ERA5.

Resuelve las dos «sorpresas» de la guía de forma automática:
  1. El archivo descargado puede ser un ZIP con varios NetCDF dentro.
  2. Dentro vienen separados instant (t2m, u10, v10) y accum (tp).
Además junta varios meses en un único Dataset ordenado por tiempo.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import xarray as xr


def unpack(path: Path) -> list[Path]:
    """Devuelve los .nc de una descarga, descomprimiéndola si es un ZIP."""
    path = Path(path)
    if path.is_dir():
        return sorted(path.glob("*.nc"))
    if zipfile.is_zipfile(path):
        outdir = path.with_suffix("")  # data/raw/era5_2023_01/
        if not outdir.exists():
            with zipfile.ZipFile(path) as zf:
                zf.extractall(outdir)
        return sorted(outdir.glob("*.nc"))
    return [path]  # ya era un NetCDF


def open_era5(paths) -> xr.Dataset:
    """Abre y combina todas las descargas en un Dataset (valid_time, lat, lon)."""
    nc_files: list[Path] = []
    for p in paths:
        nc_files.extend(unpack(p))
    if not nc_files:
        raise FileNotFoundError("No se ha encontrado ningún NetCDF en las descargas")

    # load() lee a memoria y permite cerrar el archivo (los datos son pequeños)
    parts = []
    for f in nc_files:
        with xr.open_dataset(f) as d:
            parts.append(d.load())

    # combine_by_coords coloca cada trozo según sus coordenadas: junta las
    # variables instant/accum y encadena los meses por valid_time.
    ds = xr.combine_by_coords(parts, combine_attrs="override", join="outer",
                            compat="no_conflicts")
    ds = ds.sortby("valid_time")
    if "latitude" in ds.dims:
        ds = ds.sortby("latitude", ascending=False)
    return ds
