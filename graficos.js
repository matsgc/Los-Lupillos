// ============ BLOQUE 4: GRÁFICAS E INDICADORES ============
const $ = id => document.getElementById(id);
const modoActual = () => $('vista').value;                     // 'mes' o 'semana'
const etiquetas = () => modoActual() === 'mes' ? CONFIG.meses
  : Array.from({ length: 52 }, (_, i) => 'S' + (i + 1));
const num = n => Math.round(n).toLocaleString('es-MX');
const corto = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k' : String(n);

// ---------- Indicadores ----------
function dibujarKPIs(k) {
  if (!k) { $('kpis').innerHTML = '<p>No hay focos con estos filtros.</p>'; return; }
  const anomalia = k.anomalia === null ? 'Carga más años' : (k.anomalia > 0 ? '+' : '') + k.anomalia + ' %';
  const tarjetas = [
    [num(k.total), 'Focos de calor detectados en la región'],
    [`${CONFIG.meses[k.record.mes]} ${k.record.anio}`, `Mes con más fuego (${num(k.record.n)} focos)`],
    [k.anioTop[0], `Año con más fuego (${num(k.anioTop[1])} focos)`],
    [anomalia, `${CONFIG.meses[k.mesActual]} ${k.ultimo} frente a lo normal de ese mes`]
  ];
  $('kpis').innerHTML = tarjetas.map(t => `<div class="kpi"><b>${t[0]}</b><span>${t[1]}</span></div>`).join('');
}

// ---------- Calendario de cuadros de colores ----------
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));

// t entre 0 y 1 -> color de la paleta (y si es claro, para elegir el color del texto)
function colorEscala(t, paleta) {
  let i = 0;
  while (i < paleta.length - 2 && t > paleta[i + 1][0]) i++;
  const [t0, c0] = paleta[i], [t1, c1] = paleta[i + 1];
  const k = Math.min(1, Math.max(0, (t - t0) / (t1 - t0))), a = hex(c0), b = hex(c1);
  const rgb = a.map((v, j) => Math.round(v + (b[j] - v) * k));
  return { css: `rgb(${rgb})`, claro: 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] > 150 };
}

function dibujarCalendario(tabla) {
  const anios = Object.keys(tabla).sort(), semanal = modoActual() === 'semana';
  const n = semanal ? 52 : 12, paleta = CONFIG.paletas[$('paleta').value];
  const max = Math.max(1, ...anios.flatMap(a => tabla[a]));
  let rec = { v: -1 };
  anios.forEach(a => tabla[a].forEach((v, i) => { if (v > rec.v) rec = { v, a, i }; }));

  const cols = `grid-template-columns:48px repeat(${n},1fr)`;
  let cabecera = '<div style="grid-column:1"></div>';
  if (semanal) {
    cabecera += CONFIG.meses.map((m, k) =>
      `<div class="lbl" style="grid-column:${Math.floor(CONFIG.diasInicioMes[k] / 7) + 2} / span 4">${m}</div>`).join('');
  } else {
    cabecera += CONFIG.meses.map((m, k) => `<div class="lbl" style="grid-column:${k + 2};text-align:center">${m}</div>`).join('');
  }
  const filas = anios.map(a => `<div class="cal" style="${cols}"><div class="lbl">${a}</div>` +
    tabla[a].map((v, i) => {
      const c = v ? colorEscala(Math.sqrt(v / max), paleta) : { css: '#eef2f6', claro: true };
      const esRecord = rec.a === a && rec.i === i;
      const nombre = semanal ? 'Semana ' + (i + 1) : CONFIG.meses[i];
      return `<div class="celda${semanal ? ' s' : ''}${esRecord ? ' record' : ''}" style="background:${c.css};color:${c.claro ? '#1e293b' : '#fff'}"
        title="${nombre} ${a}: ${num(v)} focos">${semanal ? (esRecord ? '★' : '') : corto(v)}</div>`;
    }).join('') + '</div>').join('');

  const degradado = paleta.map(([t, c]) => `${c} ${t * 100}%`).join(',');
  $('g_calendario').innerHTML = `<div style="overflow-x:auto"><div style="min-width:${semanal ? 900 : 560}px">
      <div class="cal" style="${cols}">${cabecera}</div>${filas}</div></div>
    <div class="leyenda-fila"><span>Pocos focos</span><div class="leyenda" style="background:linear-gradient(to right,${degradado})"></div><span>Muchos focos</span>
      <span class="gris">■ gris = sin focos · ★ = el periodo con más fuego</span></div>`;
}

// ---------- Comparar dos años ----------
function llenarSelectoresAnio(tabla) {
  const anios = Object.keys(tabla).sort();
  ['anio_a', 'anio_b'].forEach((id, i) => {
    const previo = $(id).value;
    $(id).innerHTML = anios.map(a => `<option>${a}</option>`).join('');
    $(id).value = anios.includes(previo) ? previo : anios[Math.max(0, anios.length - 1 - i)];
  });
}

