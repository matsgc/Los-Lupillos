// ============ BLOQUE 0: CONFIGURACIÓN ============
// Todo lo que se pueda querer ajustar vive aquí.
const CONFIG = {
  celda: 0.01,   // tamaño de celda de armonización en grados (~1 km = resolución de MODIS)
  mexico: { latMin: 14, latMax: 33.5, lonMin: -119.5, lonMax: -85.5 },
  meses: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
  diasInicioMes: [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334],   // para rotular el calendario semanal
  paletas: {
    fuego: [[0,'#fff7ec'],[0.25,'#fdd49e'],[0.5,'#fc8d59'],[0.75,'#d7301f'],[1,'#7f0000']],
    dalt: [[0,'#fee838'],[0.25,'#c4b56c'],[0.5,'#7c7b78'],[0.75,'#35456c'],[1,'#00224e']]   // apta para daltonismo
  }
};
