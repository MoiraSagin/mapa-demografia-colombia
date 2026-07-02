import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title="Mapa demográfico Colombia",
    layout="wide"
)

st.title("Mapa demográfico municipal de Colombia")
st.markdown("Crecimiento vegetativo estimado a partir de nacimientos menos defunciones.")
st.markdown("""
<style>
.js-plotly-plot {
    touch-action: pan-x pan-y;
}
</style>
""", unsafe_allow_html=True)
# =========================
# Cargar datos
# =========================

@st.cache_data
def cargar_datos():
    saldo = pd.read_excel("data/saldo_final.xlsx")

    geo = gpd.read_file("data/colombia_2018_simplified.topojson")

    saldo["codigo_municipio"] = (
        saldo["codigo_municipio"]
        .astype(str)
        .str.zfill(5)
    )

    geo["MPIO_CCNCT"] = (
        geo["MPIO_CCNCT"]
        .astype(str)
        .str.zfill(5)
    )

    return saldo, geo


saldo, geo = cargar_datos()

# =========================
# Filtros
# =========================

st.sidebar.header("Filtros")

anio_seleccionado = st.sidebar.selectbox(
    "Año",
    sorted(saldo["anio"].unique())
)
saldo["departamento_nombre"] = (
    saldo["departamento"]
    .astype(str)
    .str.replace(r"^\d+_", "", regex=True)
)

departamentos = ["Todos"] + sorted(saldo["departamento_nombre"].dropna().unique())

departamento_seleccionado = st.sidebar.selectbox(
    "Departamento",
    departamentos
)
variables = {
    "Crecimiento vegetativo (%)": "crecimiento_pct",
    "Saldo natural": "saldo_natural",
    "Población vegetativa": "poblacion_vegetativa",
    "Nacimientos": "nacimientos",
    "Defunciones": "defunciones"
}

variable_nombre = st.sidebar.selectbox(
    "Variable para visualizar",
    list(variables.keys())
)

variable = variables[variable_nombre]

if variable == "crecimiento_pct":
    escala = "RdYlGn"
elif variable == "saldo_natural":
    escala = "Blues"
elif variable == "poblacion_vegetativa":
    escala = "Viridis"
elif variable == "nacimientos":
    escala = "YlOrRd"
else:
    escala = "Reds"

saldo_filtrado = saldo[saldo["anio"] == anio_seleccionado]

if departamento_seleccionado != "Todos":
    saldo_filtrado = saldo_filtrado[
        saldo_filtrado["departamento_nombre"] == departamento_seleccionado
    ]

if departamento_seleccionado == "Todos":
    geo_filtrado = geo
else:
    geo_filtrado = geo[
        geo["DPTO_CNMBR"].str.upper() == departamento_seleccionado.upper()
    ]

mapa = geo_filtrado.merge(
    saldo_filtrado,
    left_on="MPIO_CCNCT",
    right_on="codigo_municipio",
    how="left"
)

variables_log = ["poblacion_vegetativa", "nacimientos", "defunciones"]

if variable in variables_log:
    mapa["valor_mapa"] = np.log10(mapa[variable].fillna(0) + 1)
    color_mapa = "valor_mapa"
    titulo_escala = variable_nombre + " (escala log)"
else:
    mapa["valor_mapa"] = mapa[variable]
    color_mapa = "valor_mapa"
    titulo_escala = variable_nombre

# =========================
# Métricas generales dinámicas
# =========================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Año", anio_seleccionado)
col2.metric("Municipios con datos", saldo_filtrado["codigo_municipio"].nunique())

if variable == "nacimientos":
    col3.metric("Nacimientos totales", f"{saldo_filtrado['nacimientos'].sum():,.0f}")
    col4.metric("Promedio municipal", f"{saldo_filtrado['nacimientos'].mean():,.0f}")

elif variable == "defunciones":
    col3.metric("Defunciones totales", f"{saldo_filtrado['defunciones'].sum():,.0f}")
    col4.metric("Promedio municipal", f"{saldo_filtrado['defunciones'].mean():,.0f}")

elif variable == "saldo_natural":
    col3.metric("Saldo natural total", f"{saldo_filtrado['saldo_natural'].sum():,.0f}")
    col4.metric("Promedio municipal", f"{saldo_filtrado['saldo_natural'].mean():,.0f}")

elif variable == "poblacion_vegetativa":
    col3.metric("Población vegetativa total", f"{saldo_filtrado['poblacion_vegetativa'].sum():,.0f}")
    col4.metric("Promedio municipal", f"{saldo_filtrado['poblacion_vegetativa'].mean():,.0f}")

else:
    col3.metric("Saldo natural total", f"{saldo_filtrado['saldo_natural'].sum():,.0f}")
    col4.metric("Crecimiento promedio", f"{saldo_filtrado['crecimiento_pct'].mean():.2f}%")
# =========================
# Escala de color
# =========================

# =========================
# Escala de color
# =========================

