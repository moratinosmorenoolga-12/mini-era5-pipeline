"""Plantilla HTML del dashboard (se guarda como texto para que viaje dentro
del paquete sin configurar package-data). Marcadores: __TITLE__, __PLOTLY__,
__DATA__."""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
__PLOTLY__
<style>
:root{
  color-scheme: light;
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,.10);
  --s1:#2a78d6; --s2:#eb6834;
  --good:#0ca30c; --warn:#fab219; --crit:#d03b3b; --warn-ink:#8a5a00;
  --banner-bg:#fff4dc;
}
@media (prefers-color-scheme: dark){
  :root:where(:not([data-theme="light"])){
    color-scheme: dark;
    --page:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
    --s1:#3987e5; --s2:#d95926; --warn-ink:#fab219; --banner-bg:#2e2510;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink-2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
  --s1:#3987e5; --s2:#d95926; --warn-ink:#fab219; --banner-bg:#2e2510;
}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
  font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1280px;margin:0 auto;padding:24px 20px 48px}
header{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:15px;margin:0 0 2px;font-weight:600}
.sub{color:var(--ink-2);margin:0}
.note{color:var(--muted);font-size:12px;margin:2px 0 8px}
.banner{background:var(--banner-bg);border:1px solid var(--border);border-left:4px solid var(--warn);
  padding:10px 14px;border-radius:8px;margin:16px 0 0;color:var(--ink)}
.filters{display:flex;gap:20px;flex-wrap:wrap;align-items:end;margin:20px 0 16px;
  padding:12px 14px;background:var(--surface);border:1px solid var(--border);border-radius:10px}
.filters label{display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--ink-2)}
select,button{font:inherit;color:var(--ink);background:var(--page);border:1px solid var(--axis);
  border-radius:6px;padding:6px 10px}
