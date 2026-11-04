import glob
import xarray as xr
import matplotlib.pyplot as plt

files = sorted(glob.glob("data/*.nc"))
print("Archivos:", files)

ds = xr.merge([xr.open_dataset(f) for f in files])
print(ds)

t2m_c = ds["t2m"] - 273.15
t2m_c.attrs["units"] = "°C"
t2m_c.isel(valid_time=0).plot()
plt.title("ERA5 2 m temperature, 2023-01-01 00:00 UTC")
plt.savefig("mapa.png")
print("Mapa guardado en mapa.png")
