"""Conecta el pipeline con tu quality.py sin tener que reescribirlo.

Busca en era5qc.quality, por este orden:
  1. Una función que ejecute todos los controles: run_checks(ds),
     run_all_checks(ds), check_all(ds) o all_checks(ds).
  2. Si no la hay, cada función check_*(ds) por separado.
Cualquier resultado con atributos/claves name, status y detail vale
(tu CheckResult encaja). Si una función necesita otros argumentos, se omite.

Si tu quality.py usa otros nombres, solo tienes que añadirlos a RUNNERS.
"""
from __future__ import annotations

import inspect

import numpy as np
import xarray as xr

RUNNERS = ("run_checks", "run_all_checks", "check_all", "all_checks")


def _normalize(r) -> dict:
    if isinstance(r, dict):
        get = r.get
    elif isinstance(r, (tuple, list)) and len(r) >= 2:
        return {"name": str(r[0]), "status": str(r[1]).upper(),
                "detail": str(r[2]) if len(r) > 2 else ""}
    else:
        def get(k, default=""):
            return getattr(r, k, default)
    status = get("status", "")
    status = getattr(status, "name", status)  # por si es un Enum
    return {"name": str(get("name", "?")), "status": str(status).upper(),
            "detail": str(get("detail", ""))}


def _as_list(res):
    if res is None:
        return []
    if isinstance(res, (list, tuple)) and res and not isinstance(res[0], str):
        return list(res)
    return [res]


def basic_checks(ds: xr.Dataset) -> list[dict]:
    """Controles mínimos de reserva por si quality.py no se puede usar."""
    out = []
    for v in ("t2m", "u10", "v10", "tp"):
        if v not in ds:
            out.append({"name": f"variables:{v}", "status": "FAIL", "detail": "falta"})
            continue
        n = int(np.isnan(ds[v].values).sum())
        out.append({"name": f"nan:{v}", "status": "OK" if n == 0 else "WARN",
                    "detail": f"{n} valores perdidos"})
    return out


def run_quality(ds: xr.Dataset) -> tuple[list[dict], str]:
    """Devuelve (resultados, origen)."""
    try:
        from era5qc import quality
    except ImportError:
        return basic_checks(ds), "QC básico (no se encontró era5qc.quality)"

    for name in RUNNERS:
        fn = getattr(quality, name, None)
        if callable(fn):
            try:
                return [_normalize(r) for r in _as_list(fn(ds))], f"quality.{name}"
            except TypeError:
                pass

    results = []
    for name, fn in inspect.getmembers(quality, inspect.isfunction):
        if not name.startswith("check_") or fn.__module__ != quality.__name__:
            continue
        try:
            results.extend(_normalize(r) for r in _as_list(fn(ds)))
        except TypeError:
            continue  # necesita otros argumentos: se omite
    if results:
        return results, "quality.check_*"
    return basic_checks(ds), "QC básico (quality.py no expone funciones compatibles)"


def has_fail(results: list[dict]) -> bool:
    return any(r["status"] == "FAIL" for r in results)
