// ============ BLOQUE 3: MAPA ============
// El mapa no deja salir de México
const LIMITES = [[CONFIG.mexico.latMin - 1, CONFIG.mexico.lonMin - 1], [CONFIG.mexico.latMax + 1, CONFIG.mexico.lonMax + 1]];
const mapa = L.map('mapa', { preferCanvas: true, maxBounds: LIMITES, maxBoundsViscosity: 1, minZoom: 5 }).setView([23.6, -102.5], 5);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', { attribution: 'Tiles © Esri' }).addTo(mapa);

const capaArea = new L.FeatureGroup().addTo(mapa);
const capaPuntos = L.layerGroup().addTo(mapa);

mapa.addControl(new L.Control.Draw({
  draw: { polygon: false, polyline: false, circle: false, marker: false, circlemarker: false,
          rectangle: { shapeOptions: { color: '#00bbd7', weight: 2 } } },
  edit: false
}));

// Pone las coordenadas en los inputs y (opcional) dibuja el rectángulo
function ponerArea(latMin, latMax, lonMin, lonMax, zoom = true) {
  const M = CONFIG.mexico;   // recorta la región para que nunca salga de México
  latMin = Math.max(latMin, M.latMin); latMax = Math.min(latMax, M.latMax);
  lonMin = Math.max(lonMin, M.lonMin); lonMax = Math.min(lonMax, M.lonMax);
  document.getElementById('lat_min').value = latMin.toFixed(2);
  document.getElementById('lat_max').value = latMax.toFixed(2);
  document.getElementById('lon_min').value = lonMin.toFixed(2);
  document.getElementById('lon_max').value = lonMax.toFixed(2);
  const M0 = CONFIG.mexico;
  const todoMexico = latMin <= M0.latMin && latMax >= M0.latMax && lonMin <= M0.lonMin && lonMax >= M0.lonMax;
  document.getElementById('region_txt').textContent = todoMexico
    ? '📍 Región: todo México. Todo lo de abajo se calcula solo con la región elegida.'
    : '📍 Región elegida: el rectángulo rojo del mapa. Todo lo de abajo se calcula solo con esa zona.';
  capaArea.clearLayers();
  L.rectangle([[latMin, lonMin], [latMax, lonMax]], { color: '#00bbd7', weight: 2, fillOpacity: 0.08 }).addTo(capaArea);
  if (zoom) mapa.fitBounds([[latMin, lonMin], [latMax, lonMax]]);
}

// Cuando el usuario dibuja un rectángulo
mapa.on(L.Draw.Event.CREATED, e => {
  const b = e.layer.getBounds();
  ponerArea(b.getSouth(), b.getNorth(), b.getWest(), b.getEast());
  actualizarTodo();
});

// Muestra máximo 4000 puntos para que el mapa no se ponga lento
function dibujarPuntos(focos) {
  capaPuntos.clearLayers();
  const paso = Math.ceil(focos.length / 4000) || 1;
  for (let i = 0; i < focos.length; i += paso) {
    const h = focos[i];
    L.circleMarker([h.lat, h.lon], { radius: 2, color: h.sensor === 'VIIRS' ? '#ea580c' : '#7c3aed', weight: 1 }).addTo(capaPuntos);
  }
}

// Botón grande para elegir región: activa el modo dibujo
function activarDibujo() {
  new L.Draw.Rectangle(mapa, { shapeOptions: { color: '#00bbd7', weight: 2 } }).enable();
}
