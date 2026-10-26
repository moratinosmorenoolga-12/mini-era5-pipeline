import numpy as np
import pandas as pd
import pytest
import xarray as xr

from era5qc import quality


def make_ds(n_time=8):
    """Dataset ERA5 sintético y sano: 8 instantes de 6 h, rejilla 5x6 de 0,25°."""
    time = pd.date_range("2023-01-01", periods=n_time, freq="6h")
    lat = np.arange(44.0, 44.0 - 5 * 0.25, -0.25)
    lon = np.arange(-2.0, -2.0 + 6 * 0.25, 0.25)
    shape = (n_time, len(lat), len(lon))
    units = {"t2m": "K", "u10": "m s**-1", "v10": "m s**-1", "tp": "m"}
    values = {"t2m": 280.0, "u10": 2.0, "v10": -1.0, "tp": 0.0005}
    data_vars = {
        v: (("valid_time", "latitude", "longitude"),
            np.full(shape, values[v], dtype="float32"),
            {"units": units[v]})
        for v in units
    }
    return xr.Dataset(
        data_vars,
        coords={
            "valid_time": time,
            "latitude": lat,
            "longitude": lon,
            "expver": ("valid_time", ["0001"] * n_time),
        },
    )


def status(results, name):
    """Estado del resultado cuyo nombre es `name` (acepta un resultado o una lista)."""
    if isinstance(results, quality.CheckResult):
        results = [results]
    return next(r.status for r in results if r.name == name)


def test_dataset_sano_pasa_todo():
    results = quality.run_all(make_ds())
    assert all(r.status == "OK" for r in results)


def test_variable_ausente_falla():
    ds = make_ds().drop_vars("tp")
    assert quality.check_variables(ds).status == "FAIL"


def test_nan_detectado():
    ds = make_ds()
    ds["t2m"][0, 0, 0] = np.nan
    assert status(quality.check_nan(ds), "nan[t2m]") == "FAIL"


def test_temperatura_fuera_de_rango():
    ds = make_ds()
    ds["t2m"][0, 0, 0] = 400.0
    assert status(quality.check_ranges(ds), "rango[t2m]") == "FAIL"


def test_precipitacion_negativa():
    ds = make_ds()
    ds["tp"][0, 0, 0] = -0.01
    assert status(quality.check_ranges(ds), "rango[tp]") == "FAIL"


def test_instante_faltante():
    ds = make_ds().isel(valid_time=[0, 1, 2, 4, 5, 6, 7])  # falta el 3
    assert quality.check_time_axis(ds).status == "FAIL"


def test_tiempo_duplicado():
    ds = make_ds()
    ds = xr.concat([ds, ds.isel(valid_time=[0])], dim="valid_time")
    assert quality.check_time_axis(ds).status == "FAIL"


def test_rejilla_irregular():
    ds = make_ds()
    lat = ds["latitude"].values.copy()
    lat[2] += 0.1
    ds = ds.assign_coords(latitude=lat)
    assert quality.check_grid(ds).status == "FAIL"


def test_unidades_incorrectas_dan_warn():
    ds = make_ds()
    ds["t2m"].attrs["units"] = "degC"
    assert status(quality.check_units(ds), "unidades[t2m]") == "WARN"


def test_expver_preliminar_da_warn():
    ds = make_ds()
    ds = ds.assign_coords(expver=("valid_time", ["0001"] * 7 + ["0005"]))
    assert quality.check_expver(ds).status == "WARN"
