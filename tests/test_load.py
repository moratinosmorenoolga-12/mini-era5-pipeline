import numpy as np
import pandas as pd
import pytest
import xarray as xr

from era5qc import quality


def make_month(start, n_time=8):
    """Mes sintetico: devuelve (instant, accum) como los dos .nc reales del CDS."""
    time = pd.date_range(start, periods=n_time, freq="6h")
    lat = np.arange(44.0, 44.0 - 5 * 0.25, -0.25)
    lon = np.arange(-2.0, -2.0 + 6 * 0.25, 0.25)
    shape = (n_time, len(lat), len(lon))
    dims = ("valid_time", "latitude", "longitude")
    units = {"t2m": "K", "u10": "m s**-1", "v10": "m s**-1", "tp": "m"}
    values = {"t2m": 280.0, "u10": 2.0, "v10": -1.0, "tp": 0.0005}

    def var(name):
        return (dims, np.full(shape, values[name], dtype="float32"),
                {"units": units[name]})

    coords = {
        "valid_time": time,
        "latitude": lat,
        "longitude": lon,
        "expver": ("valid_time", ["0001"] * n_time),
        "number": 0,
    }
    instant = xr.Dataset({v: var(v) for v in ("t2m", "u10", "v10")}, coords=coords)
    accum = xr.Dataset({"tp": var("tp")}, coords=coords)
    return instant, accum


def write_month(root, name, start, n_time=8):
    folder = root / name
    folder.mkdir(parents=True)
    instant, accum = make_month(start, n_time)
    instant.to_netcdf(folder / "data_stream-oper_stepType-instant.nc")
    accum.to_netcdf(folder / "data_stream-oper_stepType-accum.nc")


def test_un_mes_con_dos_archivos(tmp_path):
    write_month(tmp_path, "2023-01", "2023-01-01")
    ds = quality.load_era5(str(tmp_path))
    assert set(ds.data_vars) == {"t2m", "u10", "v10", "tp"}
    assert ds.sizes["valid_time"] == 8


def test_varios_meses_se_unen_en_orden(tmp_path):
    # Se crean desordenados a proposito: 2023-02 antes que 2023-01.
    write_month(tmp_path, "2023-02", "2023-01-03")
    write_month(tmp_path, "2023-01", "2023-01-01")
    ds = quality.load_era5(str(tmp_path))
    assert ds.sizes["valid_time"] == 16
    assert quality.check_time_axis(ds).status == "OK"


def test_mes_que_falta_se_detecta(tmp_path):
    write_month(tmp_path, "2023-01", "2023-01-01")
    write_month(tmp_path, "2023-03", "2023-01-10")  # hueco de varios dias
    ds = quality.load_era5(str(tmp_path))
    assert quality.check_time_axis(ds).status == "FAIL"


def test_carpeta_sin_archivos(tmp_path):
    with pytest.raises(FileNotFoundError):
        quality.load_era5(str(tmp_path))
