"""Aplicación de la parte 2. Ejecutar: streamlit run app.py."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from tws.data import CLIMATE, RAW_FEATURES, feature_names, latitude_band
from tws.inference import parse_csv, predict_frame
from tws.utils import FAMILIES, LABELS, MODELS, RESULTS

st.set_page_config(page_title="Pronóstico del agua", page_icon="💧", layout="wide")
COLORS = {"Random Forest": "#365D92", "XGBoost": "#16756C", "LSTM": "#AD5E2E",
          "Observado": "#182C3D", "Persistencia causal": "#858B94", "Climatología mensual": "#ADABB5"}
VARIABLES = {"TWS_t": "Almacenamiento de agua actual", "target": "Almacenamiento del mes siguiente",
             "SPEI_01_t": "SPEI de 1 mes", "SPEI_03_t": "SPEI de 3 meses", "SPEI_06_t": "SPEI de 6 meses",
             "SPEI_12_t": "SPEI de 12 meses", "SOIL_MOISTURE_t": "Humedad del suelo"}


@st.cache_data
def table(name):
    path = RESULTS / name
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)


@st.cache_data
def json_file(name):
    return json.loads((RESULTS / name).read_text())


@st.cache_data
def input_example():
    if (RESULTS / "ejemplo_entrada.json").exists():
        return json.loads((RESULTS / "ejemplo_entrada.json").read_text())
    frame = pd.read_csv(ROOT / "data/raw/Test.csv")
    near = frame[(frame.lat == 14.5) & (frame.lon == -90.5)]
    selected = near.iloc[-1] if len(near) else frame.iloc[-1]
    return selected.to_dict()


def chart(fig, *, height=380):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=15, r=15, t=40, b=20),
                      font=dict(family="Arial", color="#182C3D"), legend_title_text="")
    if fig.data and getattr(fig.data[0], "x", None) is not None and len(fig.data[0].x):
        first = str(fig.data[0].x[0])
        if len(first) >= 10 and first[4] == "-" and first[7] == "-":
            fig.update_xaxes(tickformat="%Y-%m")
    st.plotly_chart(fig, width="stretch")


def selected_families():
    choice = st.session_state.get("model_choice", "Todos")
    return FAMILIES if choice == "Todos" else tuple(f for f in FAMILIES if LABELS[f] == choice)


def clear_forecast():
    st.session_state.pop("forecast_result", None)


def show_forecast(result):
    st.subheader("Predicción del mes siguiente")
    if len(result) == 1:
        row = result.iloc[0]
        target_date = pd.Timestamp(row.target_time)
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        st.write(f"Mes pronosticado: **{months[target_date.month-1]} de {target_date.year}**")
        columns = st.columns(len(selected_families()))
        for column, family in zip(columns, selected_families()):
            if f"pred_{family}" in result:
                column.metric(LABELS[family], f"{row[f'pred_{family}']:.4f}")
        if row.has_history:
            st.caption(f"Último TWS conocido: {row.last_tws:.4f}. Antigüedad: {int(row.age_months)} meses.")
        else:
            st.caption("La predicción utiliza las covariables disponibles para una celda sin historia previa de TWS.")
    display = result.rename(columns={f"pred_{family}": LABELS[family] for family in FAMILIES})
    visible = ["ID", "target_time", "lat", "lon", *[LABELS[f] for f in selected_families() if LABELS[f] in display]]
    display = display[visible].rename(columns={"target_time": "Mes objetivo", "lat": "Latitud", "lon": "Longitud"})
    st.dataframe(display, hide_index=True, width="stretch", column_config={
        LABELS[family]: st.column_config.NumberColumn(format="%.4f") for family in selected_families()})
    st.download_button("Descargar predicciones", result.to_csv(index=False).encode("utf-8"),
                       file_name="predicciones_tws.csv", mime="text/csv", key="download_prediction")
    st.caption("Resultados en la escala estandarizada del reto. El valor representa almacenamiento de agua y no determina por sí solo una categoría de sequía.")


st.title("Pronóstico del almacenamiento de agua")
st.write("Explora los patrones del agua terrestre y compara las predicciones de Random Forest, XGBoost y una red LSTM para el siguiente mes.")
with st.sidebar:
    st.header("Comparación")
    st.selectbox("Algoritmo", ["Todos", *[LABELS[f] for f in FAMILIES]], key="model_choice", on_change=clear_forecast)
    st.checkbox("Mostrar rendimiento de los modelos", value=True, key="show_performance")
    st.caption("Proyecto 2 · CC3084 Data Science\nUniversidad del Valle de Guatemala")
    st.link_button("Repositorio del proyecto", "https://github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA")

if not (RESULTS / "auditoria.json").exists():
    st.info("Primero prepare los datos siguiendo la guía de ejecución.")
    st.stop()

audit = json_file("auditoria.json")
selection_path = RESULTS / "seleccion_fijada.json"
recommended = LABELS[json_file("seleccion_fijada.json")["recommended_family"]] if selection_path.exists() else "En evaluación"
cols = st.columns(4)
cols[0].metric("Observaciones de entrenamiento", f"{audit['train_rows']:,}")
cols[1].metric("Celdas terrestres", f"{audit['cells']:,}")
cols[2].metric("TWS oculto en Test", f"{audit['test_mask_rate']:.1%}")
cols[3].metric("Selección en validación", recommended)

explore, predict, evaluate = st.tabs(["Explorar datos", "Pronosticar", "Evaluar modelos"])

with explore:
    st.subheader("El agua cambia con la región y con el tiempo")
    sample = table("muestra_exploracion.parquet").copy()
    sample["region"] = latitude_band(sample.lat)
    regions = sorted(sample.region.unique())
    chosen_regions = st.multiselect("Regiones", regions, default=regions, key="explore_regions")
    year_min, year_max = int(sample.time.dt.year.min()), int(sample.time.dt.year.max())
    years = st.slider("Periodo", year_min, year_max, (year_min, year_max), key="explore_years")
    selected = sample[sample.region.isin(chosen_regions) & sample.time.dt.year.between(*years)]
    c1, c2 = st.columns(2)
    with c1:
        variable = st.selectbox("Variable para explorar", list(VARIABLES), format_func=VARIABLES.get, key="variable")
        if len(selected):
            distribution = px.histogram(selected, x=variable, color="region", nbins=60, barmode="overlay", opacity=.65,
                                         labels={variable: VARIABLES[variable]}, title="Distribución de valores")
            distribution.update_yaxes(title_text="Observaciones")
            chart(distribution)
        else:
            st.info("Seleccione al menos una región con observaciones en el periodo.")
    with c2:
        regional = table("series_regionales_eda.csv")
        regional["time"] = pd.to_datetime(regional.time)
        regional = regional[regional.region.isin(chosen_regions) & regional.time.dt.year.between(*years)]
        chart(px.line(regional, x="time", y="mean_target", color="region", markers=True,
                      labels={"time": "Mes de entrada", "mean_target": "TWS del siguiente mes"}, title="Evolución por región"))
    st.caption("La distribución utiliza una muestra fija de 40 000 observaciones. Las series y el mapa resumen todos los registros de entrenamiento. Las métricas de evaluación utilizan todas las filas de la prueba reservada.")
    geo = table("mapa_eda.parquet")
    chart(px.scatter(geo, x="lon", y="lat", color="mean_target", color_continuous_scale="RdBu_r",
                     color_continuous_midpoint=0, hover_data=["std_target", "rows"],
                     labels={"lon": "Longitud", "lat": "Latitud", "mean_target": "TWS promedio"},
                     title="Distribución espacial del almacenamiento"), height=450)
    with st.expander("Características y variables del conjunto limpio"):
        st.write("Una observación representa una celda y un mes. Se conservaron los extremos climáticos y se representaron los faltantes mediante indicadores, sin rellenar con observaciones futuras.")
        dictionary = pd.DataFrame([
            {"Columna": col, "Descripción": VARIABLES.get(col, {"time": "Mes de entrada", "lat": "Latitud en grados", "lon": "Longitud en grados"}.get(col, col)),
             "Uso": "Opcional si está oculto" if col == "TWS_t" else "Entrada"} for col in RAW_FEATURES])
        st.dataframe(dictionary, hide_index=True, width="stretch")
        st.write("Los modelos añaden seis meses de historia, estacionalidad, última observación conocida y antigüedad. Las variables hidrológicas están estandarizadas.")
        st.dataframe(pd.DataFrame({"Variables utilizadas por los modelos": feature_names()}), hide_index=True, width="stretch")
        st.dataframe(selected.head(100), hide_index=True, width="stretch")

with predict:
    st.subheader("Nuevos datos")
    st.write("Ingrese las condiciones de una celda o cargue varias observaciones. Utilice la misma escala estandarizada de los archivos del reto.")
    ready = all((MODELS / "production" / family / "metadata.json").exists() for family in selected_families())
    if not ready:
        st.info("Los modelos seleccionados estarán disponibles al finalizar el entrenamiento.")
    mode = st.radio("Forma de ingreso", ["Formulario", "Archivo CSV"], horizontal=True, key="input_mode", on_change=clear_forecast)
    if mode == "Formulario":
        example = input_example()
        defaults = {"input_date": date(2019, 1, 1), "input_lat": 14.5,
                    "input_lon": -90.5, "input_TWS_t": 0.0, "has_tws": False,
                    **{f"input_{column}": 0.0 for column in CLIMATE}}
        for key, value in defaults.items():
            st.session_state.setdefault(key, value)
        if st.button("Cargar ejemplo real de Test", key="load_example"):
            for col in ["lat", "lon", *CLIMATE]:
                st.session_state[f"input_{col}"] = float(example[col])
            st.session_state["input_date"] = pd.Timestamp(example["time"]).date()
            st.session_state["has_tws"] = not pd.isna(example["TWS_t"])
            st.session_state["input_TWS_t"] = 0.0 if pd.isna(example["TWS_t"]) else float(example["TWS_t"])
            st.session_state.pop("forecast_result", None)
        has_tws = st.checkbox("Conozco el TWS actual", key="has_tws")
        with st.form("prediction_form"):
            a, b, c = st.columns(3)
            with a:
                input_date = st.date_input("Mes de entrada", key="input_date")
                lat = st.number_input("Latitud", min_value=-90.0, max_value=90.0, step=1.0, key="input_lat")
                lon = st.number_input("Longitud", min_value=-180.0, max_value=180.0, step=1.0, key="input_lon")
            with b:
                values = {}
                for column in CLIMATE[:3]:
                    values[column] = st.number_input(VARIABLES[column], step=.1, format="%.4f", key=f"input_{column}")
            with c:
                for column in CLIMATE[3:]:
                    values[column] = st.number_input(VARIABLES[column], step=.1, format="%.4f", key=f"input_{column}")
                tws = st.number_input("TWS actual", step=.1, format="%.4f", key="input_TWS_t", disabled=not has_tws)
            submitted = st.form_submit_button("Predecir", type="primary", disabled=not ready)
        if submitted:
            frame = pd.DataFrame([{**values, "time": input_date, "lat": lat, "lon": lon,
                                   "TWS_t": tws if has_tws else np.nan}])
            try:
                with st.spinner("Calculando las predicciones…"):
                    st.session_state["forecast_result"] = predict_frame(frame, selected_families())
            except (ValueError, FloatingPointError, RuntimeError) as exc:
                st.error(str(exc))
    else:
        template = pd.DataFrame([input_example()])[["ID", *RAW_FEATURES]]
        st.download_button("Descargar CSV de ejemplo", template.to_csv(index=False).encode("utf-8"),
                           file_name="ejemplo_nuevos_datos.csv", mime="text/csv", key="template_csv")
        st.caption("Columnas necesarias: time, lat, lon, los cuatro SPEI y SOIL_MOISTURE_t. TWS_t es opcional. Se aceptan hasta 300 000 filas; los meses previos del archivo también pueden aportar historia.")
        uploaded = st.file_uploader("Archivo con nuevas observaciones", type=["csv"], key="upload_csv")
        if uploaded is not None:
            try:
                frame = parse_csv(uploaded.getvalue())
                st.dataframe(frame.head(20), hide_index=True, width="stretch")
                if st.button("Predecir archivo", type="primary", disabled=not ready, key="predict_upload"):
                    with st.spinner(f"Pronosticando {len(frame):,} observaciones…"):
                        st.session_state["forecast_result"] = predict_frame(frame, selected_families())
            except (ValueError, FloatingPointError, RuntimeError) as exc:
                st.error(str(exc))
    if "forecast_result" in st.session_state:
        show_forecast(st.session_state["forecast_result"])
    st.caption("Los modelos de producción se ajustaron con objetivos hasta septiembre de 2015. La evaluación de la siguiente pestaña corresponde a modelos separados que conservaron intacta la prueba temporal.")

with evaluate:
    if not st.session_state.show_performance:
        st.info("El rendimiento está oculto. Puede volver a mostrarlo desde la barra lateral.")
    elif not (RESULTS / "metricas_modelos.csv").exists():
        st.info("La evaluación se mostrará cuando estén disponibles los resultados de los tres algoritmos.")
    else:
        st.subheader("Prueba temporal reservada")
        st.write("Objetivos de 2014 a septiembre de 2015, evaluados con modelos entrenados con objetivos anteriores a 2014. El archivo oficial Test.csv no tiene etiquetas y sus predicciones no permiten calcular un RMSE comprobable.")
        families = selected_families()
        names = [LABELS[family] for family in families]
        performance = table("metricas_modelos.csv")
        performance = performance[(performance.stage == "holdout") & performance.family.isin(families)]
        st.dataframe(performance[["algorithm", "rmse", "mae", "r2", "bias", "fit_seconds", "inference_ms_per_1000"]].rename(
            columns={"algorithm": "Algoritmo", "rmse": "RMSE", "mae": "MAE", "r2": "R²", "bias": "Sesgo",
                     "fit_seconds": "Ajuste (s)", "inference_ms_per_1000": "Inferencia (ms/1 000)"}),
                     hide_index=True, width="stretch", column_config={
                         **{name: st.column_config.NumberColumn(format="%.4f") for name in ["RMSE", "MAE", "R²", "Sesgo"]},
                         **{name: st.column_config.NumberColumn(format="%.2f") for name in ["Ajuste (s)", "Inferencia (ms/1 000)"]}})
        st.caption("La latencia mide el modelo ya cargado. Un pronóstico en la aplicación añade preparación de datos y carga de archivos.")
        c1, c2 = st.columns(2)
        with c1:
            chart(px.bar(performance, x="algorithm", y="rmse", color="algorithm", color_discrete_map=COLORS,
                         text_auto=".4f", labels={"algorithm": "Algoritmo", "rmse": "RMSE"}, title="Error global de predicción"))
        with c2:
            temporal = table("metricas_por_mes.csv")
            temporal = temporal[temporal.algorithm.isin(names)]
            chart(px.line(temporal, x="target_time", y="rmse", color="algorithm", markers=True,
                          color_discrete_map=COLORS, labels={"target_time": "Mes objetivo", "rmse": "RMSE"},
                          title="El error cambia con el tiempo"))
        c1, c2 = st.columns(2)
        with c1:
            availability = table("metricas_por_disponibilidad.csv")
            availability = availability[availability.algorithm.isin(names)]
            chart(px.bar(availability, x="availability", y="rmse", color="algorithm", barmode="group",
                         color_discrete_map=COLORS, labels={"availability": "TWS actual", "rmse": "RMSE"},
                         title="Efecto de observar u ocultar el TWS"))
        with c2:
            region = table("metricas_por_region.csv")
            region = region[region.algorithm.isin(names)]
            chart(px.bar(region, x="region", y="rmse", color="algorithm", barmode="group",
                         color_discrete_map=COLORS, labels={"region": "Región", "rmse": "RMSE"}, title="Error por región"))
        selected_model = st.selectbox("Modelo para inspeccionar las predicciones", list(families), format_func=LABELS.get, key="scatter_model")
        observed = table("predicciones_visualizacion.parquet")
        a, b = st.columns(2)
        with a:
            fig = px.scatter(observed, x="target", y=f"pred_{selected_model}", color="availability", opacity=.35,
                             labels={"target": "TWS observado", f"pred_{selected_model}": "TWS predicho"}, title="Observado frente a predicho")
            limits = [float(observed.target.min()), float(observed.target.max())]
            fig.add_trace(go.Scatter(x=limits, y=limits, mode="lines", line=dict(color="#182C3D", dash="dash"), showlegend=False))
            chart(fig)
        with b:
            series = table("series_predicciones.csv")
            values = series[["target_time", "observed", f"pred_{selected_model}"]].rename(columns={"observed": "Observado", f"pred_{selected_model}": LABELS[selected_model]})
            chart(px.line(values.melt("target_time", var_name="Serie", value_name="TWS"), x="target_time", y="TWS", color="Serie",
                          color_discrete_map=COLORS, markers=True, labels={"target_time": "Mes objetivo"}, title="Promedio global observado y pronosticado"))
        st.caption("La dispersión utiliza una muestra fija solo para mantener la navegación ágil. Las métricas y las series incluyen toda la prueba reservada. Comparar un promedio global también requiere examinar los errores por celda y región.")
        st.download_button("Descargar métricas", performance.to_csv(index=False).encode("utf-8"), file_name="metricas_modelos.csv", mime="text/csv", key="download_metrics")
