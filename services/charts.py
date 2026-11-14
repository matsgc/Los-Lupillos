import numpy as np
import pandas as pd
import plotly.graph_objects as go

MESES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _mensaje_sin_datos(texto: str) -> str:
    """Contenedor limpio compatible con Tailwind CSS si un filtro queda vacío."""
    return (
        '<div class="flex items-center justify-center h-64 rounded-xl border '
        'border-dashed border-slate-300 bg-slate-50 text-slate-500 text-sm p-6 text-center">'
        f"{texto}"
        "</div>"
    )


def calcular_resumen_kpis(df: pd.DataFrame) -> dict[str, str | float]:
    """
    Calcula las 3 tarjetas de métricas clave para la cabecera del dashboard (Rol 5):
    1. Total de focos armonizados.
    2. Día y año récord histórico.
    3. Variación porcentual del último año completo frente a la mediana anual.
    """
    if df is None or df.empty:
        return {
            "total_armonizado": 0,
            "record_fecha": "Sin datos",
            "record_valor": 0,
            "anomalia_ultimo_anio_pct": 0.0,
        }

    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    datos["anio"] = datos["fecha"].dt.year

    total = float(datos["conteo_armonizado"].sum())

    # Día récord histórico
    idx_max = datos["conteo_armonizado"].idxmax()
    fila_max = datos.loc[idx_max]
    f_max = fila_max["fecha"]
    record_fecha = f"{f_max.day:02d} {MESES_ES[f_max.month]} {f_max.year}"
    record_valor = float(fila_max["conteo_armonizado"])

    # Anomalía del último año registrado vs. mediana histórica anual
    por_anio = datos.groupby("anio")["conteo_armonizado"].sum()
    mediana_anual = float(por_anio.median())
    ultimo_anio = int(por_anio.index.max())
    valor_ultimo = float(por_anio.loc[ultimo_anio])

    anomalia_pct = (
        ((valor_ultimo - mediana_anual) / mediana_anual) * 100.0
        if mediana_anual > 0
        else 0.0
    )

    return {
        "total_armonizado": round(total, 1),
        "record_fecha": record_fecha,
        "record_valor": round(record_valor, 1),
        "ultimo_anio": ultimo_anio,
        "anomalia_ultimo_anio_pct": round(anomalia_pct, 1),
    }


