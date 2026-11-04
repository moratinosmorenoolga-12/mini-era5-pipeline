"""Descarga ERA5 mes a mes desde el CDS y descomprime los resultados."""
from __future__ import annotations

import argparse
import calendar
import zipfile
from pathlib import Path

DATASET = "reanalysis-era5-single-levels"
VARIABLES = [
    "2m_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "total_precipitation",
]
AREA = [44, -2, 39, 5]  # N, W, S, E
HOURS = ["00:00", "06:00", "12:00", "18:00"]


def build_request(year: int, month: int) -> dict:
    """Petición al CDS para un mes, con los días reales de ese mes."""
    n_days = calendar.monthrange(year, month)[1]
    return {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": f"{year}",
        "month": f"{month:02d}",
        "day": [f"{d:02d}" for d in range(1, n_days + 1)],
        "time": HOURS,
        "area": AREA,
        "data_format": "netcdf",
    }


def unpack(downloaded: Path, out_dir: Path) -> list[Path]:
    """Deja los .nc en out_dir. Si lo descargado es un ZIP, lo descomprime."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(downloaded):
        with zipfile.ZipFile(downloaded) as z:
            z.extractall(out_dir)
        downloaded.unlink()
    else:
        downloaded.rename(out_dir / "data.nc")
    return sorted(out_dir.glob("*.nc"))


def download_month(year: int, month: int, root: str = "data/era5") -> list[Path]:
    out_dir = Path(root) / f"{year}-{month:02d}"
    existing = sorted(out_dir.glob("*.nc"))
    if existing:
        print(f"{year}-{month:02d}: ya descargado, se omite")
        return existing

    import cdsapi  # se importa aqui para poder testear el resto sin red

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "download.tmp"
    cdsapi.Client().retrieve(DATASET, build_request(year, month), str(tmp))
    return unpack(tmp, out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga ERA5 mes a mes.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--months", type=int, nargs="+", default=list(range(1, 13)))
    parser.add_argument("--root", default="data/era5")
    args = parser.parse_args()
    for month in args.months:
        files = download_month(args.year, month, args.root)
        print(f"{args.year}-{month:02d}: {len(files)} archivos .nc")


if __name__ == "__main__":
    main()
