// ============ BLOQUE 2: FILTROS Y CÁLCULOS ============

function leerFiltros() {
  const v = id => document.getElementById(id).value;
  return {
    latMin: +v('lat_min'), latMax: +v('lat_max'), lonMin: +v('lon_min'), lonMax: +v('lon_max'),
    ini: v('f_ini'), fin: v('f_fin'),
    soloVeg: document.getElementById('solo_veg').checked   // tipo 0 = vegetación
  };
}

function filtrarFocos(f) {
  return DATOS.focos.filter(h =>
    h.lat >= f.latMin && h.lat <= f.latMax && h.lon >= f.lonMin && h.lon <= f.lonMax &&
    (!f.ini || h.fecha >= f.ini) && (!f.fin || h.fecha <= f.fin) &&
    (!f.soloVeg || h.tipo === 0));
}

// Índice del periodo: mes = 0..11. Semana = 0..51 (semana 1 = días 1-7 del año, etc.)
function indicePeriodo(fecha, modo) {
  if (modo === 'mes') return Number(fecha.slice(5, 7)) - 1;
  const dia = Math.floor((new Date(fecha) - new Date(fecha.slice(0, 4) + '-01-01')) / 86400000);
  return Math.min(Math.floor(dia / 7), 51);
}

// Devuelve { "2024": [12 o 52 números], "2025": [...] }
function contarPorAnioPeriodo(focos, modo) {
  const n = modo === 'mes' ? 12 : 52, tabla = {};
  focos.forEach(h => {
    const anio = h.fecha.slice(0, 4);
    if (!tabla[anio]) tabla[anio] = Array(n).fill(0);
    tabla[anio][indicePeriodo(h.fecha, modo)]++;
  });
  return tabla;
}

function mediana(nums) {
  const s = [...nums].sort((a, b) => a - b), m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

// Indicadores clave
function calcularKPIs(tabla, total) {
  const anios = Object.keys(tabla).sort();
  if (!anios.length) return null;
  let record = { anio: '', mes: 0, n: -1 };
  anios.forEach(a => tabla[a].forEach((n, m) => { if (n > record.n) record = { anio: a, mes: m, n }; }));

  const totales = anios.map(a => [a, tabla[a].reduce((x, y) => x + y, 0)]);
  const anioTop = totales.sort((x, y) => y[1] - x[1])[0];

  // Anomalía: último mes con datos del último año vs. mediana de ese mismo mes en los otros años
  const ultimo = anios[anios.length - 1];
  let mesActual = 11;
  while (mesActual > 0 && tabla[ultimo][mesActual] === 0) mesActual--;
  const otros = anios.slice(0, -1).map(a => tabla[a][mesActual]);
  const med = otros.length ? mediana(otros) : null;
  const anomalia = med ? Math.round((tabla[ultimo][mesActual] - med) / med * 100) : null;

  return { total, record, anioTop, ultimo, mesActual, anomalia };
}

// Conteo crudo por sensor y mes, solo dentro de la región y fechas elegidas (aprox. a 0.1°)
function crudoPorMes(f) {
  const res = { MODIS: {}, VIIRS: {} };
  for (const k in DATOS.crudo) {
    const [sensor, mes, tipo, ilat, ilon] = k.split('|');
    const lat = ilat / 10, lon = ilon / 10;
    if (lat < f.latMin || lat > f.latMax || lon < f.lonMin || lon > f.lonMax) continue;
    if ((f.ini && mes < f.ini.slice(0, 7)) || (f.fin && mes > f.fin.slice(0, 7))) continue;
    if (f.soloVeg && tipo !== '0') continue;
    res[sensor][mes] = (res[sensor][mes] || 0) + DATOS.crudo[k];
  }
  return res;
}

function percentil(nums, p) {
  const s = [...nums].sort((a, b) => a - b), i = (s.length - 1) * p, b = Math.floor(i);
  return s[b] + ((s[b + 1] ?? s[b]) - s[b]) * (i - b);
}

// Perfil esperado por periodo, con lo que pasó en los años cargados:
//  med/p25/p75 = lo típico, prob = en qué fracción de años ese periodo estuvo POR ENCIMA
//  del promedio de su propio año ("¿es temporada alta?")
function calcularPerfil(tabla) {
  const anios = Object.keys(tabla).sort(), n = anios.length;
  if (!n) return null;
  const largo = tabla[anios[0]].length;
  const promedio = anios.map(a => tabla[a].reduce((x, y) => x + y, 0) / largo);
  const periodos = [];
  for (let i = 0; i < largo; i++) {
    const v = anios.map(a => tabla[a][i]);
    periodos.push({ med: mediana(v), p25: percentil(v, 0.25), p75: percentil(v, 0.75),
                    prob: v.filter((x, k) => x > promedio[k]).length / n });
  }
  return { n, periodos, confianza: n >= 6 ? 'alta' : n >= 3 ? 'media' : 'baja' };
}

// Semáforo: último periodo con datos del último año vs. los años anteriores
function semaforo(tabla) {
  const anios = Object.keys(tabla).sort();
  if (anios.length < 2) return null;
  const ult = anios[anios.length - 1];
  let i = tabla[ult].length - 1;
  while (i > 0 && tabla[ult][i] === 0) i--;
  const hist = anios.slice(0, -1).map(a => tabla[a][i]), valor = tabla[ult][i];
  const nivel = valor > percentil(hist, 0.75) ? '🔴 por encima de lo normal'
              : valor < percentil(hist, 0.25) ? '🟢 por debajo de lo normal' : '🟡 dentro de lo normal';
  return { ult, i, valor, nivel, med: Math.round(mediana(hist)) };
}