function dibujarComparacion(tabla) {
  const a = $('anio_a').value, b = $('anio_b').value;
  if (!tabla[a] || !tabla[b]) return;
  const suma = x => x.reduce((p, q) => p + q, 0), sa = suma(tabla[a]), sb = suma(tabla[b]);
  const dif = sa ? Math.round((sb - sa) / sa * 100) : 0;
  const titulo = a === b ? 'Elige dos años distintos para compararlos'
    : `En ${b} hubo ${Math.abs(dif)} % ${dif >= 0 ? 'más' : 'menos'} focos que en ${a}`;
  Plotly.newPlot('g_comparacion', [
    { type: 'bar', name: a, x: etiquetas(), y: tabla[a], marker: { color: '#00bbd7' } },
    { type: 'bar', name: b, x: etiquetas(), y: tabla[b], marker: { color: '#dc2626' } }
  ], { barmode: 'group', title: titulo, margin: { t: 40 }, yaxis: { title: 'Focos de calor' } });
}

// ---------- Los dos satélites juntos ----------
function dibujarArmonizacion(focos, filtros) {
  const crudo = crudoPorMes(filtros), armon = {};
  focos.forEach(h => { const m = h.fecha.slice(0, 7); armon[m] = (armon[m] || 0) + 1; });
  const meses = [...new Set([...Object.keys(armon), ...Object.keys(crudo.MODIS), ...Object.keys(crudo.VIIRS)])].sort();
  const serie = (nombre, datos, color, dash) => ({
    type: 'scatter', mode: 'lines+markers', name: nombre, x: meses, y: meses.map(m => datos[m] || 0),
    line: { color, dash: dash || 'solid', width: dash ? 2 : 4 }
  });
  Plotly.newPlot('g_armonizacion', [
    serie('Satélite MODIS (como llega)', crudo.MODIS, '#7c3aed', 'dot'),
    serie('Satélite VIIRS (como llega)', crudo.VIIRS, '#ea580c', 'dot'),
    serie('Serie combinada (la que usa la página)', armon, '#008242')
  ], { margin: { t: 10 }, yaxis: { title: 'Focos de calor' }, legend: { orientation: 'h', y: -0.2 } });
}

// ---------- Qué esperar el próximo año ----------
function dibujarPerfil(tabla) {
  const p = calcularPerfil(tabla), x = etiquetas();
  if (!p) { $('resumen_perfil').textContent = ''; return; }
  const ps = p.periodos;
  Plotly.newPlot('g_perfil', [
    { x, y: ps.map(d => d.prob * 100), yaxis: 'y2', type: 'bar', name: 'Qué tan seguido es temporada alta', marker: { color: 'rgba(51,65,85,.25)' } },
    { x, y: ps.map(d => d.p75), mode: 'lines', line: { width: 0 }, showlegend: false, hoverinfo: 'skip' },
    { x, y: ps.map(d => d.p25), mode: 'lines', line: { width: 0 }, fill: 'tonexty', fillcolor: 'rgba(220,38,38,.25)', name: 'Rango normal' },
    { x, y: ps.map(d => d.med), mode: 'lines+markers', name: 'Lo habitual', line: { color: '#dc2626' } }
  ], { margin: { t: 10 }, yaxis: { title: 'Focos de calor' }, legend: { orientation: 'h', y: -0.2 },
       yaxis2: { overlaying: 'y', side: 'right', range: [0, 100], title: '% de los años', showgrid: false } });

  const top = ps.map((d, i) => ({ ...d, nombre: x[i] })).sort((u, v) => v.prob - u.prob || v.med - u.med).slice(0, 3);
  const lista = top.map(d => `<b>${d.nombre}</b> (en ${Math.round(d.prob * 100)} % de los años)`).join(', ');
  const sem = semaforo(tabla);
  const estado = sem ? `El último periodo (${etiquetas()[sem.i]} ${sem.ult}) tuvo ${num(sem.valor)} focos: ${sem.nivel} (lo habitual es ~${num(sem.med)}).`
                      : 'Para ver si el periodo actual es normal, carga al menos 2 años.';
  const fiable = { baja: 'Baja: hay pocos años de datos, tómalo solo como una idea general. Con 5 o más años mejora.',
                   media: 'Media: ya hay varios años, pero conviene sumar más.', alta: 'Alta: hay muchos años de historial.' }[p.confianza];
  $('resumen_perfil').innerHTML = `🔥 Lo más probable es que haya más incendios en: ${lista}.<br>${estado}<br>
    <b>Qué tan confiable:</b> ${fiable}<br><i>Es una idea basada en el pasado, no una predicción: no considera lluvia ni sequía.</i>`;
}
