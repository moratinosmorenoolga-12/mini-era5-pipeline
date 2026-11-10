"""Tests de la fase 8. Como en test_quality.py: datos fabricados, sin red."""
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from era5qc import analysis as an
from era5qc.demo import make_month
from era5qc.fetch import build_request


def tiny_ds(hours=24, days=2):
    """Mini-ERA5 con valores conocidos: 10 °C, viento del oeste a 4 m/s, 1 mm/h."""
    t = pd.date_range("2023-01-01", periods=days * 24, freq="1h")
    t = t[t.hour % (24 // hours) == 0] if hours < 24 else t
    lat, lon = np.array([42.0, 41.75, 41.5]), np.array([1.0, 1.25])
    shape = (len(t), 3, 2)
    return xr.Dataset(
        {"t2m": (("valid_time", "latitude", "longitude"), np.full(shape, 283.15)),
         "u10": (("valid_time", "latitude", "longitude"), np.full(shape, 4.0)),
         "v10": (("valid_time", "latitude", "longitude"), np.zeros(shape)),
         "tp": (("valid_time", "latitude", "longitude"), np.full(shape, 0.001))},
        coords={"valid_time": t, "latitude": lat, "longitude": lon})


# --- conversiones ---------------------------------------------------------
@pytest.mark.parametrize("u,v,esperado", [
    (0, -5, 0),     # sopla hacia el sur -> viene del norte
    (-5, 0, 90),    # hacia el oeste -> del este
    (0, 5, 180),    # hacia el norte -> del sur
    (5, 0, 270),    # hacia el este -> del oeste
])
def test_direccion_viento(u, v, esperado):
    assert an.wind_direction(u, v) == pytest.approx(esperado)


def test_velocidad_viento():
    assert an.wind_speed(3.0, 4.0) == pytest.approx(5.0)


def test_brujula():
    assert an.compass(0) == "N" and an.compass(350) == "N"
    assert an.compass(225) == "SO" and an.compass(270) == "O"


def test_conversion_unidades():
    dsp = an.to_physical(tiny_ds())
    assert float(dsp["t2m_c"].mean()) == pytest.approx(10.0)
    assert float(dsp["tp_mm"].mean()) == pytest.approx(1.0)
    assert float(dsp["wd10"].mean()) == pytest.approx(270.0)


def test_precip_negativa_se_anula():
    ds = tiny_ds()
    ds["tp"][:] = -1e-9  # ruido numérico típico de ERA5
    assert float(an.to_physical(ds)["tp_mm"].min()) == 0.0


# --- precipitación: horaria frente a cada 6 h -----------------------------
def test_precip_diaria_horaria_es_total_real():
    ds = tiny_ds(hours=24)
    daily = an.daily_table(an.to_physical(ds), ds)
    assert an.precip_is_complete(ds)
    assert daily["precip_mm"].tolist() == pytest.approx([24.0, 24.0])


def test_precip_diaria_6h_se_estima():
    ds = tiny_ds(hours=4)  # 00, 06, 12, 18
    daily = an.daily_table(an.to_physical(ds), ds)
    assert not an.precip_is_complete(ds)
    assert daily["precip_mm"].tolist() == pytest.approx([24.0, 24.0])  # 4 valores × 6


# --- espacio --------------------------------------------------------------
def test_media_ponderada_por_latitud():
    ds = tiny_ds()
    da = ds["t2m"].isel(valid_time=0).copy()
    da[0, :] = 300.0  # la fila más al norte (celdas más pequeñas)
    simple = float(da.mean())
    ponderada = float(an.area_mean(da))
    assert ponderada < simple  # el norte pesa algo menos


def test_rosa_suma_100():
    rng = np.random.default_rng(1)
    rose = an.wind_rose(rng.uniform(0, 15, 500), rng.uniform(0, 360, 500))
    assert rose.values.sum() == pytest.approx(100.0)
    assert list(rose.index)[:4] == ["N", "NNE", "NE", "ENE"]


def test_extremos_localiza_maximo():
    ds = tiny_ds()
    ds["t2m"][5, 2, 1] = 300.0
    ext = an.extremes(an.to_physical(ds))
    assert ext["t_max"]["valor"] == pytest.approx(26.85)
    assert (ext["t_max"]["lat"], ext["t_max"]["lon"]) == (41.5, 1.25)


# --- descarga sin red -----------------------------------------------------
def test_peticion_mes_completo():
    cfg = {"period": {"hours": "all"}, "variables": ["2m_temperature"],
           "region": {"area": [44, -2, 39, 5]}}
    req = build_request(cfg, 2024, 2)
    assert len(req["day"]) == 29          # 2024 es bisiesto
    assert len(req["time"]) == 24
    assert req["month"] == "02"


# --- de extremo a extremo con datos sintéticos -----------------------------
def test_pipeline_demo_completo(tmp_path):
    from era5qc.pipeline import run

    cfg = {
        "region": {"name": "Test", "area": [43, 0, 41, 2]},
        "period": {"years": [2023], "months": [1], "hours": ["00:00", "06:00", "12:00", "18:00"]},
        "variables": [],
        "points": {"A": [42.0, 1.0]},
        "paths": {"raw": str(tmp_path / "raw"), "outputs": str(tmp_path / "out")},
        "qc": {"stop_on_fail": True},
        "dashboard": {"offline": False},
    }
    code = run(cfg, demo=True, log=lambda *_: None)
    out = tmp_path / "out"
    assert code == 0, "QC en FAIL:\n" + (out / "qc.csv").read_text()
    for f in ("dashboard.html", "summary.json", "daily.csv", "points.csv", "qc.csv"):
        assert (out / f).exists(), f
    summary = json.loads((out / "summary.json").read_text())
    assert summary["meta"]["synthetic"] is True
    assert summary["meta"]["n_times"] == 124
    assert len(pd.read_csv(out / "daily.csv")) == 31


def test_demo_tiene_estructura_era5():
    inst, accum = make_month(2023, 1, hours=[0, 6, 12, 18])
    assert set(inst.data_vars) == {"t2m", "u10", "v10"}
    assert set(accum.data_vars) == {"tp"}
    assert inst.sizes == {"valid_time": 124, "latitude": 21, "longitude": 29}
    assert 220 < float(inst["t2m"].min()) and float(inst["t2m"].max()) < 330


def test_qc_bridge_entiende_checkresult():
    from dataclasses import dataclass

    from era5qc.qc_bridge import _normalize, has_fail

    @dataclass
    class CheckResult:
        name: str
        status: str
        detail: str

    r = [_normalize(CheckResult("nan", "fail", "3 NaN")), _normalize(("rango", "OK"))]
    assert r[0] == {"name": "nan", "status": "FAIL", "detail": "3 NaN"}
    assert r[1]["status"] == "OK"
    assert has_fail(r)
