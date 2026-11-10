"""Pipeline completo: descarga -> calidad -> análisis -> dashboard.

Uso (desde la raíz del proyecto, con .venv activado):

    python -m era5qc.pipeline                      # todo, según config/pipeline.yaml
    python -m era5qc.pipeline --skip-download      # reutiliza lo ya descargado
    python -m era5qc.pipeline --demo               # datos sintéticos, sin red

Salidas en outputs/:
    dashboard.html   el panel interactivo (doble clic para abrirlo)
    summary.json     todos los resultados en un formato legible por programas
    daily.csv        serie diaria de la zona
    points.csv       resumen por punto de interés
    qc.csv           resultado de cada control de calidad

Código de salida: 0 si todo bien, 1 si algún control de calidad da FAIL
(igual que quality.py, para que GitHub Actions lo detecte).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

from era5qc import analysis as an
from era5qc.dashboard import build_bundle, write_dashboard
from era5qc.fetch import download_period, target_path
from era5qc.io import open_era5
from era5qc.qc_bridge import has_fail, run_quality


def load_config(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(cfg: dict, skip_download=False, demo=False, log=print) -> int:
    if demo:
        # Los datos sintéticos van a su propia carpeta (data/demo) para que
        # nunca se confundan con una descarga real.
        raw = Path(cfg["paths"]["raw"])
        cfg = {**cfg, "paths": {**cfg["paths"], "raw": str(raw.parent / "demo")}}
    out = Path(cfg["paths"]["outputs"])
    out.mkdir(parents=True, exist_ok=True)

    # 1. Descarga ---------------------------------------------------------
    if demo:
        from era5qc.demo import write_demo_downloads

        log("[1/4] Generando datos SINTÉTICOS de demostración")
        paths = write_demo_downloads(cfg)
    elif skip_download:
        log("[1/4] Descarga omitida: se usan los archivos de " + cfg["paths"]["raw"])
        paths = [target_path(cfg["paths"]["raw"], y, m)
                 for y in cfg["period"]["years"] for m in cfg["period"]["months"]]
        missing = [p for p in paths if not p.exists()]
        if missing:
            log(f"ERROR: faltan {', '.join(p.name for p in missing)}. Quita --skip-download.")
            return 2
    else:
        log("[1/4] Descargando del CDS")
        paths = download_period(cfg)

    ds = open_era5(paths)
    if not demo and str(ds.attrs.get("synthetic_demo", "")).lower() == "true":
        log("ERROR: los archivos de " + cfg["paths"]["raw"] + " son datos SINTÉTICOS de la demo.")
        log("       Bórralos (rm -r " + cfg["paths"]["raw"] + ") y vuelve a ejecutar para descargar los reales.")
        return 2
    log(f"      {ds.sizes['valid_time']} instantes, rejilla "
        f"{ds.sizes['latitude']}×{ds.sizes['longitude']}, variables {list(ds.data_vars)}")

    # 2. Calidad (sobre los datos SIN transformar) -------------------------
    log("[2/4] Control de calidad")
    qc, source = run_quality(ds)
    for r in qc:
        log(f"      {r['status']:<4} {r['name']}: {r['detail']}")
    pd.DataFrame(qc).to_csv(out / "qc.csv", index=False)
    failed = has_fail(qc)
    if failed and cfg.get("qc", {}).get("stop_on_fail", True):
        log("ERROR: hay controles en FAIL; no se analizan datos defectuosos.")
        return 1

    # 3. Análisis ---------------------------------------------------------
    log("[3/4] Análisis")
    dsp = an.to_physical(ds)
    an.daily_table(dsp, ds).round(3).to_csv(out / "daily.csv")
    an.point_table(dsp, ds, cfg["points"]).round(3).to_csv(out / "points.csv")
    bundle = build_bundle(ds, dsp, cfg, qc, source)
    summary = {k: bundle[k] for k in ("meta", "qc", "kpis")}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    if not an.precip_is_complete(ds):
        log("      AVISO: datos no horarios; la precipitación total es una estimación")

    # 4. Dashboard --------------------------------------------------------
    offline = cfg.get("dashboard", {}).get("offline", True)
    html = write_dashboard(bundle, out / "dashboard.html", offline=offline)
    log(f"[4/4] Dashboard listo: {html}")
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pipeline ERA5: descarga, calidad, análisis y dashboard")
    ap.add_argument("--config", default="config/pipeline.yaml")
    ap.add_argument("--skip-download", action="store_true", help="usar las descargas existentes")
    ap.add_argument("--demo", action="store_true", help="datos sintéticos, sin red ni clave")
    args = ap.parse_args(argv)
    return run(load_config(args.config), skip_download=args.skip_download, demo=args.demo)


if __name__ == "__main__":
    sys.exit(main())
