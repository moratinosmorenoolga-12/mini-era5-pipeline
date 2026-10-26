import cdsapi

def download_sample(target="data/era5_sample.nc"):
    c = cdsapi.Client()
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": [
                "2m_temperature",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "total_precipitation",
            ],
            "year": "2023",
            "month": "01",
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [44, -2, 39, 5],  # N, W, S, E
            "data_format": "netcdf",
        },
        target,
    )

if __name__ == "__main__":
    download_sample()