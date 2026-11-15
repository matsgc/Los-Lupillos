// ============ BLOQUE 5: CONEXIÓN (botones y eventos) ============
let focosFiltrados = [], tablaActual = {};

function actualizarTodo() {
  if (!DATOS.focos.length) return;
  const filtros = leerFiltros();
  focosFiltrados = filtrarFocos(filtros);
  tablaActual = contarPorAnioPeriodo(focosFiltrados, modoActual());
  dibujarKPIs(calcularKPIs(contarPorAnioPeriodo(focosFiltrados, 'mes'), focosFiltrados.length));
  dibujarCalendario(tablaActual);
  llenarSelectoresAnio(tablaActual);
  dibujarComparacion(tablaActual);
  dibujarPerfil(tablaActual);
  dibujarArmonizacion(focosFiltrados, filtros);
  dibujarPuntos(focosFiltrados);
  $('estado').textContent = `✅ ${focosFiltrados.length.toLocaleString('es-MX')} focos armonizados en el área y fechas elegidas.`;
}

function descargarCSV() {
  const filas = ['fecha,latitud,longitud,sensor,frp'].concat(
    focosFiltrados.map(h => [h.fecha, h.lat, h.lon, h.sensor, h.frp].join(',')));
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(new Blob([filas.join('\n')], { type: 'text/csv' }));
  enlace.download = 'focos_armonizados.csv';
  enlace.click();
}

$('archivos').addEventListener('change', async e => {
  $('estado').textContent = '⏳ Leyendo y armonizando archivos...';
  try {
    await cargarArchivos([...e.target.files]);
  } catch (err) { $('estado').textContent = '⚠️ ' + err.message; return; }
  $('lista-archivos').textContent = 'Cargados: ' + DATOS.archivos.join(' · ');
  const fechas = DATOS.focos.map(h => h.fecha).sort();      // fechas iniciales = todo el rango
  $('f_ini').value = fechas[0];
  $('f_fin').value = fechas[fechas.length - 1];
  actualizarTodo();
});

// Fechas y casilla: recalculan solas
$('f_ini').onchange = $('f_fin').onchange = $('solo_veg').onchange = actualizarTodo;
$('btn-dibujar').onclick = activarDibujo;
$('btn-mexico').onclick = () => { const m = CONFIG.mexico; ponerArea(m.latMin, m.latMax, m.lonMin, m.lonMax); mapa.setView([23.6, -102.5], 5); actualizarTodo(); };
$('btn-csv').onclick = descargarCSV;
$('vista').onchange = actualizarTodo;
$('paleta').onchange = () => dibujarCalendario(tablaActual);
$('anio_a').onchange = $('anio_b').onchange = () => dibujarComparacion(tablaActual);

// Arranque: área = todo México
ponerArea(CONFIG.mexico.latMin, CONFIG.mexico.latMax, CONFIG.mexico.lonMin, CONFIG.mexico.lonMax, false);
