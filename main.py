from pathlib import Path
import pandas as pd
from services.harmonizer import FireHarmonizer

# Ruta absoluta de la carpeta donde está main.py (/home/davidvergara/Escritorio/nasa)
BASE_DIR = Path(__file__).resolve().parent


def cargar_carpeta_sensor(subruta_en_data: str) -> pd.DataFrame:
    """Busca recursivamente cualquier CSV de México ignorando mayúsculas/minúsculas."""
    carpeta = BASE_DIR / "data" / subruta_en_data

    if not carpeta.exists():
        raise FileNotFoundError(f"La carpeta no existe: {carpeta}")

    # Filtra todos los .csv que contengan 'mexico' en su nombre (sin importar mayúsculas)
    archivos = sorted(
        f for f in carpeta.rglob("*.csv") if "mexico" in f.name.lower()
    )

    if not archivos:
        # Muestra qué hay realmente dentro para ayudarte a ubicar el error si sigue vacío
        contenido = [p.name for p in carpeta.iterdir()]
        raise FileNotFoundError(
            f"No hay CSV de México en: {carpeta}\n"
            f"Contenido encontrado ahí: {contenido}"
        )

    print(f"Uniendo {len(archivos)} archivos desde '{carpeta}'...")
    return pd.concat([pd.read_csv(f) for f in archivos], ignore_index=True)


def main():
    # 1. Cargar datos (si pones "modis" busca en toda data/modis y sus subcarpetas)
    df_modis = cargar_carpeta_sensor("modis_2025_all_countries")
    df_viirs = cargar_carpeta_sensor("viirs-jpss1_2025_all_countries")  # <-- Ajusta al nombre exacto de tu carpeta VIIRS en data/

    print(f"Total registros MODIS: {len(df_modis):,}")
    print(f"Total registros VIIRS: {len(df_viirs):,}")

    # 2. Inicializar y ejecutar armonización
    harmonizer = FireHarmonizer(freq="ME")
    serie_modis = harmonizer.preprocess_and_aggregate(df_modis, sensor="MODIS")
    serie_viirs = harmonizer.preprocess_and_aggregate(df_viirs, sensor="VIIRS")

    serie_unificada = harmonizer.fit_and_harmonize(
        modis_series=serie_modis,
        viirs_series=serie_viirs,
        transition_year=2012
    )

    resultado_final = harmonizer.compute_historical_percentiles(serie_unificada)

    print("\n--- UMBRALES HISTÓRICOS POR MES (P10, P50, P90) ---")
    print(harmonizer.percentiles_df.round(1))

    print("\n--- TEMPORADAS CRÍTICAS DETECTADAS (> P90) ---")
    criticas = resultado_final[resultado_final["is_critical_season"]]
    print(criticas[["modis", "viirs", "unified_fires", "P90", "status"]].tail(12))

    salida = BASE_DIR / "data" / "serie_armonizada_mexico.csv"
    resultado_final.to_csv(salida)
    print(f"\nListo. Archivo guardado en: {salida}")


if __name__ == "__main__":
    main()