def generar_heatmap_calendario(
    df: pd.DataFrame,
    columna_valor: str = "conteo_armonizado",
    modo_daltonico: bool = False,
    incluir_plotlyjs: bool | str = False,
) -> str:
    """
    Construye el heatmap interactivo de 365 días x años con soporte para
    paleta estándar de fuego o paleta accesible para daltonismo (Cividis).
    """
    if df is None or df.empty:
        return _mensaje_sin_datos("No hay focos de calor registrados para los filtros seleccionados.")

    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    datos["anio"] = datos["fecha"].dt.year
    datos["dia_anio"] = datos["fecha"].dt.day_of_year

    datos = datos[datos["dia_anio"] <= 365]

    matriz = datos.pivot_table(
        index="anio",
        columns="dia_anio",
        values=columna_valor,
        aggfunc="sum",
        fill_value=0,
    ).reindex(columns=range(1, 366), fill_value=0)

    fechas_ref = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    etiquetas_dias = [f"{f.day:02d} {MESES_ES[f.month]}" for f in fechas_ref]
    customdata = np.tile(etiquetas_dias, (len(matriz.index), 1))

    if modo_daltonico:
        escala_color = [
            [0.00, "#f1f5f9"],
            [0.01, "#00204c"],
            [0.35, "#414d6b"],
            [0.70, "#bcaf6f"],
            [1.00, "#ffe945"],
        ]
    else:
        escala_color = [
            [0.00, "#f1f5f9"],
            [0.01, "#fef08a"],
            [0.30, "#fb923c"],
            [0.65, "#dc2626"],
            [1.00, "#7f1d1d"],
        ]

    dias_inicio_mes = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    nombres_meses = list(MESES_ES.values())

    fig = go.Figure(
        data=go.Heatmap(
            z=matriz.values,
            x=list(matriz.columns),
            y=list(matriz.index),
            customdata=customdata,
            colorscale=escala_color,
            xgap=1,
            ygap=2,
            colorbar=dict(
                title="Focos",
                thickness=14,
                len=0.85,
            ),
            hovertemplate=(
                "<b>%{customdata} de %{y}</b> (Día %{x})<br>"
                "Focos armonizados: <b>%{z:.1f}</b><extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text=(
                "Calendario Histórico de Focos de Calor (365 Días × Años)"
                "<br><span style='font-size:12px;color:#64748b;'>"
                "Celdas grises = 0 focos | Las zonas intensas identifican la temporada crítica de quema"
                "</span>"
            ),
            x=0.01,
            y=0.96,
            yanchor="top",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, system-ui, sans-serif", color="#1e293b"),
        xaxis=dict(
            title="",
            tickmode="array",
            tickvals=dias_inicio_mes,
            ticktext=nombres_meses,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            type="category",
            autorange="reversed",
            showgrid=False,
        ),
        margin=dict(l=55, r=45, t=85, b=40),
        height=470,
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs=incluir_plotlyjs,
        config={
            "responsive": True,
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
        },
    )


def generar_comparacion_crudo_vs_armonizado(
    df: pd.DataFrame,
    percentiles: dict[str, float] | None = None,
    incluir_plotlyjs: bool | str = False,
) -> str:
    """
    Construye la gráfica comparativa 'Crudo vs. Armonizado' explicando la
    diferencia de resolución espacial entre MODIS (1 km) y VIIRS (375 m).
    """
    if df is None or df.empty:
        return _mensaje_sin_datos("Sin datos suficientes para comparar la serie cruda y armonizada.")

    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])

    mensual = (
        datos.set_index("fecha")[["conteo_crudo", "conteo_armonizado"]]
        .resample("ME")
        .sum()
        .reset_index()
    )

    # Calcular anomalía porcentual respecto a la mediana mensual (P50)
    mediana_ref = (
        percentiles["p50"]
        if percentiles and "p50" in percentiles and percentiles["p50"] > 0
        else float(mensual["conteo_armonizado"].median())
    )
    if mediana_ref > 0:
        mensual["anomalia_pct"] = ((mensual["conteo_armonizado"] - mediana_ref) / mediana_ref) * 100.0
    else:
        mensual["anomalia_pct"] = 0.0

    fecha_min = mensual["fecha"].min()
    fecha_max = mensual["fecha"].max()
    fecha_viirs = pd.Timestamp("2012-01-01")

    fig = go.Figure()

    if fecha_max >= fecha_viirs:
        fig.add_vrect(
            x0=fecha_viirs,
            x1=fecha_max,
            fillcolor="#fef3c7",
            opacity=0.35,
            layer="below",
            line_width=0,
            annotation_text="Era VIIRS (375 m — Mayor resolución)",
            annotation_position="top right",
            annotation_font=dict(size=11, color="#b45309"),
            annotation_bgcolor="rgba(255, 251, 235, 0.85)",
        )

    if fecha_min < fecha_viirs:
        fig.add_annotation(
            x=fecha_min + (fecha_viirs - fecha_min) / 2,
            y=0.98,
            yref="paper",
            text="Era MODIS (1 km)",
            showarrow=False,
            font=dict(size=11, color="#64748b"),
            bgcolor="rgba(255, 255, 255, 0.85)",
        )

    fig.add_trace(
        go.Scatter(
            x=mensual["fecha"],
            y=mensual["conteo_crudo"],
            mode="lines",
            name="Crudo (Sin corregir)",
            line=dict(color="#94a3b8", width=1.8, dash="dot"),
            hovertemplate="Crudo: <b>%{y:.0f}</b> focos<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=mensual["fecha"],
            y=mensual["conteo_armonizado"],
            customdata=mensual["anomalia_pct"],
            mode="lines",
            name="Armonizado (Escala equivalente 1 km)",
            line=dict(color="#dc2626", width=2.6),
            fill="tozeroy",
            fillcolor="rgba(220, 38, 38, 0.08)",
            hovertemplate=(
                "Armonizado: <b>%{y:.1f}</b> focos<br>"
                "Anomalía vs. mediana: <b>%{customdata:+.1f}%</b><extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=fecha_viirs,
        line_width=1.5,
        line_dash="dash",
        line_color="#d97706",
    )

    if percentiles:
        if "p90" in percentiles:
            fig.add_hline(
                y=percentiles["p90"],
                line_dash="dash",
                line_color="#7f1d1d",
                annotation_text=f"Umbral Crítico P90 ({percentiles['p90']:.0f})",
                annotation_position="top left",
                annotation_font=dict(size=11, color="#7f1d1d"),
                annotation_bgcolor="rgba(255, 255, 255, 0.88)",
                annotation_borderpad=3,
            )
        if "p50" in percentiles:
            fig.add_hline(
                y=percentiles["p50"],
                line_dash="dot",
                line_color="#475569",
                annotation_text=f"Mediana Histórica P50 ({percentiles['p50']:.0f})",
                annotation_position="bottom left",
                annotation_font=dict(size=11, color="#475569"),
                annotation_bgcolor="rgba(255, 255, 255, 0.88)",
                annotation_borderpad=3,
            )

    fig.update_layout(
        title=dict(
            text=(
                "Corrección del Salto Satelital (2012): Crudo vs. Armonizado"
                "<br><span style='font-size:12px;color:#64748b;'>"
                "Ajusta la resolución de VIIRS (375 m) a la escala histórica de MODIS (1 km) para evitar falsos picos"
                "</span>"
            ),
            x=0.01,
            y=0.96,
            yanchor="top",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, system-ui, sans-serif", color="#1e293b"),
        xaxis=dict(
            title="",
            showgrid=False,
            rangeselector=dict(
                x=0.0,
                xanchor="left",
                y=1.03,
                yanchor="bottom",
                bgcolor="#f1f5f9",
                activecolor="#dc2626",
                font=dict(size=11),
                buttons=[
                    dict(count=5, label="Últimos 5 años", step="year", stepmode="backward"),
                    dict(count=15, label="15 años", step="year", stepmode="backward"),
                    dict(step="all", label="Todo el historial"),
                ],
            ),
        ),
        yaxis=dict(
            title="Focos mensuales",
            gridcolor="#f1f5f9",
            zeroline=False,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(l=60, r=45, t=125, b=65),
        height=480,
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs=incluir_plotlyjs,
        config={
            "responsive": True,
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
        },
    )


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    fechas = pd.date_range("2005-01-01", "2024-12-31", freq="D")
    dia_anio = fechas.day_of_year

    estacionalidad = np.exp(-0.5 * ((dia_anio - 115) / 25) ** 2) * 40
    base_armonizada = np.maximum(0, estacionalidad + rng.normal(3, 4, size=len(fechas)))
    base_armonizada = np.where(base_armonizada < 2.5, 0, base_armonizada)

    factor_viirs = np.where(fechas.year >= 2012, 2.8, 1.0)
    base_cruda = base_armonizada * factor_viirs

    df_prueba = pd.DataFrame(
        {
            "fecha": fechas,
            "conteo_crudo": base_cruda,
            "conteo_armonizado": base_armonizada,
        }
    )

    kpis = calcular_resumen_kpis(df_prueba)
    html_hm_fuego = generar_heatmap_calendario(df_prueba, modo_daltonico=False)
    html_hm_dalt = generar_heatmap_calendario(df_prueba, modo_daltonico=True)
    html_cp = generar_comparacion_crudo_vs_armonizado(
        df_prueba,
        percentiles={"p50": 320, "p90": 850},
    )

    pagina_preview = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview Rol 4 - Monitor de Focos de Calor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
</head>
<body class="bg-slate-100 text-slate-800 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
        <header class="flex flex-wrap items-center justify-between gap-4 bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <div>
                <h1 class="text-xl font-bold text-slate-900">Monitor Histórico de Focos de Calor</h1>
                <p class="text-sm text-slate-500">Vista previa de visualizaciones temporales (Rol 4)</p>
            </div>
            <button onclick="alternarPaleta()" id="btn-paleta"
                class="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-900 text-white hover:bg-slate-700 transition">
                Cambiar a Modo Daltónico (Cividis)
            </button>
        </header>

        <!-- Tarjetas KPI -->
        <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Total Focos Armonizados</p>
                <p class="text-2xl font-bold text-slate-900 mt-1">{kpis['total_armonizado']:,.0f}</p>
                <p class="text-xs text-slate-400 mt-1">Serie unificada 2005–2024</p>
            </div>
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Día Récord Histórico</p>
                <p class="text-2xl font-bold text-red-600 mt-1">{kpis['record_fecha']}</p>
                <p class="text-xs text-slate-400 mt-1">{kpis['record_valor']:.1f} focos en un solo día</p>
            </div>
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Anomalía ({kpis['ultimo_anio']}) vs. Mediana</p>
                <p class="text-2xl font-bold text-amber-600 mt-1">{kpis['anomalia_ultimo_anio_pct']:+.1f}%</p>
                <p class="text-xs text-slate-400 mt-1">Respecto al comportamiento histórico</p>
            </div>
        </section>

        <!-- Heatmap con selector de accesibilidad -->
        <section class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <div id="hm-fuego">{html_hm_fuego}</div>
            <div id="hm-dalt" class="hidden">{html_hm_dalt}</div>
        </section>

        <!-- Gráfica comparativa -->
        <section class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            {html_cp}
        </section>
    </div>

    <script>
        let daltActivo = false;
        function alternarPaleta() {{
            daltActivo = !daltActivo;
            document.getElementById('hm-fuego').classList.toggle('hidden', daltActivo);
            document.getElementById('hm-dalt').classList.toggle('hidden', !daltActivo);
            document.getElementById('btn-paleta').textContent = daltActivo
                ? 'Cambiar a Modo Estándar (Fuego)'
                : 'Cambiar a Modo Daltónico (Cividis)';
            window.dispatchEvent(new Event('resize'));
        }}
    </script>
</body>
</html>"""

    with open("preview_rol4.html", "w", encoding="utf-8") as f:
        f.write(pagina_preview)