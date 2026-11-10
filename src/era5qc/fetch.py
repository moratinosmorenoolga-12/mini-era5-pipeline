"""Descarga de ERA5 guiada por config/pipeline.yaml (fase 8).

Vive aparte de download.py para no interferir con tus funciones y tests.

Fase 8: la descarga ya no está fijada a enero de 2023. Lee el periodo, la zona
y las variables de config/pipeline.yaml y hace UNA petición por mes (el CDS
pone límites al tamaño de cada petición y así, si falla un mes, no se pierde
todo).

Si el archivo de un mes ya existe, no se vuelve a descargar (caché).
"""
from __future__ import annotations

import calendar
from pathlib import Path

DATASET = "reanalysis-era5-single-levels"
ALL_HOURS = [f"{h:02d}:00" for h in range(24)]


def build_request(cfg: dict, year: int, month: int) -> dict:
    """Construye la petición del CDS para un mes. Sin red: se puede testear."""
    hours = cfg["period"].get("hours", "all")
    times = ALL_HOURS if hours == "all" else list(hours)
    n_days = calendar.monthrange(year, month)[1]
    return {
        "product_type": "reanalysis",
        "variable": list(cfg["variables"]),
        "year": f"{year}",
        "month": f"{month:02d}",
        "day": [f"{d:02d}" for d in range(1, n_days + 1)],
        "time": times,
        "area": list(cfg["region"]["area"]),  # N, W, S, E
        "data_format": "netcdf",
    }


def target_path(raw_dir: Path, year: int, month: int) -> Path:
    # El CDS suele devolver un ZIP aunque pidas NetCDF (ver guía, sección 7),
    # así que guardamos como .download y io.py decide qué es.
    return Path(raw_dir) / f"era5_{year}_{month:02d}.download"


def download_period(cfg: dict, client=None, force: bool = False) -> list[Path]:
    """Descarga todos los meses de la configuración. Devuelve las rutas."""
    raw_dir = Path(cfg["paths"]["raw"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for year in cfg["period"]["years"]:
        for month in cfg["period"]["months"]:
            target = target_path(raw_dir, year, month)
            if target.exists() and not force:
                print(f"[descarga] {target.name} ya existe, se reutiliza")
            else:
                if client is None:
                    import cdsapi  # solo se importa si de verdad hay que descargar

                    client = cdsapi.Client()
                print(f"[descarga] pidiendo {year}-{month:02d} al CDS...")
                client.retrieve(DATASET, build_request(cfg, year, month), str(target))
            paths.append(target)
    return paths
