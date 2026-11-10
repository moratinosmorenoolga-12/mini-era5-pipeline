"""Genera datos SINTÉTICOS con la misma estructura que una descarga de ERA5.

Sirve para probar el pipeline y el dashboard sin red ni clave del CDS (por
ejemplo en GitHub Actions). Imita lo esencial: rejilla de 0,25°, Kelvin,
metros, dos NetCDF (instant y accum) dentro de un ZIP, coordenadas number y
expver. Los valores son inventados pero plausibles: el mar templa, los
Pirineos enfrían, hay ciclo diario y un par de episodios de lluvia.

¡No usar para sacar conclusiones! El dashboard muestra un aviso.
"""
from __future__ import annotations

import calendar
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


def _land_mask(lat2, lon2):
    coast_lon = np.interp(lat2, [39.0, 40.5, 41.0, 41.4, 42.0, 42.4, 43.4], [-0.2, 0.7, 1.0, 2.3, 3.2, 3.2, 3.1])
    land = (lon2 < coast_lon) | (lat2 > 43.4)
    mallorca = ((lat2 - 39.62) / 0.28) ** 2 + ((lon2 - 2.95) / 0.45) ** 2 < 1
    return land | mallorca


def _elevation_km(lat2, lon2):
    pyrenees = 1.6 * np.exp(-((lat2 - 42.65) / 0.3) ** 2) * ((lon2 > -2) & (lon2 < 3.0))
    iberico = 1.1 * np.exp(-((lat2 - 40.6) ** 2 + (lon2 + 1.2) ** 2) / 0.5)
    ebro = -0.25 * np.exp(-((lat2 - 41.6) ** 2 / 0.2 + (lon2 - 0.0) ** 2 / 2.0))
    return np.clip(pyrenees + iberico + 0.35 + ebro, 0, None)


def make_month(year=2023, month=1, area=(44, -2, 39, 5), hours=range(24), seed=0):
    n, w, s, e = area
    lat = np.arange(n, s - 0.001, -0.25)
    lon = np.arange(w, e + 0.001, 0.25)
    days = calendar.monthrange(year, month)[1]
    times = pd.date_range(f"{year}-{month:02d}-01", periods=days * 24, freq="1h")
    times = times[np.isin(times.hour, list(hours))]
    rng = np.random.default_rng(seed + year * 100 + month)

    lat2, lon2 = np.meshgrid(lat, lon, indexing="ij")
    land = _land_mask(lat2, lon2)
    elev = np.where(land, _elevation_km(lat2, lon2), 0.0)

    nt = len(times)
    tday = np.arange(nt)
    # anomalía sinóptica (ola de frío a mitad de mes) + ruido lento
    frac = (times.day.values - 1 + times.hour.values / 24) / days
    synoptic = -5 * np.exp(-((frac - 0.5) / 0.08) ** 2) + np.cumsum(rng.normal(0, 0.25, nt))
    synoptic -= synoptic.mean()
    diurnal = np.cos(2 * np.pi * (times.hour.values - 14) / 24)

    coast_lon = np.interp(lat2, [39.0, 40.5, 41.0, 41.4, 42.0, 42.4, 43.4],
                          [-0.2, 0.7, 1.0, 2.3, 3.2, 3.2, 3.1])
    maritime = 3.0 * np.exp(-np.clip(coast_lon - lon2, 0, None) / 0.4)
    base = np.where(land, 6.5 + maritime - 6.5 * elev - 0.6 * (lat2 - 41), 13.5 - 0.4 * (lat2 - 41))
    amp = np.where(land, 4.5 - 0.8 * maritime, 0.6)
    t_c = (base[None] + amp[None] * diurnal[:, None, None]
           + np.where(land, 1.0, 0.4)[None] * synoptic[:, None, None]
           + rng.normal(0, 0.4, (nt, *lat2.shape)))

    # viento: régimen de mistral/cierzo (NO) que se refuerza en la ola de frío
    strength = 3 + 6 * np.exp(-((frac - 0.5) / 0.1) ** 2) + 1.5 * np.sin(tday / 17)
    u = strength[:, None, None] * 0.8 * np.where(land, 0.6, 1.2)[None]
    v = -strength[:, None, None] * 0.6 * np.where(land, 0.6, 1.2)[None]
    rot = 1.2 * np.sin(tday / 29)[:, None, None]  # giros lentos del viento
    u, v = u * np.cos(rot) - v * np.sin(rot), u * np.sin(rot) + v * np.cos(rot)
    u = u + rng.normal(0, 1.2, u.shape)
    v = v + rng.normal(0, 1.2, v.shape)

    # lluvia: tres episodios, más intensos en el litoral y el Pirineo
    tp = np.zeros_like(t_c)
    for centre, width, inten in [(0.15, 0.03, 0.3), (0.62, 0.04, 0.5), (0.85, 0.02, 0.25)]:
        pulse = np.exp(-((frac - centre) / width) ** 2)
        geo = 0.5 + elev + 1.2 * np.exp(-((lon2 - 2.4) ** 2) / 0.6)
        field = inten * pulse[:, None, None] * geo[None] * rng.gamma(0.6, 1.0, t_c.shape)
        tp += field
    tp_m = (tp / 1000.0).astype("float32")

    coords = {"valid_time": times, "latitude": lat, "longitude": lon}
    expver = xr.DataArray(np.full(nt, "0001"), dims="valid_time")
    attrs = {"synthetic_demo": "true", "source": "era5qc.demo (datos inventados)"}
    inst = xr.Dataset(
        {"t2m": (("valid_time", "latitude", "longitude"), (t_c + 273.15).astype("float32"), {"units": "K"}),
         "u10": (("valid_time", "latitude", "longitude"), u.astype("float32"), {"units": "m s**-1"}),
         "v10": (("valid_time", "latitude", "longitude"), v.astype("float32"), {"units": "m s**-1"})},
        coords=coords, attrs=attrs).assign_coords(number=0, expver=expver)
    accum = xr.Dataset(
        {"tp": (("valid_time", "latitude", "longitude"), tp_m, {"units": "m"})},
        coords=coords, attrs=attrs).assign_coords(number=0, expver=expver)
    return inst, accum


def write_demo_downloads(cfg: dict) -> list[Path]:
    """Escribe un ZIP por mes, con el mismo nombre que usaría fetch.py."""
    from era5qc.fetch import target_path

    raw = Path(cfg["paths"]["raw"])
    raw.mkdir(parents=True, exist_ok=True)
    hours_cfg = cfg["period"].get("hours", "all")
    hours = range(24) if hours_cfg == "all" else [int(h[:2]) for h in hours_cfg]
    paths = []
    for y in cfg["period"]["years"]:
        for m in cfg["period"]["months"]:
            inst, accum = make_month(y, m, tuple(cfg["region"]["area"]), hours)
            target = target_path(raw, y, m)
            tmp = raw / f"_tmp_{y}_{m:02d}"
            tmp.mkdir(exist_ok=True)
            fi = tmp / "data_stream-oper_stepType-instant.nc"
            fa = tmp / "data_stream-oper_stepType-accum.nc"
            inst.to_netcdf(fi)
            accum.to_netcdf(fa)
            with zipfile.ZipFile(target, "w") as zf:
                zf.write(fi, fi.name)
                zf.write(fa, fa.name)
            fi.unlink(); fa.unlink(); tmp.rmdir()
            paths.append(target)
    return paths
