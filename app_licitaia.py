from __future__ import annotations

import os
import sys
from typing import Dict

import pandas as pd
import streamlit as st

# Evita errores de import en despliegues tipo Streamlit Cloud / Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from calcular import ParametrosProyecto, calcular_presupuesto
from datos import (
    CATALOGO_ABA,
    CATALOGO_SAN,
    CASO_PLIEGO_EMASESA,
    COLCHON_ACTIVO_DEFAULT,
    IMPORTE_GA_DEFAULT,
    IMPORTE_SS_DEFAULT,
    MODO_GA_DEFAULT,
    MODO_SS_DEFAULT,
    PCT_GA_DEFAULT,
    PCT_SS_DEFAULT,
    PRECIOS_UNIDADES,
    TIPOS_REURB,
)

st.set_page_config(page_title="LicitaIA", layout="wide")


def euro(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def seleccionar_por_label(catalogo: list[Dict], label: str) -> Dict:
    return next(item for item in catalogo if item["label"] == label)


st.markdown(
    """
<style>
body { background-color: #f4f6f9; }
.title-box {
    background: #1f3b5b;
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 25px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="title-box">
<h2>LicitaIA</h2>
Estimación de presupuesto para redes de abastecimiento, saneamiento y reurbanización
</div>
""",
    unsafe_allow_html=True,
)

if "preset_cargado" not in st.session_state:
    st.session_state.preset_cargado = False

col_a, col_b = st.columns([1, 3])
with col_a:
    if st.button("Cargar caso pliego EMASESA"):
        st.session_state.preset_cargado = True
        for clave, valor in CASO_PLIEGO_EMASESA.items():
            st.session_state[clave] = valor
        st.rerun()
with col_b:
    st.caption("Este botón rellena valores orientativos del caso base para arrancar más rápido.")

aba_labels = [item["label"] for item in CATALOGO_ABA]
san_labels = [item["label"] for item in CATALOGO_SAN]
reurb_labels = [item["label"] for item in TIPOS_REURB]

st.markdown("### Parámetros del proyecto")

col1, col2, col3 = st.columns(3)
with col1:
    metros_aba = st.number_input(
        "Longitud ABA (m)", min_value=0.0, value=float(st.session_state.get("longitud_aba", 100.0))
    )
    aba_label = st.selectbox(
        "Tipo ABA",
        aba_labels,
        index=aba_labels.index(st.session_state.get("tipo_aba", aba_labels[0]))
        if st.session_state.get("tipo_aba", aba_labels[0]) in aba_labels
        else 0,
    )
    uds_acometidas_aba = st.number_input(
        "Nº acometidas ABA", min_value=0, value=int(st.session_state.get("uds_acometidas_aba", 0))
    )
    uds_valvulas = st.number_input(
        "Nº válvulas", min_value=0, value=int(st.session_state.get("uds_valvulas", 0))
    )
    uds_tomas_agua = st.number_input(
        "Nº tomas de agua", min_value=0, value=int(st.session_state.get("uds_tomas_agua", 0))
    )

with col2:
    metros_san = st.number_input(
        "Longitud SAN (m)", min_value=0.0, value=float(st.session_state.get("longitud_san", 150.0))
    )
    san_label = st.selectbox(
        "Tipo SAN",
        san_labels,
        index=san_labels.index(st.session_state.get("tipo_san", san_labels[0]))
        if st.session_state.get("tipo_san", san_labels[0]) in san_labels
        else 0,
    )
    uds_acometidas_san = st.number_input(
        "Nº acometidas SAN", min_value=0, value=int(st.session_state.get("uds_acometidas_san", 0))
    )
    uds_conexiones_san = st.number_input(
        "Nº conexiones SAN", min_value=0, value=int(st.session_state.get("uds_conexiones_san", 0))
    )
    uds_pozos = st.number_input("Nº pozos", min_value=0, value=int(st.session_state.get("uds_pozos", 0)))
    uds_imbornales = st.number_input(
        "Nº imbornales", min_value=0, value=int(st.session_state.get("uds_imbornales", 0))
    )

with col3:
    reurb_label = st.selectbox(
        "Reurbanización",
        reurb_labels,
        index=reurb_labels.index(st.session_state.get("reurbanizacion", reurb_labels[0]))
        if st.session_state.get("reurbanizacion", reurb_labels[0]) in reurb_labels
        else 0,
    )

    st.markdown("#### Seguridad y salud")
    modo_ss = st.radio(
        "Cálculo SS",
        ["fijo", "porcentaje"],
        horizontal=True,
        index=0 if st.session_state.get("modo_ss", MODO_SS_DEFAULT) == "fijo" else 1,
    )
    importe_ss = st.number_input(
        "Importe SS (€)", min_value=0.0, value=float(st.session_state.get("importe_ss", IMPORTE_SS_DEFAULT))
    )
    pct_ss = st.number_input(
        "SS (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("pct_ss", PCT_SS_DEFAULT * 100))
    )

    st.markdown("#### Gestión ambiental")
    modo_ga = st.radio(
        "Cálculo GA",
        ["fijo", "porcentaje"],
        horizontal=True,
        index=0 if st.session_state.get("modo_ga", MODO_GA_DEFAULT) == "fijo" else 1,
    )
    importe_ga = st.number_input(
        "Importe GA (€)", min_value=0.0, value=float(st.session_state.get("importe_ga", IMPORTE_GA_DEFAULT))
    )
    pct_ga = st.number_input(
        "GA (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("pct_ga", PCT_GA_DEFAULT * 100))
    )

st.markdown("### Configuración adicional")
config_col1, config_col2 = st.columns(2)
with config_col1:
    activar_colchon = st.checkbox(
        "Activar colchón comercial",
        value=bool(st.session_state.get("activar_colchon", COLCHON_ACTIVO_DEFAULT)),
    )
with config_col2:
    pct_colchon = st.number_input(
        "Colchón (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("pct_colchon", 10.0))
    )

precios_aba = seleccionar_por_label(CATALOGO_ABA, aba_label)
precios_san = seleccionar_por_label(CATALOGO_SAN, san_label)
reurbanizacion = seleccionar_por_label(TIPOS_REURB, reurb_label)

if st.button("Calcular presupuesto"):
    parametros = ParametrosProyecto(
        metros_aba=metros_aba,
        precios_aba=precios_aba,
        metros_san=metros_san,
        precios_san=precios_san,
        reurbanizacion=reurbanizacion,
        uds_acometidas_aba=uds_acometidas_aba,
        uds_acometidas_san=uds_acometidas_san,
        uds_valvulas=uds_valvulas,
        uds_tomas_agua=uds_tomas_agua,
        uds_conexiones_san=uds_conexiones_san,
        uds_pozos=uds_pozos,
        uds_imbornales=uds_imbornales,
        precio_valvula=PRECIOS_UNIDADES["valvula_compuerta"],
        precio_toma_agua=PRECIOS_UNIDADES["toma_agua"],
        precio_conexion_san=PRECIOS_UNIDADES["conexion_saneamiento"],
        precio_pozo=PRECIOS_UNIDADES["pozo_registro"],
        precio_imbornal=PRECIOS_UNIDADES["imbornal"],
        modo_ss=modo_ss,
        importe_ss=importe_ss,
        pct_ss=pct_ss / 100,
        modo_ga=modo_ga,
        importe_ga=importe_ga,
        pct_ga=pct_ga / 100,
        activar_colchon=activar_colchon,
        pct_colchon=pct_colchon / 100,
    )
    resultado = calcular_presupuesto(parametros)

    st.markdown("### Resumen económico")
    c1, c2, c3 = st.columns(3)
    c1.metric("Presupuesto total", euro(resultado["total"]))
    c2.metric("PEM", euro(resultado["pem"]))
    c3.metric("PBL sin IVA", euro(resultado["pbl_sin_iva"]))

    st.markdown("### Desglose del presupuesto")
    etiquetas = {
        "obra_civil_aba": "Obra civil ABA",
        "obra_civil_san": "Obra civil SAN",
        "pavimentacion_aba": "Pavimentación ABA",
        "pavimentacion_san": "Pavimentación SAN",
        "acometidas_aba": "Acometidas ABA",
        "acometidas_san": "Acometidas SAN",
        "valvulas": "Válvulas",
        "tomas_agua": "Tomas de agua",
        "conexiones_san": "Conexiones SAN",
        "pozos": "Pozos de registro",
        "imbornales": "Imbornales",
        "seguridad_salud": "Seguridad y salud",
        "gestion_ambiental": "Gestión ambiental",
        "pem": "PEM",
        "control_calidad_referencia": "Control de calidad (1% ref.)",
        "gastos_generales": "Gastos generales",
        "beneficio_industrial": "Beneficio industrial",
        "pbl_base": "PBL base",
        "margen_seguridad": "Colchón comercial",
        "pbl_sin_iva": "PBL sin IVA",
        "iva": "IVA",
        "total": "Total",
    }
    orden = list(etiquetas.keys())
    filas = [{"Concepto": etiquetas[k], "Importe": euro(resultado[k])} for k in orden]
    df = pd.DataFrame(filas)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "La partida de control de calidad se muestra como referencia interna para valorar rentabilidad, no como suma adicional automática."
    )
else:
    st.info("Introduce los parámetros del proyecto y pulsa 'Calcular presupuesto'.")
