import glob
import xarray as xr
import matplotlib.pyplot as plt

files = sorted(glob.glob("data/*.nc"))
print("Archivos:", files)

ds = xr.merge([xr.open_dataset(f) for f in files])
print(ds)

t2m_c = ds["t2m"] - 273.15
t2m_c.isel(valid_time=0).plot()
plt.title("Temperatura a 2 m (°C)")
plt.savefig("mapa.png")
print("Mapa guardado en mapa.png")
