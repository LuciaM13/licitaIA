from __future__ import annotations

import pandas as pd
import streamlit as st

from calcular import ParametrosProyecto, calcular_presupuesto
from datos import (
    CATALOGO_ABA,
    CATALOGO_SAN,
    COSTES_UNITARIOS_DEFAULT,
    DEFAULTS_PLIEGO,
    TIPOS_REURB,
    VALORES_PLIEGO,
)

st.set_page_config(page_title="LicitaIA", layout="wide")


def euro(v: float) -> str:
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


st.markdown(
    """
    <style>
    body {background-color:#f4f6f9;}
    .title-box {background:#1f3b5b; color:white; padding:20px; border-radius:8px; margin-bottom:25px;}
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

st.info(
    "Esta versión corrige el cálculo de acometidas por metro y permite introducir partidas "
    "independientes como válvulas, pozos, imbornales, conexiones, seguridad y salud y gestión ambiental."
)

modo = st.radio(
    "Modo de cálculo",
    ["Estimación genérica", "Caso pliego EMASESA"],
    horizontal=True,
)

aba_labels = [i["label"] for i in CATALOGO_ABA]
san_labels = [i["label"] for i in CATALOGO_SAN]
reurb_labels = [i["label"] for i in TIPOS_REURB]

st.markdown("### Parámetros principales")
col1, col2, col3 = st.columns(3)

with col1:
    metros_aba = st.number_input(
        "Longitud ABA (m)",
        min_value=0.0,
        value=float(DEFAULTS_PLIEGO["metros_aba_80"] + DEFAULTS_PLIEGO["metros_aba_100"]) if modo == "Caso pliego EMASESA" else 100.0,
        step=1.0,
    )
    aba_label = st.selectbox(
        "Tipo ABA",
        aba_labels,
        index=aba_labels.index("FD Ø 80 mm") if modo == "Caso pliego EMASESA" else aba_labels.index("PE-100 Ø 90 mm"),
    )

with col2:
    metros_san = st.number_input(
        "Longitud SAN (m)",
        min_value=0.0,
        value=float(DEFAULTS_PLIEGO["metros_san"]) if modo == "Caso pliego EMASESA" else 150.0,
        step=1.0,
    )
    san_label = st.selectbox(
        "Tipo SAN",
        san_labels,
        index=san_labels.index("Gres Ø 300 mm"),
    )

with col3:
    reurb_label = st.selectbox(
        "Reurbanización",
        reurb_labels,
        index=reurb_labels.index("Acerado hidráulico + calzada aglomerado") if modo == "Caso pliego EMASESA" else reurb_labels.index("Terrizo / sin urbanizar"),
    )

st.markdown("### Partidas complementarias")
col4, col5 = st.columns(2)

with col4:
    st.markdown("**Capítulo 05 - Acometidas abastecimiento**")
    num_acometidas_aba = st.number_input("Nº acometidas ABA", min_value=0, value=DEFAULTS_PLIEGO["num_acometidas_aba"] if modo == "Caso pliego EMASESA" else 0)
    coste_acometida_aba = st.number_input("Coste unitario acometida ABA (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["acometida_aba"]), step=10.0)
    num_valvulas = st.number_input("Nº válvulas", min_value=0, value=DEFAULTS_PLIEGO["num_valvulas"] if modo == "Caso pliego EMASESA" else 0)
    coste_valvula = st.number_input("Coste unitario válvula (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["valvula"]), step=10.0)
    num_tomas_agua = st.number_input("Nº tomas de agua / BR", min_value=0, value=DEFAULTS_PLIEGO["num_tomas_agua"] if modo == "Caso pliego EMASESA" else 0)
    coste_toma_agua = st.number_input("Coste unitario toma de agua (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["toma_agua"]), step=10.0)

with col5:
    st.markdown("**Capítulo 06 - Acometidas saneamiento**")
    num_acometidas_san = st.number_input("Nº acometidas SAN", min_value=0, value=DEFAULTS_PLIEGO["num_acometidas_san"] if modo == "Caso pliego EMASESA" else 0)
    coste_acometida_san = st.number_input("Coste unitario acometida SAN (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["acometida_san"]), step=10.0)
    num_conexiones_san = st.number_input("Nº conexiones SAN", min_value=0, value=DEFAULTS_PLIEGO["num_conexiones_san"] if modo == "Caso pliego EMASESA" else 0)
    coste_conexion_san = st.number_input("Coste unitario conexión SAN (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["conexion_san"]), step=10.0)
    num_pozos = st.number_input("Nº pozos", min_value=0, value=DEFAULTS_PLIEGO["num_pozos"] if modo == "Caso pliego EMASESA" else 0)
    coste_pozo = st.number_input("Coste unitario pozo (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["pozo"]), step=10.0)
    num_imbornales = st.number_input("Nº imbornales", min_value=0, value=DEFAULTS_PLIEGO["num_imbornales"] if modo == "Caso pliego EMASESA" else 0)
    coste_imbornal = st.number_input("Coste unitario imbornal (€)", min_value=0.0, value=float(COSTES_UNITARIOS_DEFAULT["imbornal"]), step=10.0)

st.markdown("### Seguridad, medio ambiente y margen")
col6, col7, col8 = st.columns(3)

with col6:
    ss_modo_txt = st.selectbox("Seguridad y salud", ["Importe fijo", "Porcentaje"], index=0)
    ss_modo = "fijo" if ss_modo_txt == "Importe fijo" else "porcentaje"
    ss_default = VALORES_PLIEGO["seguridad_salud"] if ss_modo == "fijo" else 0.11
    seguridad_salud_valor = st.number_input(
        "Valor SS (€ o ratio)",
        min_value=0.0,
        value=float(ss_default),
        step=100.0 if ss_modo == "fijo" else 0.01,
        format="%.2f" if ss_modo == "fijo" else "%.4f",
    )

with col7:
    ga_modo_txt = st.selectbox("Gestión ambiental", ["Importe fijo", "Porcentaje"], index=0)
    ga_modo = "fijo" if ga_modo_txt == "Importe fijo" else "porcentaje"
    ga_default = VALORES_PLIEGO["gestion_ambiental"] if ga_modo == "fijo" else 0.04
    gestion_ambiental_valor = st.number_input(
        "Valor GA (€ o ratio)",
        min_value=0.0,
        value=float(ga_default),
        step=100.0 if ga_modo == "fijo" else 0.01,
        format="%.2f" if ga_modo == "fijo" else "%.4f",
    )

with col8:
    incluir_colchon = st.checkbox("Añadir colchón comercial", value=False)
    pct_colchon = st.number_input("% colchón", min_value=0.0, value=0.10, step=0.01, format="%.4f")

precios_aba = next(i for i in CATALOGO_ABA if i["label"] == aba_label)
precios_san = next(i for i in CATALOGO_SAN if i["label"] == san_label)
reurbanizacion = next(i for i in TIPOS_REURB if i["label"] == reurb_label)

if st.button("Calcular presupuesto"):
    params = ParametrosProyecto(
        metros_aba=float(metros_aba),
        precios_aba=precios_aba,
        metros_san=float(metros_san),
        precios_san=precios_san,
        reurbanizacion=reurbanizacion,
        num_acometidas_aba=int(num_acometidas_aba),
        coste_acometida_aba=float(coste_acometida_aba),
        num_acometidas_san=int(num_acometidas_san),
        coste_acometida_san=float(coste_acometida_san),
        num_valvulas=int(num_valvulas),
        coste_valvula=float(coste_valvula),
        num_tomas_agua=int(num_tomas_agua),
        coste_toma_agua=float(coste_toma_agua),
        num_conexiones_san=int(num_conexiones_san),
        coste_conexion_san=float(coste_conexion_san),
        num_pozos=int(num_pozos),
        coste_pozo=float(coste_pozo),
        num_imbornales=int(num_imbornales),
        coste_imbornal=float(coste_imbornal),
        seguridad_salud_modo=ss_modo,
        seguridad_salud_valor=float(seguridad_salud_valor),
        gestion_ambiental_modo=ga_modo,
        gestion_ambiental_valor=float(gestion_ambiental_valor),
        incluir_colchon=bool(incluir_colchon),
        pct_colchon=float(pct_colchon),
    )

    resultado = calcular_presupuesto(params)

    st.markdown("### Resumen económico")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Presupuesto total", euro(resultado["total"]))
    c2.metric("PEM", euro(resultado["pem"]))
    c3.metric("PBL sin IVA", euro(resultado["pbl_sin_iva"]))
    c4.metric("Control calidad 1%", euro(resultado["control_calidad_recomendado"]))

    st.markdown("### Desglose")
    etiquetas = {
        "obra_civil_aba": "Cap. 01 Obra civil ABA",
        "obra_civil_san": "Cap. 02 Obra civil SAN",
        "pavimentacion_aba": "Cap. 03 Pavimentación ABA",
        "pavimentacion_san": "Cap. 04 Pavimentación SAN",
        "acometidas_aba": "Cap. 05 Acometidas ABA",
        "acometidas_san": "Cap. 06 Acometidas SAN",
        "subtotal_capitulos_1_6": "Subtotal capítulos 01-06",
        "seguridad_salud": "Cap. 07 Seguridad y salud",
        "gestion_ambiental": "Cap. 08 Gestión ambiental",
        "pem": "PEM",
        "gastos_generales": "13% Gastos generales",
        "beneficio_industrial": "6% Beneficio industrial",
        "pbl_base": "PBL base",
        "margen_seguridad": "Colchón comercial",
        "pbl_sin_iva": "PBL sin IVA",
        "iva": "IVA",
        "total": "Total",
        "control_calidad_recomendado": "Control de calidad recomendado",
    }
    orden = list(etiquetas.keys())
    filas = [{"Concepto": etiquetas[k], "Importe": euro(resultado[k])} for k in orden]
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    if modo == "Caso pliego EMASESA":
        st.markdown("### Comparativa rápida con los importes del pliego")
        comp = pd.DataFrame([
            {"Concepto": "Cap. 01 Obra civil ABA", "Pliego": euro(VALORES_PLIEGO["obra_civil_aba"]), "Calculado": euro(resultado["obra_civil_aba"]), "Diferencia": euro(resultado["obra_civil_aba"] - VALORES_PLIEGO["obra_civil_aba"] )},
            {"Concepto": "Cap. 02 Obra civil SAN", "Pliego": euro(VALORES_PLIEGO["obra_civil_san"]), "Calculado": euro(resultado["obra_civil_san"]), "Diferencia": euro(resultado["obra_civil_san"] - VALORES_PLIEGO["obra_civil_san"] )},
            {"Concepto": "Cap. 03 Pavimentación ABA", "Pliego": euro(VALORES_PLIEGO["pavimentacion_aba"]), "Calculado": euro(resultado["pavimentacion_aba"]), "Diferencia": euro(resultado["pavimentacion_aba"] - VALORES_PLIEGO["pavimentacion_aba"] )},
            {"Concepto": "Cap. 04 Pavimentación SAN", "Pliego": euro(VALORES_PLIEGO["pavimentacion_san"]), "Calculado": euro(resultado["pavimentacion_san"]), "Diferencia": euro(resultado["pavimentacion_san"] - VALORES_PLIEGO["pavimentacion_san"] )},
            {"Concepto": "Cap. 05 Acometidas ABA", "Pliego": euro(VALORES_PLIEGO["acometidas_aba"]), "Calculado": euro(resultado["acometidas_aba"]), "Diferencia": euro(resultado["acometidas_aba"] - VALORES_PLIEGO["acometidas_aba"] )},
            {"Concepto": "Cap. 06 Acometidas SAN", "Pliego": euro(VALORES_PLIEGO["acometidas_san"]), "Calculado": euro(resultado["acometidas_san"]), "Diferencia": euro(resultado["acometidas_san"] - VALORES_PLIEGO["acometidas_san"] )},
            {"Concepto": "Cap. 07 Seguridad y salud", "Pliego": euro(VALORES_PLIEGO["seguridad_salud"]), "Calculado": euro(resultado["seguridad_salud"]), "Diferencia": euro(resultado["seguridad_salud"] - VALORES_PLIEGO["seguridad_salud"] )},
            {"Concepto": "Cap. 08 Gestión ambiental", "Pliego": euro(VALORES_PLIEGO["gestion_ambiental"]), "Calculado": euro(resultado["gestion_ambiental"]), "Diferencia": euro(resultado["gestion_ambiental"] - VALORES_PLIEGO["gestion_ambiental"] )},
        ])
        st.dataframe(comp, use_container_width=True, hide_index=True)
else:
    st.info("Introduce los parámetros y pulsa 'Calcular presupuesto'.")