button{cursor:pointer}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:16px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.tile .lab{font-size:12px;color:var(--ink-2)}
.tile .val{font-size:26px;font-weight:600;margin:2px 0}
.tile .ctx{font-size:12px;color:var(--muted)}
.grid2{display:grid;grid-template-columns:3fr 2fr;gap:16px;margin-bottom:16px}
.grid22{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
@media (max-width:900px){.grid2,.grid22{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 14px 8px;min-width:0}
.chart{width:100%;height:330px}
.chart.tall{height:440px}
.ptgrid{display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;margin:8px 0}
.ptgrid div{font-size:13px;color:var(--ink-2)} .ptgrid b{color:var(--ink);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--grid);font-variant-numeric:tabular-nums}
th:first-child,td:first-child{text-align:left}
th{color:var(--ink-2);font-weight:600}
tr.sel td{background:color-mix(in srgb,var(--s1) 10%,transparent)}
.st{display:inline-flex;gap:6px;align-items:center;font-weight:600}
.st i{font-style:normal;display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;
  color:#fff;font-size:11px}
.st.OK i{background:var(--good)} .st.WARN i{background:var(--warn);color:#0b0b0b} .st.FAIL i{background:var(--crit)}
.qcbadge{font-size:13px;padding:6px 10px;border-radius:999px;border:1px solid var(--border);background:var(--surface)}
details{margin-top:10px} summary{cursor:pointer;color:var(--ink-2)}
.scroll{max-height:320px;overflow:auto}
footer{color:var(--muted);font-size:12px;margin-top:24px}
footer li{margin:3px 0}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1 id="title"></h1>
      <p class="sub" id="subtitle"></p>
    </div>
    <div style="display:flex;gap:10px;align-items:center">
      <span class="qcbadge" id="qcbadge"></span>
      <button id="theme" type="button">Cambiar tema</button>
    </div>
  </header>
  <div id="banner"></div>

  <div class="filters" role="group" aria-label="Filtros">
    <label>Punto de interés
      <select id="point"></select>
    </label>
    <label>Variable del mapa
      <select id="mapvar">
        <option value="t_media">Temperatura media (°C)</option>
        <option value="precip_total">Precipitación total (mm)</option>
        <option value="viento_medio">Viento medio a 10 m (m/s)</option>
        <option value="viento_max">Viento máximo a 10 m (m/s)</option>
      </select>
    </label>
    <span class="note" id="cellnote" style="margin:0 0 6px"></span>
  </div>

  <section class="kpis" id="kpis" aria-label="Indicadores de toda la zona"></section>

  <div class="grid2">
    <div class="card">
      <h2 id="maptitle">Mapa</h2>
      <p class="note">Cada píxel es una celda de 0,25° (~25 km). Los círculos son los puntos de interés.</p>
      <div id="map" class="chart tall"></div>
    </div>
    <div class="card">
      <h2 id="pttitle">Punto</h2>
      <p class="note">Valores de la celda de la rejilla más cercana.</p>
      <div class="ptgrid" id="ptgrid"></div>
      <div id="rose" class="chart" style="height:300px"></div>
    </div>
  </div>

  <div class="grid22">
    <div class="card"><h2>Temperatura a 2 m</h2>
      <p class="note">Punto: valor de cada instante. Zona: media diaria ponderada por área.</p>
      <div id="temp" class="chart"></div></div>
    <div class="card"><h2 id="ptitle">Precipitación diaria</h2>
      <p class="note" id="pnote"></p>
      <div id="precip" class="chart"></div></div>
    <div class="card"><h2>Viento a 10 m</h2>
      <p class="note">Velocidad calculada como √(u² + v²).</p>
      <div id="wind" class="chart"></div></div>
    <div class="card"><h2>Ciclo diario de la temperatura</h2>
      <p class="note">Media de todos los días para cada hora UTC (en Cataluña, hora local = UTC + 1 en invierno).</p>
      <div id="diurnal" class="chart"></div></div>
  </div>

  <div class="grid22">
    <div class="card"><h2>Comparativa de puntos</h2>
      <p class="note">Haz clic en una fila para seleccionar el punto.</p>
      <div class="scroll"><table id="pttable"></table></div></div>
    <div class="card"><h2>Control de calidad</h2>
      <p class="note" id="qcsource"></p>
      <div class="scroll"><table id="qctable"></table></div></div>
  </div>

  <div class="card">
    <h2>Datos diarios de la zona</h2>
    <details><summary>Ver tabla (los mismos datos de los gráficos)</summary>
      <div class="scroll"><table id="dailytable"></table></div></details>
  </div>

  <footer>
    <ul id="method"></ul>
    <div id="gen"></div>
  </footer>
</div>

<script>
const D = __DATA__;
Plotly.register({moduleType:"locale", name:"es", dictionary:{}, format:{
  days:["domingo","lunes","martes","miércoles","jueves","viernes","sábado"],
  shortDays:["dom","lun","mar","mié","jue","vie","sáb"],
  months:["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],
  shortMonths:["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"],
  date:"%d/%m/%Y", decimal:",", thousands:"."}});
const $ = id => document.getElementById(id);
const fmt = (v, nd=1) => v == null ? "–" : v.toLocaleString("es-ES",{minimumFractionDigits:nd,maximumFractionDigits:nd});
const fdate = iso => new Date(iso + (iso.length <= 16 ? ":00Z" : "")).toLocaleString("es-ES",
  {day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",timeZone:"UTC"}) + " UTC";
const fday = d => new Date(d.slice(0,10)+"T00:00:00Z").toLocaleDateString("es-ES",{day:"numeric",month:"short",year:"numeric",timeZone:"UTC"});
const nearestName = (lat, lon) => {
  let best=null, bd=1e9;
  for (const [n,p] of Object.entries(D.points)){
    const d=Math.hypot(p.lat-lat,(p.lon-lon)*Math.cos(lat*Math.PI/180));
    if (d<bd){bd=d;best=n;}
  }
  return bd < 0.3 ? best : `${fmt(lat,2)}°N, ${fmt(lon,2)}°E`;
};
const where = e => nearestName(e.lat, e.lon);

function css(name){ return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function isDark(){ return getComputedStyle(document.documentElement).colorScheme.includes("dark"); }

const SEQ = ["#cde2fb","#9ec5f4","#6da7ec","#3987e5","#256abf","#184f95","#0d366b"];
function seqScale(){ const s = isDark() ? [...SEQ].reverse() : SEQ;
  return s.map((c,i)=>[i/(s.length-1), c]); }
function divScale(){ const mid = isDark() ? "#383835" : "#f0efec";
  return [[0,"#184f95"],[0.25,"#5598e7"],[0.5,mid],[0.75,"#ec835a"],[1,"#b8302f"]]; }
function roseColors(){ return isDark()
  ? ["#184f95","#256abf","#3987e5","#6da7ec","#9ec5f4","#cde2fb"]
  : ["#86b6ef","#5598e7","#2a78d6","#256abf","#184f95","#0d366b"]; }

function baseLayout(extra={}){
  const ink2=css("--ink-2"), grid=css("--grid"), axis=css("--axis");
  const ax = {gridcolor:grid, linecolor:axis, zerolinecolor:axis, tickfont:{color:ink2,size:11},
              title:{font:{color:ink2,size:12}}, automargin:true};
  return Object.assign({
    paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)",
    font:{family:'system-ui,-apple-system,"Segoe UI",sans-serif', color:css("--ink"), size:12},
    margin:{l:48,r:12,t:8,b:36}, hovermode:"x unified",
    hoverlabel:{bgcolor:css("--surface"), bordercolor:axis, font:{color:css("--ink")}},
    legend:{orientation:"h", x:0, y:1.12, font:{color:ink2}},
    xaxis:{...ax}, yaxis:{...ax},
  }, extra);
}
const CFG = {displayModeBar:false, responsive:true, locale:"es"};

let POINT = Object.keys(D.points)[0];

function renderHeader(){
  const m = D.meta;
  $("title").textContent = `${m.title} · ${m.region}`;
  $("subtitle").textContent = `ERA5 (ECMWF/Copernicus) · ${fday(m.start)} – ${fday(m.end)} · ` +
    `cada ${fmt(m.step_h,0)} h · ${m.n_times} instantes · rejilla ${m.grid[0]} × ${m.grid[1]}`;
  if (m.synthetic) $("banner").innerHTML = `<div class="banner"><b>Datos sintéticos de demostración.</b> ` +
    `Este panel se ha generado con valores inventados por <code>era5qc.demo</code> para probar el pipeline. ` +
    `Ejecuta <code>python -m era5qc.pipeline</code> con tus descargas para ver datos reales.</div>`;
  const counts = {OK:0,WARN:0,FAIL:0};
  D.qc.results.forEach(r => counts[r.status] = (counts[r.status]||0)+1);
  const worst = counts.FAIL ? "FAIL" : counts.WARN ? "WARN" : "OK";
  const icon = {OK:"✓",WARN:"!",FAIL:"✕"}[worst];
  $("qcbadge").innerHTML = `<span class="st ${worst}"><i aria-hidden="true">${icon}</i>Calidad: ${worst}</span>` +
    ` <span style="color:var(--muted)">${counts.OK} OK · ${counts.WARN} WARN · ${counts.FAIL} FAIL</span>`;
  $("qcsource").textContent = `Resultados de ${D.qc.source}, sobre los datos sin transformar.`;
  $("qctable").innerHTML = "<tr><th>Comprobación</th><th style='text-align:left'>Estado</th><th style='text-align:left'>Detalle</th></tr>" +
    D.qc.results.map(r => `<tr><td>${r.name}</td><td style="text-align:left"><span class="st ${r.status}"><i aria-hidden="true">${{OK:"✓",WARN:"!",FAIL:"✕"}[r.status]||"?"}</i>${r.status}</span></td><td style="text-align:left">${r.detail}</td></tr>`).join("");
  const pc = m.precip_complete;
  $("pnote").textContent = pc ? "Suma de los 24 valores horarios de cada día (total real)."
    : `Estimación: con datos cada ${fmt(m.step_h,0)} h solo se ve 1 de cada ${fmt(m.step_h,0)} horas; se multiplica por ${fmt(m.step_h,0)}.`;
  $("ptitle").textContent = pc ? "Precipitación diaria" : "Precipitación diaria (estimada)";
  $("method").innerHTML = [
    "Temperatura convertida de K a °C (−273,15); precipitación de m a mm (×1000).",
    "Dirección del viento = de dónde sopla (0° norte, 90° este), calculada a partir de u10 y v10.",
    "Medias de la zona ponderadas por cos(latitud): las celdas del norte son algo más pequeñas.",
    "Cada punto usa la celda más cercana: en la costa, esa celda puede mezclar tierra y mar.",
    "Horas en UTC. La precipitación horaria de ERA5 es lo acumulado en la hora que termina en ese instante.",
  ].map(s=>`<li>${s}</li>`).join("");
  $("gen").textContent = `Generado ${m.generated} con era5qc.`;
}

function renderKpis(){
  const k = D.kpis, e = k.extremes, pc = D.meta.precip_complete;
  const tiles = [
    ["Temperatura media de la zona", `${fmt(k.t_media_area)} °C`, "todo el periodo"],
    ["Mínima absoluta", `${fmt(e.t_min.valor)} °C`, `${where(e.t_min)} · ${fdate(e.t_min.fecha)}`],
    ["Máxima absoluta", `${fmt(e.t_max.valor)} °C`, `${where(e.t_max)} · ${fdate(e.t_max.fecha)}`],
    [pc ? "Precipitación media acumulada" : "Precipitación media (estim.)", `${fmt(k.precip_media_area)} mm`, "promedio de todas las celdas"],
    ["Hora más lluviosa", `${fmt(e.precip_max_hora.valor)} mm`, `${where(e.precip_max_hora)} · ${fdate(e.precip_max_hora.fecha)}`],
    ["Viento máximo a 10 m", `${fmt(e.viento_max.valor)} m/s`, `${fmt(e.viento_max.valor*3.6,0)} km/h · ${where(e.viento_max)}`],
  ];
  $("kpis").innerHTML = tiles.map(([l,v,c]) => `<div class="tile"><div class="lab">${l}</div><div class="val">${v}</div><div class="ctx">${c}</div></div>`).join("");
}

function renderMap(){
  const key = $("mapvar").value, z = D.maps[key];
  const isT = key === "t_media";
  const unit = isT ? "°C" : key === "precip_total" ? "mm" : "m/s";
  const flat = z.flat().filter(v => v != null);
  const mean = flat.reduce((a,b)=>a+b,0)/flat.length;
  const span = Math.max(...flat.map(v=>Math.abs(v-mean)));
  $("maptitle").textContent = $("mapvar").selectedOptions[0].text +
    (key==="precip_total" && !D.meta.precip_complete ? " · estimación" : "");
  const heat = {type:"heatmap", x:D.grid.lon, y:D.grid.lat, z,
    colorscale: isT ? divScale() : seqScale(),
    zmid: isT ? mean : undefined, zmin: isT ? mean-span : undefined, zmax: isT ? mean+span : undefined,
    colorbar:{title:{text:unit, font:{color:css("--ink-2")}}, tickfont:{color:css("--ink-2")}, outlinewidth:0, thickness:12},
    hovertemplate:`%{y:.2f}°N, %{x:.2f}°E<br><b>%{z:.1f} ${unit}</b><extra></extra>`};
  const names = Object.keys(D.points);
  const pts = {type:"scatter", mode:"markers+text", x:names.map(n=>D.points[n].lon), y:names.map(n=>D.points[n].lat),
    text:names.map(n=>n.split(" (")[0]), textposition:"top center",
    textfont:{color:css("--ink"), size:11},
    marker:{size:names.map(n=>n===POINT?14:9), color:"rgba(0,0,0,0)",
      line:{color:names.map(n=>n===POINT?css("--ink"):css("--ink-2")), width:names.map(n=>n===POINT?3:1.5)}},
    hovertemplate:"%{text}<extra></extra>", customdata:names};
  const midlat = (D.grid.lat[0]+D.grid.lat[D.grid.lat.length-1])/2;
  const lay = baseLayout({hovermode:"closest", showlegend:false, margin:{l:44,r:8,t:8,b:36},
    xaxis:{...baseLayout().xaxis, title:{text:"longitud (°)"}, showgrid:false, constrain:"domain"},
    yaxis:{...baseLayout().yaxis, title:{text:"latitud (°)"}, showgrid:false,
           scaleanchor:"x", scaleratio:1/Math.cos(midlat*Math.PI/180), constrain:"domain"}});
  Plotly.react("map", [heat, pts], lay, CFG);
  $("map").on && $("map").removeAllListeners && $("map").removeAllListeners("plotly_click");
  $("map").on("plotly_click", ev => { const p = ev.points.find(p => p.customdata); if (p) setPoint(p.customdata); });
}

function renderPoint(){
  const P = D.points[POINT], s = P.summary;
  $("pttitle").textContent = POINT;
  $("cellnote").textContent = `Celda usada: ${fmt(P.lat,2)}°N, ${fmt(P.lon,2)}°E`;
  const pc = D.meta.precip_complete;
  $("ptgrid").innerHTML = [
    ["T media", `${fmt(s.t_media_c)} °C`], ["T mín / máx", `${fmt(s.t_min_c)} / ${fmt(s.t_max_c)} °C`],
    [pc?"Precipitación total":"Precip. (estim.)", `${fmt(s.precip_total_mm)} mm`], ["Viento medio", `${fmt(s.viento_medio_ms)} m/s`],
    ["Viento máximo", `${fmt(s.viento_max_ms)} m/s`], ["Dirección dominante", s.dir_dominante],
  ].map(([a,b])=>`<div>${a}<br><b>${b}</b></div>`).join("");

  // rosa de los vientos
  const cols = roseColors();
  const rose = P.rose.bins.map((b,i)=>({type:"barpolar", name:`${b} m/s`, r:P.rose.values[i], theta:P.rose.sectors,
    marker:{color:cols[i], line:{color:css("--surface"), width:1}},
    hovertemplate:`%{theta} · ${b} m/s: %{r:.1f}%<extra></extra>`}));
  Plotly.react("rose", rose, baseLayout({hovermode:"closest", margin:{l:24,r:24,t:28,b:8},
    legend:{orientation:"v", x:1.02, y:0.5, font:{color:css("--ink-2"), size:11}, title:{text:"velocidad", font:{size:11, color:css("--ink-2")}}},
    polar:{bgcolor:"rgba(0,0,0,0)", barmode:"stack",
      angularaxis:{direction:"clockwise", rotation:90, gridcolor:css("--grid"), linecolor:css("--axis"), tickfont:{color:css("--ink-2"), size:10}},
      radialaxis:{gridcolor:css("--grid"), linecolor:css("--axis"), tickfont:{color:css("--muted"), size:9}, ticksuffix:"%", angle:90}}}), CFG);

  const s1 = css("--s1"), s2 = css("--s2");
  const shortName = POINT.split(" (")[0];
  Plotly.react("temp", [
    {type:"scatter", mode:"lines", name:shortName, x:D.time, y:P.t, line:{color:s1, width:1.5}, hovertemplate:"%{y:.1f} °C"},
    {type:"scatter", mode:"lines", name:"Media de la zona (diaria)", x:D.days.map(d=>d+"T12:00"), y:D.area.t_media, line:{color:s2, width:2}, hovertemplate:"%{y:.1f} °C"},
  ], baseLayout({yaxis:{...baseLayout().yaxis, title:{text:"°C"}}}), CFG);

  Plotly.react("precip", [
    {type:"bar", name:shortName, x:D.days, y:P.daily.precip, marker:{color:s1, cornerradius:4}, hovertemplate:"%{y:.1f} mm"},
    {type:"bar", name:"Media de la zona", x:D.days, y:D.area.precip, marker:{color:s2, cornerradius:4}, hovertemplate:"%{y:.1f} mm"},
  ], baseLayout({barmode:"group", bargap:0.25, bargroupgap:0.1, yaxis:{...baseLayout().yaxis, title:{text:"mm/día"}, rangemode:"tozero"}}), CFG);

  Plotly.react("wind", [
    {type:"scatter", mode:"lines", name:shortName, x:D.time, y:P.ws, line:{color:s1, width:1.5}, hovertemplate:"%{y:.1f} m/s"},
    {type:"scatter", mode:"lines", name:"Media de la zona (diaria)", x:D.days.map(d=>d+"T12:00"), y:D.area.viento, line:{color:s2, width:2}, hovertemplate:"%{y:.1f} m/s"},
  ], baseLayout({yaxis:{...baseLayout().yaxis, title:{text:"m/s"}, rangemode:"tozero"}}), CFG);

  const hrs = D.area.diurnal_hours.map(h => `${String(h).padStart(2,"0")}:00`);
  Plotly.react("diurnal", [
    {type:"scatter", mode:"lines+markers", name:shortName, x:hrs, y:P.diurnal, line:{color:s1, width:2}, marker:{size:8, line:{color:css("--surface"), width:2}}, hovertemplate:"%{y:.1f} °C"},
    {type:"scatter", mode:"lines+markers", name:"Media de la zona", x:hrs, y:D.area.diurnal, line:{color:s2, width:2}, marker:{size:8, line:{color:css("--surface"), width:2}}, hovertemplate:"%{y:.1f} °C"},
  ], baseLayout({xaxis:{...baseLayout().xaxis, title:{text:"hora UTC"}, type:"category", tickangle:0, tickvals:hrs.filter((_,i)=>i%3===0)}, yaxis:{...baseLayout().yaxis, title:{text:"°C"}}}), CFG);

  // tabla comparativa
  const pc2 = D.meta.precip_complete;
  $("pttable").innerHTML = `<tr><th>Punto</th><th>T media</th><th>T mín</th><th>T máx</th><th>${pc2?"Precip.":"Precip. est."} (mm)</th><th>Viento medio</th><th>Dir.</th></tr>` +
    Object.entries(D.points).map(([n,p]) => { const s=p.summary;
      return `<tr data-n="${n}" class="${n===POINT?"sel":""}" style="cursor:pointer"><td>${n}</td><td>${fmt(s.t_media_c)}</td><td>${fmt(s.t_min_c)}</td><td>${fmt(s.t_max_c)}</td><td>${fmt(s.precip_total_mm)}</td><td>${fmt(s.viento_medio_ms)}</td><td>${s.dir_dominante}</td></tr>`;}).join("");
  document.querySelectorAll("#pttable tr[data-n]").forEach(tr => tr.onclick = () => setPoint(tr.dataset.n));
}

function renderDailyTable(){
  $("dailytable").innerHTML = "<tr><th>Día</th><th>T media (°C)</th><th>Precipitación (mm)</th><th>Viento medio (m/s)</th></tr>" +
    D.days.map((d,i)=>`<tr><td>${d}</td><td>${fmt(D.area.t_media[i])}</td><td>${fmt(D.area.precip[i],2)}</td><td>${fmt(D.area.viento[i])}</td></tr>`).join("");
}

function setPoint(n){ POINT = n; $("point").value = n; renderPoint(); renderMap(); }
function renderAll(){ renderHeader(); renderKpis(); renderMap(); renderPoint(); renderDailyTable(); }

$("point").innerHTML = Object.keys(D.points).map(n=>`<option>${n}</option>`).join("");
$("point").onchange = e => setPoint(e.target.value);
$("mapvar").onchange = renderMap;
$("theme").onclick = () => {
  document.documentElement.dataset.theme = isDark() ? "light" : "dark";
  renderMap(); renderPoint();
};
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { renderMap(); renderPoint(); });
renderAll();
</script>
</body>
</html>
"""
