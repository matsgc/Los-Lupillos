import numpy as np
import pandas as pd
from scipy import stats


class FireHarmonizer:
    """
    Armoniza series históricas de MODIS y VIIRS eliminando el salto de 2012
    y calcula percentiles históricos (P10, P50, P90) para detectar temporadas críticas.
    """

    def __init__(self, freq: str = "ME"):
        """
        freq: Frecuencia de agregación temporal ('ME' mensual, 'W' semanal, 'D' diaria).
        """
        self.freq = freq
        self.slope = None
        self.intercept = None
        self.percentiles_df = None

    def preprocess_and_aggregate(self, df: pd.DataFrame, sensor: str) -> pd.Series:
        """Filtra detecciones válidas y agrupa conteos por periodo temporal."""
        data = df.copy()
        data["acq_date"] = pd.to_datetime(data["acq_date"])

        # Filtrar solo presuntos incendios de vegetación (type == 0)
        if "type" in data.columns:
            data = data[data["type"] == 0]

        # Filtro básico de calidad/confianza según sensor
        if sensor.upper() == "MODIS":
            data = data[data["confidence"] >= 50]
        elif sensor.upper() == "VIIRS":
            data = data[data["confidence"].astype(str).str.lower() != "l"]

        # Conteo de focos de calor por periodo
        series = (
            data.set_index("acq_date")
            .resample(self.freq)
            .size()
            .rename(sensor.lower())
        )
        return series

    def fit_and_harmonize(
        self, modis_series: pd.Series, viirs_series: pd.Series, transition_year: int = 2012
    ) -> pd.DataFrame:
        """
        Ajusta la relación entre MODIS y VIIRS usando el periodo de traslape (>= 2012)
        y reconstruye la serie completa sin salto.
        """
        combined = pd.concat([modis_series, viirs_series], axis=1).fillna(0)

        # 1. Periodo de traslape (donde ambos satélites miden simultáneamente)
        overlap = combined[combined.index.year >= transition_year]
        overlap = overlap[(overlap["modis"] > 0) & (overlap["viirs"] > 0)]

        # 2. Ajuste estadístico en escala logarítmica para manejar sesgo y evitar negativos
        log_modis = np.log1p(overlap["modis"].values)
        log_viirs = np.log1p(overlap["viirs"].values)

        res = stats.linregress(log_modis, log_viirs)
        self.slope = res.slope
        self.intercept = res.intercept

        # 3. Proyectar MODIS a escala equivalente VIIRS para toda la historia
        modis_harmonized = np.expm1(
            self.intercept + self.slope * np.log1p(combined["modis"].values)
        )
        combined["modis_harmonized"] = np.maximum(0, modis_harmonized)

        # 4. Construir serie unificada: MODIS armonizado (< 2012) + VIIRS real (>= 2012)
        combined["unified_fires"] = np.where(
            combined.index.year < transition_year,
            combined["modis_harmonized"],
            combined["viirs"],
        )
        return combined

    def compute_historical_percentiles(self, unified_df: pd.DataFrame) -> pd.DataFrame:
        """Calcula P10, P50 y P90 por mes calendario y clasifica temporadas críticas."""
        df = unified_df.copy()
        df["month"] = df.index.month

        # Calcular percentiles históricos por mes usando numpy
        stats_rows = []
        for month, group in df.groupby("month"):
            vals = group["unified_fires"].values
            p10, p50, p90 = np.percentile(vals, [10, 50, 90])
            stats_rows.append({"month": month, "P10": p10, "P50": p50, "P90": p90})

        self.percentiles_df = pd.DataFrame(stats_rows).set_index("month")

        # Cruzar umbrales con la serie histórica para etiquetar anomalías
        df = df.join(self.percentiles_df, on="month")
        df["is_critical_season"] = df["unified_fires"] >= df["P90"]
        df["status"] = np.select(
            [
                df["unified_fires"] >= df["P90"],
                df["unified_fires"] <= df["P10"],
            ],
            ["CRITICA (>P90)", "BAJA (<P10)"],
            default="NORMAL (P10-P90)",
        )
        return df