if variable in ["crecimiento_pct", "saldo_natural"]:

    min_val = mapa[variable].min()
    max_val = mapa[variable].max()

    limite = max(abs(min_val), abs(max_val))

    escala = [
        [0.00, "#8B0000"],
        [0.25, "#FF6B6B"],
        [0.50, "#F7F7F7"],
        [0.75, "#90EE90"],
        [1.00, "#006400"],
    ]

    rango_color = [-limite, limite]

elif variable == "defunciones":

    escala = "Reds"
    rango_color = None

elif variable == "nacimientos":

    escala = "Greens"
    rango_color = None

elif variable == "poblacion_vegetativa":

    escala = "Greens"
    rango_color = None


# =========================
# Mapa solo Colombia
# =========================
hover_templates = {
    "crecimiento_pct": (
        "<b>%{customdata[0]}</b><br>"
        "Departamento: %{customdata[1]}<br>"
        "Crecimiento vegetativo: %{customdata[2]:.2f}%<extra></extra>"
    ),

    "saldo_natural": (
        "<b>%{customdata[0]}</b><br>"
        "Departamento: %{customdata[1]}<br>"
        "Saldo natural: %{customdata[2]:,.0f}<extra></extra>"
    ),

    "poblacion_vegetativa": (
        "<b>%{customdata[0]}</b><br>"
        "Departamento: %{customdata[1]}<br>"
        "Población vegetativa: %{customdata[2]:,.0f}<extra></extra>"
    ),

    "nacimientos": (
        "<b>%{customdata[0]}</b><br>"
        "Departamento: %{customdata[1]}<br>"
        "Nacimientos: %{customdata[2]:,.0f}<extra></extra>"
    ),

    "defunciones": (
        "<b>%{customdata[0]}</b><br>"
        "Departamento: %{customdata[1]}<br>"
        "Defunciones: %{customdata[2]:,.0f}<extra></extra>"
    )
}

fig = px.choropleth(
    mapa,
    geojson=mapa.__geo_interface__,
    locations=mapa.index,
    color=color_mapa,
    hover_name="MPIO_CNMBR",
    custom_data=["MPIO_CNMBR", "DPTO_CNMBR", variable],
    color_continuous_scale=escala,
    range_color=rango_color,
)

fig.update_geos(
    fitbounds="locations",
    visible=False
)

if variable in ["poblacion_vegetativa", "nacimientos", "defunciones"]:
    tick_vals = [0, 1, 2, 3, 4, 5, 6, 7]
    tick_text = [
        "0",
        "10",
        "100",
        "1.000",
        "10.000",
        "100.000",
        "1.000.000",
        "10.000.000"
    ]
else:
    tick_vals = None
    tick_text = None

fig.update_layout(
    margin={"r": 0, "t": 20, "l": 0, "b": 0},
    coloraxis_colorbar=dict(
        title=titulo_escala,
        tickvals=tick_vals,
        ticktext=tick_text
    ),
    dragmode="pan"
)

fig.update_traces(
    marker_line_width=0.15,
    marker_line_color="black"
)
fig.update_traces(
    hovertemplate=hover_templates[variable]
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True
    }
)
# =========================
# Tabla
# =========================

st.subheader("Datos municipales")

tabla = saldo_filtrado[
    [
        "departamento",
        "municipio",
        "anio",
        "nacimientos",
        "defunciones",
        "saldo_natural",
        "poblacion_vegetativa",
        "crecimiento_pct"
    ]
].sort_values(variable, ascending=False)
tabla["departamento"] = (
    tabla["departamento"]
    .str.replace(r"^\d+_", "", regex=True)
)
tabla = tabla.rename(columns={
    "departamento": "Departamento",
    "municipio": "Municipio",
    "anio": "Año",
    "nacimientos": "Nacimientos",
    "defunciones": "Defunciones",
    "saldo_natural": "Saldo natural",
    "poblacion_vegetativa": "Población vegetativa",
    "crecimiento_pct": "Crecimiento (%)"
})
tabla["Nacimientos"] = tabla["Nacimientos"].map("{:,.0f}".format)
tabla["Defunciones"] = tabla["Defunciones"].map("{:,.0f}".format)
tabla["Saldo natural"] = tabla["Saldo natural"].map("{:,.0f}".format)
tabla["Población vegetativa"] = tabla["Población vegetativa"].map("{:,.0f}".format)
tabla["Crecimiento (%)"] = tabla["Crecimiento (%)"].map("{:.2f}".format)
if variable == "nacimientos":
    columnas = [
        "Departamento",
        "Municipio",
        "Año",
        "Nacimientos"
    ]

elif variable == "defunciones":
    columnas = [
        "Departamento",
        "Municipio",
        "Año",
        "Defunciones"
    ]

elif variable == "saldo_natural":
    columnas = [
        "Departamento",
        "Municipio",
        "Año",
        "Saldo natural"
    ]

elif variable == "poblacion_vegetativa":
    columnas = [
        "Departamento",
        "Municipio",
        "Año",
        "Población vegetativa"
    ]

else:
    columnas = [
        "Departamento",
        "Municipio",
        "Año",
        "Crecimiento (%)"
    ]

tabla = tabla[columnas]
st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True
)