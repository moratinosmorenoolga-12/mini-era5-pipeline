"""Análisis de los datos ERA5: de valores «crudos» a magnitudes interpretables.

Todo son funciones pequeñas y puras (entra un Dataset, sale un resultado), así
que se pueden testear sin red ni archivos, igual que quality.py.

Conversiones clave:
  t2m  K   -> °C       (restar 273,15)
  tp   m   -> mm       (multiplicar por 1000). En ERA5 horario cada valor es
                        lo acumulado en la hora que termina en valid_time.
  u10, v10 -> velocidad del viento (m/s) y dirección de la que sopla (grados).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

COMPASS_16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]


# --------------------------------------------------------------------------
# Conversiones
# --------------------------------------------------------------------------
def wind_speed(u, v):
    return np.hypot(u, v)


def wind_direction(u, v):
    """Dirección meteorológica: de DÓNDE viene el viento (0 = norte, 90 = este).

    u > 0 sopla hacia el este, así que viene del oeste (270°).
    v < 0 sopla hacia el sur, así que viene del norte (0°).
    """
    return (270.0 - np.degrees(np.arctan2(v, u))) % 360.0


def compass(deg: float) -> str:
    return COMPASS_16[int(((deg % 360) + 11.25) // 22.5) % 16]


def to_physical(ds: xr.Dataset) -> xr.Dataset:
    """Añade variables en unidades «humanas». No modifica las originales."""
    out = ds.copy()
    out["t2m_c"] = ds["t2m"] - 273.15
    out["t2m_c"].attrs = {"units": "°C", "long_name": "Temperatura a 2 m"}
    out["tp_mm"] = (ds["tp"] * 1000.0).clip(min=0)  # quita ruido negativo diminuto
    out["tp_mm"].attrs = {"units": "mm", "long_name": "Precipitación"}
    out["ws10"] = wind_speed(ds["u10"], ds["v10"])
    out["ws10"].attrs = {"units": "m/s", "long_name": "Velocidad del viento a 10 m"}
    out["wd10"] = wind_direction(ds["u10"], ds["v10"])
    out["wd10"].attrs = {"units": "°", "long_name": "Dirección del viento (procedencia)"}
    return out


# --------------------------------------------------------------------------
# Utilidades espaciales y temporales
# --------------------------------------------------------------------------
def time_step_hours(ds: xr.Dataset) -> float:
    t = pd.to_datetime(ds["valid_time"].values)
    if len(t) < 2:
        return float("nan")
    return float(pd.Series(t).diff().dropna().dt.total_seconds().median() / 3600)


def area_mean(da: xr.DataArray) -> xr.DataArray:
    """Media espacial ponderada por cos(latitud).

    En una rejilla lat/lon las celdas cercanas al polo son más pequeñas; sin
    pesos, el norte de la zona contaría un poco más de lo que le toca.
    """
    w = np.cos(np.deg2rad(da["latitude"]))
    return da.weighted(w).mean(("latitude", "longitude"))


def nearest_cell(ds: xr.Dataset, lat: float, lon: float) -> dict:
    cell = ds.sel(latitude=lat, longitude=lon, method="nearest")
    return {"lat": float(cell["latitude"]), "lon": float(cell["longitude"])}


def precip_is_complete(ds: xr.Dataset) -> bool:
    """Solo con datos horarios la suma de tp es el total real del periodo."""
    return abs(time_step_hours(ds) - 1.0) < 1e-6


def precip_total(tp_mm: xr.DataArray, ds: xr.Dataset) -> xr.DataArray:
    """Total de precipitación a lo largo del tiempo.

    Con datos cada N horas solo vemos 1 de cada N horas: se estima el total
    como suma × N (y el dashboard lo marca como «estimación»).
    """
    step = time_step_hours(ds)
    factor = 1.0 if precip_is_complete(ds) else step
    return tp_mm.sum("valid_time") * factor


# --------------------------------------------------------------------------
# Productos del análisis
# --------------------------------------------------------------------------
def daily_table(dsp: xr.Dataset, ds_raw: xr.Dataset) -> pd.DataFrame:
    """Serie diaria del promedio de la zona."""
    step = time_step_hours(ds_raw)
    factor = 1.0 if precip_is_complete(ds_raw) else step
    t = area_mean(dsp["t2m_c"]).to_series()
    p = area_mean(dsp["tp_mm"]).to_series()
    w = area_mean(dsp["ws10"]).to_series()
    df = pd.DataFrame({
        "t_min_c": t.resample("1D").min(),
        "t_media_c": t.resample("1D").mean(),
        "t_max_c": t.resample("1D").max(),
        "precip_mm": p.resample("1D").sum() * factor,
        "viento_medio_ms": w.resample("1D").mean(),
    })
    df.index.name = "fecha"
    return df


def point_table(dsp: xr.Dataset, ds_raw: xr.Dataset, points: dict) -> pd.DataFrame:
    """Resumen por punto de interés (celda más cercana)."""
    rows = []
    for name, (lat, lon) in points.items():
        c = dsp.sel(latitude=lat, longitude=lon, method="nearest")
        t = c["t2m_c"]
        rows.append({
            "punto": name,
            "lat_celda": float(c["latitude"]),
            "lon_celda": float(c["longitude"]),
            "t_media_c": float(t.mean()),
            "t_min_c": float(t.min()),
            "t_max_c": float(t.max()),
            "precip_total_mm": float(precip_total(c["tp_mm"], ds_raw)),
            "viento_medio_ms": float(c["ws10"].mean()),
            "viento_max_ms": float(c["ws10"].max()),
            "dir_dominante": compass(dominant_direction(c["wd10"].values)),
        })
    return pd.DataFrame(rows).set_index("punto")


def dominant_direction(wd: np.ndarray) -> float:
    """Sector de 22,5° del que más veces sopla el viento."""
    sectors = (((np.asarray(wd) % 360) + 11.25) // 22.5).astype(int) % 16
    return float(np.bincount(sectors.ravel(), minlength=16).argmax() * 22.5)


def wind_rose(ws: np.ndarray, wd: np.ndarray,
              speed_bins=(0, 2, 4, 6, 8, 10, np.inf)) -> pd.DataFrame:
    """Frecuencia (%) por dirección (16 sectores) y franja de velocidad."""
    ws, wd = np.asarray(ws).ravel(), np.asarray(wd).ravel()
    sectors = (((wd % 360) + 11.25) // 22.5).astype(int) % 16
    labels = [f"{a:g}–{b:g}" if np.isfinite(b) else f"≥{a:g}"
              for a, b in zip(speed_bins[:-1], speed_bins[1:])]
    speed_cls = pd.cut(ws, bins=list(speed_bins), labels=labels, right=False)
    table = pd.crosstab(pd.Categorical(sectors, categories=range(16)), speed_cls,
                        dropna=False)
    table.index = COMPASS_16
    return table / max(len(ws), 1) * 100


def diurnal_cycle(da: xr.DataArray) -> pd.Series:
    """Media por hora UTC: cómo cambia una variable a lo largo del día."""
    s = da.to_series()
    return s.groupby(s.index.hour).mean()


def extremes(dsp: xr.Dataset) -> dict:
    """Valor, fecha y lugar de los extremos de toda la zona y el periodo."""
    def where(da, fn):
        idx = getattr(da, fn)(...)  # argmin/argmax sobre todas las dimensiones
        sel = da.isel(idx)
        return {
            "valor": float(sel),
            "fecha": pd.Timestamp(sel["valid_time"].values).isoformat(),
            "lat": float(sel["latitude"]),
            "lon": float(sel["longitude"]),
        }
    return {
        "t_min": where(dsp["t2m_c"], "argmin"),
        "t_max": where(dsp["t2m_c"], "argmax"),
        "viento_max": where(dsp["ws10"], "argmax"),
        "precip_max_hora": where(dsp["tp_mm"], "argmax"),
    }


def maps(dsp: xr.Dataset, ds_raw: xr.Dataset) -> dict[str, xr.DataArray]:
    return {
        "t_media": dsp["t2m_c"].mean("valid_time"),
        "precip_total": precip_total(dsp["tp_mm"], ds_raw),
        "viento_medio": dsp["ws10"].mean("valid_time"),
        "viento_max": dsp["ws10"].max("valid_time"),
    }
