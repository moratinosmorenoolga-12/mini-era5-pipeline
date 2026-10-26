"""Controles de calidad para datos ERA5 (NetCDF) con xarray."""
from __future__ import annotations

import glob
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xarray as xr

# Variables esperadas, sus unidades originales de ERA5 y rangos físicos plausibles.
EXPECTED_VARS = {
    "t2m": {"units": "K", "range": (220.0, 330.0)},         # -53 a 57 °C
    "u10": {"units": "m s**-1", "range": (-60.0, 60.0)},
    "v10": {"units": "m s**-1", "range": (-60.0, 60.0)},
    "tp": {"units": "m", "range": (-1e-6, 0.2)},            # m acumulados en 1 h
}


@dataclass
class CheckResult:
    name: str
    status: str  # "OK", "WARN" o "FAIL"
    detail: str


def load_era5(data_dir: str = "data") -> xr.Dataset:
    """Abre todos los .nc de una carpeta y los une en un solo Dataset."""
    files = sorted(glob.glob(f"{data_dir}/*.nc"))
    if not files:
        raise FileNotFoundError(f"No hay archivos .nc en {data_dir}")
    return xr.merge([xr.open_dataset(f) for f in files], compat="override")


def _time_name(ds: xr.Dataset) -> str:
    return "valid_time" if "valid_time" in ds.dims else "time"


def check_variables(ds: xr.Dataset) -> CheckResult:
    missing = [v for v in EXPECTED_VARS if v not in ds.data_vars]
    if missing:
        return CheckResult("variables", "FAIL", f"faltan: {missing}")
    return CheckResult("variables", "OK", f"presentes: {list(EXPECTED_VARS)}")


def check_nan(ds: xr.Dataset) -> list[CheckResult]:
    results = []
    for var in EXPECTED_VARS:
        if var not in ds.data_vars:
            continue
        n = int(ds[var].isnull().sum())
        status = "OK" if n == 0 else "FAIL"
        results.append(CheckResult(f"nan[{var}]", status, f"{n} de {ds[var].size} valores NaN"))
    return results


def check_ranges(ds: xr.Dataset) -> list[CheckResult]:
    results = []
    for var, spec in EXPECTED_VARS.items():
        if var not in ds.data_vars:
            continue
        lo, hi = spec["range"]
        vmin, vmax = float(ds[var].min()), float(ds[var].max())
        status = "OK" if (vmin >= lo and vmax <= hi) else "FAIL"
        results.append(
            CheckResult(f"rango[{var}]", status,
                        f"min={vmin:.4g}, max={vmax:.4g} (permitido {lo} a {hi})")
        )
    return results


def check_time_axis(ds: xr.Dataset, freq: str = "6h") -> CheckResult:
    t = pd.DatetimeIndex(ds[_time_name(ds)].values)
    dups = int(t.duplicated().sum())
    if not t.is_monotonic_increasing:
        return CheckResult("tiempo", "FAIL", "el eje temporal no está ordenado")
    expected = pd.date_range(t.min(), t.max(), freq=freq)
    missing = expected.difference(t)
    if dups or len(missing):
        return CheckResult("tiempo", "FAIL",
                           f"{dups} duplicados, {len(missing)} instantes faltantes")
    return CheckResult("tiempo", "OK", f"{len(t)} instantes, paso regular de {freq}")


def check_grid(ds: xr.Dataset, step: float = 0.25) -> CheckResult:
    for coord in ("latitude", "longitude"):
        diffs = np.abs(np.diff(ds[coord].values))
        if not np.allclose(diffs, step, atol=1e-6):
            return CheckResult("rejilla", "FAIL", f"{coord} no tiene paso regular de {step}°")
    return CheckResult("rejilla", "OK", f"paso regular de {step}°")


def check_units(ds: xr.Dataset) -> list[CheckResult]:
    results = []
    for var, spec in EXPECTED_VARS.items():
        if var not in ds.data_vars:
            continue
        units = ds[var].attrs.get("units")
        status = "OK" if units == spec["units"] else "WARN"
        results.append(CheckResult(f"unidades[{var}]", status,
                                   f"'{units}' (esperado '{spec['units']}')"))
    return results


def check_expver(ds: xr.Dataset) -> CheckResult:
    if "expver" not in ds.coords:
        return CheckResult("expver", "OK", "sin coordenada expver")
    values = sorted(set(np.unique(ds["expver"].values).tolist()))
    if values == ["0001"]:
        return CheckResult("expver", "OK", "ERA5 definitivo (0001)")
    return CheckResult("expver", "WARN", f"versiones {values}: posible ERA5T preliminar")


def run_all(ds: xr.Dataset) -> list[CheckResult]:
    results = [check_variables(ds)]
    results += check_nan(ds)
    results += check_ranges(ds)
    results += [check_time_axis(ds), check_grid(ds)]
    results += check_units(ds)
    results.append(check_expver(ds))
    return results


def main(data_dir: str = "data") -> int:
    ds = load_era5(data_dir)
    results = run_all(ds)
    for r in results:
        print(f"[{r.status:4}] {r.name:16} {r.detail}")
    n_fail = sum(r.status == "FAIL" for r in results)
    n_warn = sum(r.status == "WARN" for r in results)
    print(f"\nResumen: {len(results)} comprobaciones, {n_fail} FAIL, {n_warn} WARN")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
