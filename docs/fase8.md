# Fase 8: pipeline de descarga y análisis, y dashboard

*Continuación de la «Guía para dummies». Practica: orquestar un proceso de
principio a fin, analizar datos meteorológicos y comunicar resultados.*

## 21. Qué añade esta fase

Hasta ahora cada paso se lanzaba a mano. Ahora un solo comando hace todo:

```
descarga (CDS) → calidad (quality.py) → análisis → dashboard.html
```

| Archivo nuevo | Qué hace |
|---|---|
| `config/pipeline.yaml` | Periodo, zona, variables y puntos de interés. **Se cambia aquí, no en el código.** |
| `src/era5qc/fetch.py` | Descarga mes a mes según la configuración. Si un mes ya está, no lo repite (caché). Tu `download.py` no se toca. |
| `src/era5qc/io.py` | Detecta el ZIP sorpresa, lo descomprime y junta instant + accum + varios meses. |
| `src/era5qc/qc_bridge.py` | Llama a tu `quality.py` sin modificarlo. |
| `src/era5qc/analysis.py` | Conversiones y cálculos (funciones pequeñas y testeadas). |
| `src/era5qc/dashboard.py`, `_template.py` | Empaquetan los resultados en un HTML interactivo. |
| `src/era5qc/pipeline.py` | El «director de orquesta». |
| `src/era5qc/demo.py` | Fabrica datos **sintéticos** con la forma de ERA5 (para probar sin red). |
| `tests/test_analysis.py` | 17 tests nuevos, incluido uno de extremo a extremo. |

## 22. Instalación

En Ubuntu, con `.venv` activado:

```
pip install pyyaml plotly
```

Y añádelas a `pyproject.toml`, en `dependencies`, para que Docker y GitHub
Actions también las instalen:

```toml
dependencies = ["xarray", "netcdf4", "cdsapi", "matplotlib", "pyyaml", "plotly"]
```

- `pyyaml`: lee el archivo de configuración `.yaml`.
- `plotly`: solo se usa para copiar su JavaScript dentro del HTML; los gráficos
  se dibujan en el navegador.

## 23. Uso

```
python -m era5qc.pipeline --demo            # 1º: probar con datos inventados
python -m era5qc.pipeline                   # descargar y analizar de verdad
python -m era5qc.pipeline --skip-download   # repetir el análisis sin descargar
```

(Si no instalaste el proyecto con `pip install -e .`, antepón `PYTHONPATH=src`.)

Se crean en `outputs/` (añádelo a `.gitignore`):

| Archivo | Para qué |
|---|---|
| `dashboard.html` | El panel. Ábrelo desde Windows: `\\wsl$\Ubuntu\home\olgamm12\proyectos\mini-era5-pipeline\outputs` |
| `daily.csv` | Serie diaria de la zona (se abre con Excel) |
| `points.csv` | Resumen de cada ciudad |
| `qc.csv` | Resultado de cada control de calidad |
| `summary.json` | Todo lo anterior para otros programas |

**Orden importante:** la calidad se comprueba sobre los datos *originales*
(Kelvin, metros), antes de convertir nada. Si hay un `FAIL`, el pipeline se
detiene y devuelve código 1, como `quality.py`.

## 24. Qué se calcula y por qué

| Cálculo | Fórmula | Detalle a recordar |
|---|---|---|
| Temperatura en °C | `t2m − 273,15` | |
| Precipitación en mm | `tp × 1000` | Se ponen a 0 los valores negativos diminutos (ruido numérico de ERA5). |
| Velocidad del viento | `√(u² + v²)` | Teorema de Pitágoras con las dos componentes. |
| Dirección del viento | `(270 − atan2(v, u)) mod 360` | Es de **dónde viene**: 270° = viento del oeste. |
| Media de la zona | media ponderada por `cos(latitud)` | En la rejilla, las celdas del norte son algo más pequeñas. |
| Punto de interés | celda más cercana | En la costa, la celda puede ser medio mar. |
| Rosa de los vientos | % de horas por dirección (16) y velocidad | |
| Ciclo diario | media por hora UTC | |

### La trampa de la precipitación

En ERA5 horario, cada valor de `tp` es la lluvia **de la hora que acaba** en
ese instante. Con las 24 horas, sumar da el total real. Con solo 00, 06, 12 y
18 h (lo que se descargó en la fase 1) solo vemos 1 de cada 6 horas: la suma
se queda corta. Por eso:

- `config/pipeline.yaml` pide ahora `hours: all` (24 horas al día).
- Si usas datos cada 6 h, el pipeline **estima** el total (suma × 6) y el
  dashboard lo marca como «estimación».

## 25. El dashboard

Un único archivo HTML, sin servidor: se abre con doble clic y funciona sin
internet. Contiene:

- **Indicadores**: temperatura media, mínima y máxima absolutas (con lugar y
  hora), precipitación media, hora más lluviosa y viento máximo.
- **Mapa** con selector de variable. Temperatura en escala azul-rojo centrada
  en la media de la zona (azul = más frío que la media); lluvia y viento en
  escala de un solo color (más oscuro = más).
- **Punto de interés** (selector o clic en el mapa/tabla): resumen y rosa de
  los vientos.
- **Series temporales** de temperatura, lluvia y viento: el punto elegido
  (azul) frente a la media de la zona (naranja).
- **Ciclo diario** de la temperatura.
- **Tablas**: comparativa de ciudades, control de calidad y datos diarios.
- Modo claro/oscuro y aviso visible si los datos son sintéticos.

## 26. Ideas para ampliar

- Pedir varios eneros (`years: [2019, 2020, 2021, 2022, 2023]`) y comparar
  cada año con la media: es una **anomalía**, la base de los estudios de clima.
- Añadir variables (`mean_sea_level_pressure`, `2m_dewpoint_temperature` para
  la humedad relativa).
- En GitHub Actions, ejecutar `--demo` y guardar el dashboard como artefacto
  (ver `docs/ci-snippet.yml`).
