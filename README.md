# Calendario de Actividad de Quema – México (MODIS + VIIRS)

## Cómo correrlo
1. Abre `index.html` en el navegador (doble clic o Live Server). **No necesita servidor Python.** Requiere internet (librerías por CDN).
2. Sube uno o varios CSV de NASA FIRMS (MODIS y/o VIIRS, de cualquier año).
3. Dibuja un área en el mapa, elige fechas y revisa calendario, comparación de años y KPIs.

> Para comparar años necesitan **más de un año de datos**: los CSV de ejemplo son solo 2025.
> Descarguen 2020–2024 en https://firms.modaps.eosdis.nasa.gov/download/ (Archive) y súbanlos junto con los de 2025.

## Cómo se armonizan MODIS y VIIRS (para explicarlo en la presentación)
1. Se detecta el sensor por sus columnas (`bright_ti4` = VIIRS, `brightness` = MODIS).
2. Se descarta confianza baja (MODIS < 30, VIIRS = `l`).
3. Ambos pasan al mismo formato: fecha, lat, lon, sensor, frp.
4. Se usa una rejilla de ~1 km (0.01°, la resolución de MODIS): **un foco = una celda con fuego en un día**.
   Así los píxeles VIIRS de 375 m (≈4 por celda) no inflan el conteo y Terra/Aqua/VIIRS no se cuentan doble.
- Resultado con los datos 2025: 301,776 filas crudas → 183,280 focos armonizados.
- Límite honesto: VIIRS detecta fuegos más pequeños que MODIS, así que queda una diferencia residual.
  Mejora futura: factor de escala calculado en los años donde ambos sensores se traslapan (2012+).

## Estructura (un archivo por bloque)
| Archivo | Qué hace | Quién |
|---|---|---|
| `js/config.js` | Constantes: tamaño de celda, paletas, límites de México | Pedagoga + cualquiera |
| `js/datos.js` | Carga CSV y armonización | Dev 1 |
| `js/filtros.js` | Filtros por área/fecha, tablas año×mes, KPIs, mediana | Dev 2 |
| `js/mapa.js` | Mapa Leaflet, dibujar rectángulo, puntos | Dev 3 |
| `js/graficos.js` | Calendario, comparación de años, prueba de armonización | Dev 4 |
| `js/app.js` + `index.html` | Botones, eventos, diseño | Dev 5 |
| Pedagoga | Textos en español claro, leyendas, guion de la demo, prueba con usuarios | |

## Ideas para después (por prioridad)
1. Factor de escala MODIS→VIIRS (ver límite arriba).
2. Semáforo de alerta (mes actual vs. mediana) con texto simple para agricultores.
3. Calendario diario estilo "GitHub" para un año.
4. Filtro por FRP (intensidad) y por día/noche.

## Vista semanal y estimación (en la página)
- **Vista:** selector Mensual / Semanal. Semana 1 = días 1–7 del año (52 semanas; el 29–31 dic cae en la 52).
- **Estimación (sección 6):** con los años cargados muestra la mediana, el rango típico (percentiles 25–75) y la
  *probabilidad de alta actividad* = en qué fracción de los años ese periodo estuvo por encima del promedio de su año.
  El semáforo compara el último periodo contra los años anteriores. Confianza: baja (<3 años), media (3–5), alta (6+).
  Es una expectativa histórica, **no** una predicción: no usa clima ni sequía.

## Alerta por correo (`alerta/alerta_correo.py`)
1. Pide una MAP_KEY gratis: https://firms.modaps.eosdis.nasa.gov/api/map_key/
2. En Gmail activa la verificación en 2 pasos y crea una **contraseña de aplicación** (no uses tu contraseña normal).
3. Prueba local (no envía nada):
   `FIRMS_MAP_KEY=tu_clave python alerta/alerta_correo.py --prueba`
   (en Windows PowerShell: `$env:FIRMS_MAP_KEY="tu_clave"; python alerta/alerta_correo.py --prueba`)
4. Para que corra solo cada día: sube el proyecto a GitHub y en Settings → Secrets → Actions crea
   `FIRMS_MAP_KEY`, `CORREO_DE`, `CORREO_CLAVE`, `CORREO_PARA`. El flujo está en `.github/workflows/alerta.yml`.
   Ajusta `REGION` (oeste,sur,este,norte) y `UMBRAL` en ese archivo.
- Nunca pongas claves en el código ni en la página web: quedarían públicas.
