"""
ALERTA POR CORREO – focos de calor activos en una región de México
-------------------------------------------------------------------
Qué hace (cada vez que se ejecuta):
  1. Pide a NASA FIRMS los focos de los últimos días (VIIRS y MODIS) en tu región.
  2. Los armoniza igual que la página web (confianza baja fuera, 1 foco por celda de ~1 km por día).
  3. Si hay MÁS focos que el umbral, te manda un correo con el resumen. Si no, no manda nada.

Solo usa la librería estándar de Python (no hay que instalar nada).
Uso:   python alerta_correo.py            -> envía el correo si se pasa el umbral
       python alerta_correo.py --prueba   -> solo muestra el correo en pantalla, no lo envía
"""
import csv, io, os, smtplib, sys, urllib.error, urllib.request
from email.message import EmailMessage

# ============ BLOQUE 1: CONFIGURACIÓN ============
# Región: oeste, sur, este, norte (por defecto, Yucatán). Cámbiala con la variable REGION.
REGION = os.environ.get("REGION", "-90.5,19.5,-87.0,21.7")
UMBRAL = int(os.environ.get("UMBRAL", "20"))        # focos en el periodo para mandar alerta
DIAS = int(os.environ.get("DIAS", "2"))             # días UTC a consultar (hoy + anteriores). FIRMS permite 1 a 5.
# OJO: con DIAS=1 solo se pide el día UTC en curso; si apenas empezó, casi no habrá datos.
CELDA = 0.01                                        # ~1 km, igual que la página web
FUENTES = ["VIIRS_NOAA20_NRT", "VIIRS_SNPP_NRT", "MODIS_NRT"]

# Secretos: NUNCA los escribas en el código. Se leen del entorno (ver README).
MAP_KEY = os.environ.get("FIRMS_MAP_KEY", "").strip().strip("'\"")   # quita espacios y comillas sobrantes
CORREO_DE = os.environ.get("CORREO_DE", "")         # tu cuenta que envía (ej. Gmail)
CORREO_CLAVE = os.environ.get("CORREO_CLAVE", "")   # "contraseña de aplicación", no la normal
CORREO_PARA = os.environ.get("CORREO_PARA", "")     # destinatarios, separados por coma

# ============ BLOQUE 2: DESCARGAR DATOS DE FIRMS ============
def descargar(fuente):
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{fuente}/{REGION}/{DIAS}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            texto = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:    # mostramos lo que responde FIRMS (sin imprimir tu clave)
        detalle = e.read().decode("utf-8", "ignore")[:200].strip()
        raise RuntimeError(f"HTTP {e.code}. Respuesta de FIRMS: {detalle or '(vacía)'}") from None
    if not texto.startswith("latitude"):   # a veces FIRMS responde 200 con un mensaje de error en texto
        raise RuntimeError(f"Respuesta inesperada de FIRMS: {texto[:200].strip()}")
    return [dict(fila, fuente=fuente) for fila in csv.DictReader(io.StringIO(texto))]

# ============ BLOQUE 3: ARMONIZAR (misma lógica que datos.js) ============
def confianza_ok(fila):
    c = str(fila.get("confidence", "")).lower()
    if c.isdigit():                      # MODIS: número 0-100
        return int(c) >= 30
    return not c.startswith("l")         # VIIRS: l / n / h

def armonizar(filas):
    vistas, focos = set(), []
    for f in filas:
        if not confianza_ok(f) or f.get("type", "0") not in ("0", ""):
            continue                     # (el tipo solo viene en algunos archivos)
        lat, lon = float(f["latitude"]), float(f["longitude"])
        clave = (f["acq_date"], round(lat / CELDA), round(lon / CELDA))
        if clave in vistas:
            continue                     # ya había un foco en esa celda ese día
        vistas.add(clave)
        focos.append({"fecha": f["acq_date"], "lat": lat, "lon": lon,
                      "frp": float(f.get("frp") or 0), "fuente": f["fuente"]})
    return focos

# ============ BLOQUE 4: ARMAR EL CORREO ============
def armar_texto(focos):
    top = sorted(focos, key=lambda x: x["frp"], reverse=True)[:10]
    lineas = [f"Se detectaron {len(focos)} focos de calor (armonizados) en los últimos {DIAS} días (UTC)",
              f"en la región {REGION} (oeste,sur,este,norte). Umbral de alerta: {UMBRAL}.", "",
              "Los 10 más intensos (potencia FRP en MW):"]
    for f in top:
        lineas.append(f"- FRP {f['frp']:.1f} | {f['fecha']} | {f['fuente']} | "
                      f"https://www.google.com/maps?q={f['lat']},{f['lon']}")
    lineas += ["", "Nota: un foco es una anomalía térmica vista por satélite; puede ser incendio forestal,",
               "quema agrícola u otra fuente de calor. Confirma con autoridades locales antes de actuar."]
    return "\n".join(lineas)

def enviar(texto, n):
    msg = EmailMessage()
    msg["Subject"] = f"🔥 Alerta de incendios: {n} focos en {DIAS} días"
    msg["From"], msg["To"] = CORREO_DE, CORREO_PARA
    msg.set_content(texto)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:   # para otro proveedor, cambia el host
        servidor.login(CORREO_DE, CORREO_CLAVE)
        servidor.send_message(msg)

# ============ BLOQUE 5: PROGRAMA PRINCIPAL ============
def main():
    prueba = "--prueba" in sys.argv
    if not MAP_KEY:
        sys.exit("Falta FIRMS_MAP_KEY (pide una gratis en https://firms.modaps.eosdis.nasa.gov/api/map_key/)")
    print(f"Clave leída: {len(MAP_KEY)} caracteres (una MAP_KEY de FIRMS suele tener 32). Región: {REGION}")
    filas = []
    for fuente in FUENTES:
        try:
            nuevas = descargar(fuente)
            print(f"  {fuente}: {len(nuevas)} filas")
            filas += nuevas
        except Exception as e:           # si una fuente falla, seguimos con las demás
            print(f"Aviso: no se pudo leer {fuente}: {e}")
    focos = armonizar(filas)
    print(f"{len(filas)} filas crudas -> {len(focos)} focos armonizados (umbral {UMBRAL})")
    if len(focos) < UMBRAL:
        print("Por debajo del umbral: no se envía correo.")
        return
    texto = armar_texto(focos)
    if prueba:
        print("\n--- CORREO (modo prueba, no se envió) ---\n" + texto)
    else:
        enviar(texto, len(focos))
        print("Correo enviado.")

if __name__ == "__main__":
    main()
