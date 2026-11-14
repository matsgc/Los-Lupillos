cat << 'EOF' > INTEGRACION_ROL4.md
# Guía de Integración — Rol 4 (`services/charts.py`)

Este módulo entrega las visualizaciones interactivas en Plotly (heatmap de 365 días × años y comparativa *Crudo vs. Armonizado*) junto con las métricas resumen listas para incrustar en Django y Tailwind CSS.

---

## 1. Contrato de datos (Rol 1 y Rol 2 → Rol 4)

Las funciones de `services/charts.py` esperan recibir:

1. **`df` (`pandas.DataFrame`)** con al menos estas tres columnas:
   * `fecha`: fecha del registro (`datetime` o `str` convertible con `pd.to_datetime`).
   * `conteo_crudo`: conteo diario original sin corregir (MODIS + VIIRS).
   * `conteo_armonizado`: conteo diario ajustado por `services/harmonizer.py`.
2. **`percentiles` (`dict`, opcional)** calculado por `services/harmonizer.py`:
   ```python
   percentiles = {"p10": 120.0, "p50": 320.0, "p90": 850.0}