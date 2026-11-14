import numpy as np
import pandas as pd
import plotly.graph_objects as go


def generar_heatmap_calendario(
    df: pd.DataFrame,
    columna_valor: str = "conteo_armonizado",
    incluir_plotlyjs: bool | str = False,
) -> str:
    """
    Construye el heatmap interactivo de 365 días x años y devuelve el fragmento HTML.
    """
    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    datos["anio"] = datos["fecha"].dt.year
    datos["dia_anio"] = datos["fecha"].dt.dayofyear

    # Mantener matriz estricta de 365 días (descarta día 366 en años bisiestos)
    datos = datos[datos["dia_anio"] <= 365]

    matriz = datos.pivot_table(
        index="anio",
        columns="dia_anio",
        values=columna_valor,
        aggfunc="sum",
        fill_value=0,
    ).reindex(columns=range(1, 366), fill_value=0)

    dias_inicio_mes = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    nombres_meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=matriz.values,
            x=list(matriz.columns),
            y=list(matriz.index),
            colorscale="YlOrRd",
            colorbar=dict(title="Focos"),
            hovertemplate=(
                "<b>Año:</b> %{y}<br>"
                "<b>Día del año:</b> %{x}<br>"
                "<b>Focos / Intensidad:</b> %{z:.1f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="Calendario Histórico de Focos de Calor (365 Días × Años)",
        xaxis=dict(
            title="Mes / Día del año",
            tickmode="array",
            tickvals=dias_inicio_mes,
            ticktext=nombres_meses,
            showgrid=False,
        ),
        yaxis=dict(
            title="Año",
            type="category",
            autorange="reversed",
        ),
        margin=dict(l=60, r=20, t=50, b=50),
        height=450,
    )

    return fig.to_html(full_html=False, include_plotlyjs=incluir_plotlyjs)


def generar_comparacion_crudo_vs_armonizado(
    df: pd.DataFrame,
    percentiles: dict[str, float] | None = None,
    incluir_plotlyjs: bool | str = False,
) -> str:
    """
    Construye la gráfica comparativa 'Crudo vs. Armonizado' mostrando la eliminación
    del salto de 2012 entre MODIS y VIIRS y los percentiles históricos (P10, P50, P90).
    """
    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])

    mensual = (
        datos.set_index("fecha")[["conteo_crudo", "conteo_armonizado"]]
        .resample("ME")
        .sum()
        .reset_index()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=mensual["fecha"],
            y=mensual["conteo_crudo"],
            mode="lines",
            name="Crudo (MODIS + VIIRS)",
            line=dict(color="#94a3b8", width=1.8, dash="dot"),
            hovertemplate="Fecha: %{x|%Y-%m}<br>Crudo: %{y:.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=mensual["fecha"],
            y=mensual["conteo_armonizado"],
            mode="lines",
            name="Armonizado",
            line=dict(color="#dc2626", width=2.5),
            hovertemplate="Fecha: %{x|%Y-%m}<br>Armonizado: %{y:.1f}<extra></extra>",
        )
    )

    fig.add_vline(
        x="2012-01-01",
        line_width=1.5,
        line_dash="dash",
        line_color="#f59e0b",
    )
    fig.add_annotation(
        x="2012-01-01",
        y=1.02,
        yref="paper",
        text="Inicio VIIRS (Salto 2012)",
        showarrow=False,
        font=dict(color="#d97706", size=11),
    )

    if percentiles:
        if "p90" in percentiles:
            fig.add_hline(
                y=percentiles["p90"],
                line_dash="dash",
                line_color="#7f1d1d",
                annotation_text=f"P90 Crítico ({percentiles['p90']:.0f})",
                annotation_position="top left",
            )
        if "p50" in percentiles:
            fig.add_hline(
                y=percentiles["p50"],
                line_dash="dot",
                line_color="#475569",
                annotation_text=f"P50 Mediana ({percentiles['p50']:.0f})",
                annotation_position="bottom left",
            )

    fig.update_layout(
        title="Comparación Histórica: Serie Cruda vs. Armonizada",
        xaxis_title="Año",
        yaxis_title="Focos de calor mensuales",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=65, b=50),
        height=420,
    )

    return fig.to_html(full_html=False, include_plotlyjs=incluir_plotlyjs)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    fechas = pd.date_range("2005-01-01", "2024-12-31", freq="D")
    dia_anio = fechas.dayofyear

    estacionalidad = np.exp(-0.5 * ((dia_anio - 115) / 25) ** 2) * 40
    base_armonizada = np.maximum(0, estacionalidad + rng.normal(5, 4, size=len(fechas)))

    # Simula el salto de 2012 al entrar VIIRS en los datos sin armonizar
    factor_viirs = np.where(fechas.year >= 2012, 2.8, 1.0)
    base_cruda = base_armonizada * factor_viirs

    df_prueba = pd.DataFrame(
        {
            "fecha": fechas,
            "conteo_crudo": base_cruda,
            "conteo_armonizado": base_armonizada,
        }
    )

    with open("test_heatmap.html", "w", encoding="utf-8") as f:
        f.write(generar_heatmap_calendario(df_prueba, incluir_plotlyjs="cdn"))

    with open("test_comparacion.html", "w", encoding="utf-8") as f:
        f.write(
            generar_comparacion_crudo_vs_armonizado(
                df_prueba,
                percentiles={"p50": 450, "p90": 950},
                incluir_plotlyjs="cdn",
            )
        )

    print("Pruebas generadas: test_heatmap.html y test_comparacion.html")