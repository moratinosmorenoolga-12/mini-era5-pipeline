"""Genera outputs/dashboard.html: un único archivo que se abre con doble clic.

El análisis se hace en Python (analysis.py); aquí solo se empaquetan los
resultados como JSON dentro de una plantilla HTML con gráficos Plotly.
Con offline: true se incrusta plotly.js y el panel funciona sin internet.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from era5qc import analysis as an
from era5qc._template import TEMPLATE


def _r(x, nd=2):
    """Redondea y cambia NaN por None (JSON no admite NaN)."""
    if isinstance(x, (list, tuple, np.ndarray)):
        return [_r(v, nd) for v in np.asarray(x).tolist()]
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return round(float(x), nd)


def build_bundle(ds_raw, dsp, cfg, qc_results, qc_source) -> dict:
    times = pd.to_datetime(dsp["valid_time"].values)
    complete = an.precip_is_complete(ds_raw)
    step = an.time_step_hours(ds_raw)
    factor = 1.0 if complete else step
    daily = an.daily_table(dsp, ds_raw)
    pts = an.point_table(dsp, ds_raw, cfg["points"])
    ext = an.extremes(dsp)
    mp = an.maps(dsp, ds_raw)

    area_t = an.area_mean(dsp["t2m_c"])
    points = {}
    for name, (lat, lon) in cfg["points"].items():
        c = dsp.sel(latitude=lat, longitude=lon, method="nearest")
        t = c["t2m_c"].to_series()
        p = c["tp_mm"].to_series()
        rose = an.wind_rose(c["ws10"].values, c["wd10"].values)
        row = pts.loc[name]
        points[name] = {
            "lat": float(row.lat_celda), "lon": float(row.lon_celda),
            "summary": {k: (_r(v) if not isinstance(v, str) else v)
                        for k, v in row.items()},
            "t": _r(t.values, 1),
            "ws": _r(c["ws10"].values, 1),
            "daily": {
                "precip": _r(p.resample("1D").sum().values * factor, 2),
                "t_min": _r(t.resample("1D").min().values, 1),
                "t_max": _r(t.resample("1D").max().values, 1),
            },
            "diurnal": _r(an.diurnal_cycle(c["t2m_c"]).values, 2),
            "rose": {"sectors": list(rose.index), "bins": [str(b) for b in rose.columns],
                     "values": [_r(rose[b].values, 2) for b in rose.columns]},
        }

    diur = an.diurnal_cycle(area_t)
    synthetic = str(ds_raw.attrs.get("synthetic_demo", "")).lower() == "true"
    return {
        "meta": {
            "title": cfg.get("dashboard", {}).get("title", "Panel climático ERA5"),
            "region": cfg["region"]["name"],
            "area": cfg["region"]["area"],
            "start": times[0].isoformat(), "end": times[-1].isoformat(),
            "step_h": step, "n_times": len(times),
            "grid": [int(dsp.sizes["latitude"]), int(dsp.sizes["longitude"])],
            "precip_complete": complete, "synthetic": synthetic,
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        },
        "qc": {"source": qc_source, "results": qc_results},
        "kpis": {
            "t_media_area": _r(float(area_t.mean()), 1),
            "precip_media_area": _r(float(an.area_mean(mp["precip_total"])), 1),
            "viento_medio_area": _r(float(an.area_mean(mp["viento_medio"])), 1),
            "extremes": {k: {**v, "valor": _r(v["valor"], 2)} for k, v in ext.items()},
        },
        "grid": {"lat": _r(dsp["latitude"].values, 2), "lon": _r(dsp["longitude"].values, 2)},
        "maps": {k: [_r(row, 2) for row in v.transpose("latitude", "longitude").values]
                 for k, v in mp.items()},
        "time": [t.strftime("%Y-%m-%dT%H:%M") for t in times],
        "days": [d.strftime("%Y-%m-%d") for d in daily.index],
        "area": {
            "t_media": _r(daily["t_media_c"].values, 1),
            "precip": _r(daily["precip_mm"].values, 2),
            "viento": _r(daily["viento_medio_ms"].values, 1),
            "diurnal_hours": [int(h) for h in diur.index],
            "diurnal": _r(diur.values, 2),
        },
        "points": points,
    }


def _plotly_js(offline: bool) -> str:
    if offline:
        import plotly

        js = (Path(plotly.__file__).parent / "package_data" / "plotly.min.js").read_text()
        return f"<script>{js}</script>"
    return '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'


def write_dashboard(bundle: dict, path: Path, offline: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE.replace("__TITLE__", bundle["meta"]["title"])
            .replace("__PLOTLY__", _plotly_js(offline))
            .replace("__DATA__", data))
    path.write_text(html, encoding="utf-8")
    return path
