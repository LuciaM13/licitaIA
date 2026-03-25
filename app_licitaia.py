from __future__ import annotations

"""
app_licitaia.py
---------------
Aplicación Streamlit de LicitaIA.

Este archivo hace tres trabajos:
1. dibuja la interfaz
2. recoge los datos que introduce el usuario
3. llama a la lógica de cálculo para obtener el presupuesto

Además, incluye una comprobación opcional del CSV de precios para explicar qué parte
está realmente cubierta por el modelo simplificado.
"""

import os
import sys
from typing import Dict

import pandas as pd
import streamlit as st

# Evita errores de import en despliegues tipo Streamlit Cloud / Render.
# Con esto Python buscará los módulos también en la misma carpeta del proyecto.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from auditor_csv import resumir_csv
from calcular import ParametrosProyecto, calcular_presupuesto
from datos import (
    CATALOGO_ABA,
    CATALOGO_SAN,
    CASO_PLIEGO_EMASESA,
    COLCHON_ACTIVO_DEFAULT,
    CSV_GROUP_STATUS,
    IMPORTE_GA_DEFAULT,
    IMPORTE_SS_DEFAULT,
    MODO_GA_DEFAULT,
    MODO_SS_DEFAULT,
    PCT_COLCHON_DEFAULT,
    PCT_GA_DEFAULT,
    PCT_SS_DEFAULT,
    PRECIOS_UNIDADES,
    TIPOS_REURB,
)

st.set_page_config(page_title="LicitaIA", layout="wide")


def euro(valor: float) -> str:
    """Formatea números como euros con estilo español."""
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def seleccionar_por_label(catalogo: list[Dict], label: str) -> Dict:
    """Devuelve el elemento del catálogo cuyo texto visible coincide con el label."""
    return next(item for item in catalogo if item["label"] == label)


def construir_resultado_auditoria(ruta_csv: str) -> pd.DataFrame:
    """Convierte el resumen del auditor en una tabla cómoda para Streamlit."""
    resumen = resumir_csv(ruta_csv)
    tabla = pd.DataFrame(resumen["detalle"])
    tabla["Precio mínimo"] = tabla["Precio mínimo"].map(euro)
    tabla["Precio máximo"] = tabla["Precio máximo"].map(euro)
    return tabla, resumen


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
.help-box {
    background: #eef4fb;
    border-left: 6px solid #1f3b5b;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
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

st.markdown(
    """
<div class="help-box">
<b>Cómo calcula esta app:</b><br>
1. Calcula obra civil y pavimentación por metro de red.<br>
2. Calcula acometidas y elementos singulares por número de unidades.<br>
3. Suma Seguridad y Salud y Gestión Ambiental como importe fijo o porcentaje.<br>
4. Obtiene el PEM y después aplica GG, BI e IVA.<br>
<br>
<b>Importante:</b> el modelo es una <u>estimación simplificada</u>. No reproduce línea por línea toda la base de precios.
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
    st.caption("Rellena automáticamente un caso de ejemplo parecido al pliego para empezar más rápido.")

aba_labels = [item["label"] for item in CATALOGO_ABA]
san_labels = [item["label"] for item in CATALOGO_SAN]
reurb_labels = [item["label"] for item in TIPOS_REURB]

st.markdown("### Parámetros del proyecto")

# Se agrupan en tres columnas para que el usuario entienda mejor el formulario:
# - columna 1: abastecimiento
# - columna 2: saneamiento
# - columna 3: condicionantes generales
col1, col2, col3 = st.columns(3)
with col1:
    metros_aba = st.number_input(
        "Longitud ABA (m)",
        min_value=0.0,
        value=float(st.session_state.get("longitud_aba", 100.0)),
        help="Metros de red de abastecimiento a ejecutar o renovar.",
    )
    aba_label = st.selectbox(
        "Tipo ABA",
        aba_labels,
        index=aba_labels.index(st.session_state.get("tipo_aba", aba_labels[0]))
        if st.session_state.get("tipo_aba", aba_labels[0]) in aba_labels
        else 0,
        help="Material y diámetro de la tubería de abastecimiento.",
    )
    uds_acometidas_aba = st.number_input(
        "Nº acometidas ABA",
        min_value=0,
        value=int(st.session_state.get("uds_acometidas_aba", 0)),
        help="Número de acometidas de abastecimiento a intervenir.",
    )
    uds_valvulas = st.number_input(
        "Nº válvulas",
        min_value=0,
        value=int(st.session_state.get("uds_valvulas", 0)),
        help="Válvulas de compuerta u otras equivalentes que quieras estimar.",
    )
    uds_tomas_agua = st.number_input(
        "Nº tomas de agua",
        min_value=0,
        value=int(st.session_state.get("uds_tomas_agua", 0)),
        help="Tomas de agua, bocas de riego o elementos similares.",
    )

with col2:
    metros_san = st.number_input(
        "Longitud SAN (m)",
        min_value=0.0,
        value=float(st.session_state.get("longitud_san", 150.0)),
        help="Metros de red de saneamiento a ejecutar o renovar.",
    )
    san_label = st.selectbox(
        "Tipo SAN",
        san_labels,
        index=san_labels.index(st.session_state.get("tipo_san", san_labels[0]))
        if st.session_state.get("tipo_san", san_labels[0]) in san_labels
        else 0,
        help="Material y diámetro de la tubería de saneamiento.",
    )
    uds_acometidas_san = st.number_input(
        "Nº acometidas SAN",
        min_value=0,
        value=int(st.session_state.get("uds_acometidas_san", 0)),
        help="Número de acometidas de saneamiento a adaptar o ejecutar.",
    )
    uds_conexiones_san = st.number_input(
        "Nº conexiones SAN",
        min_value=0,
        value=int(st.session_state.get("uds_conexiones_san", 0)),
        help="Conexiones de la nueva red con la red existente.",
    )
    uds_pozos = st.number_input(
        "Nº pozos",
        min_value=0,
        value=int(st.session_state.get("uds_pozos", 0)),
        help="Pozos de registro nuevos o adaptados.",
    )
    uds_imbornales = st.number_input(
        "Nº imbornales",
        min_value=0,
        value=int(st.session_state.get("uds_imbornales", 0)),
        help="Imbornales nuevos o repuestos.",
    )

with col3:
    reurb_label = st.selectbox(
        "Reurbanización",
        reurb_labels,
        index=reurb_labels.index(st.session_state.get("reurbanizacion", reurb_labels[0]))
        if st.session_state.get("reurbanizacion", reurb_labels[0]) in reurb_labels
        else 0,
        help="Tipo general de reposición superficial. Afecta al coste de pavimentación mediante factores.",
    )

    st.markdown("#### Seguridad y salud")
    modo_ss = st.radio(
        "Cálculo SS",
        ["fijo", "porcentaje"],
        horizontal=True,
        index=0 if st.session_state.get("modo_ss", MODO_SS_DEFAULT) == "fijo" else 1,
        help="Elige si SS se mete como importe cerrado o como porcentaje sobre el parcial.",
    )
    importe_ss = st.number_input(
        "Importe SS (€)",
        min_value=0.0,
        value=float(st.session_state.get("importe_ss", IMPORTE_SS_DEFAULT)),
    )
    pct_ss = st.number_input(
        "SS (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.get("pct_ss", PCT_SS_DEFAULT * 100)),
    )

    st.markdown("#### Gestión ambiental")
    modo_ga = st.radio(
        "Cálculo GA",
        ["fijo", "porcentaje"],
        horizontal=True,
        index=0 if st.session_state.get("modo_ga", MODO_GA_DEFAULT) == "fijo" else 1,
        help="Elige si GA se mete como importe cerrado o como porcentaje sobre el parcial.",
    )
    importe_ga = st.number_input(
        "Importe GA (€)",
        min_value=0.0,
        value=float(st.session_state.get("importe_ga", IMPORTE_GA_DEFAULT)),
    )
    pct_ga = st.number_input(
        "GA (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.get("pct_ga", PCT_GA_DEFAULT * 100)),
    )

st.markdown("### Configuración adicional")
config_col1, config_col2 = st.columns(2)
with config_col1:
    activar_colchon = st.checkbox(
        "Activar colchón comercial",
        value=bool(st.session_state.get("activar_colchon", COLCHON_ACTIVO_DEFAULT)),
        help="Añade un margen interno extra sobre el PBL base. Útil para simulaciones.",
    )
with config_col2:
    pct_colchon = st.number_input(
        "Colchón (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.get("pct_colchon", PCT_COLCHON_DEFAULT * 100)),
    )

# Convertimos las selecciones visuales en diccionarios con precios.
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
    df_resultado = pd.DataFrame(filas)
    st.dataframe(df_resultado, use_container_width=True, hide_index=True)
    st.caption(
        "El control de calidad se muestra como referencia interna. No se suma automáticamente al total del presupuesto."
    )
else:
    st.info("Introduce los parámetros del proyecto y pulsa 'Calcular presupuesto'.")


st.markdown("### Comprobación del CSV de precios")
st.caption(
    "Esta revisión sirve para ver si el modelo simplificado recoge toda la información del CSV o si hay grupos que aún faltan."
)

ruta_csv_por_defecto = os.path.join(BASE_DIR, "240415_VALORACIÓN ACTUACIONES(S-BASE PRECIOS ABRIL-'24)).csv")
ruta_csv = st.text_input("Ruta del CSV a revisar", value=ruta_csv_por_defecto)

if st.button("Analizar CSV"):
    if not os.path.exists(ruta_csv):
        st.error("No se ha encontrado el CSV en esa ruta.")
    else:
        try:
            tabla_auditoria, resumen = construir_resultado_auditoria(ruta_csv)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Líneas con precio", resumen["lineas_con_precio"])
            c2.metric("Grupos detectados", resumen["grupos_detectados"])
            c3.metric("Grupos directos/parciales", f"{resumen['grupos_directos']} / {resumen['grupos_parciales']}")
            c4.metric("Grupos no cubiertos", resumen["grupos_no_cubiertos"])

            st.dataframe(tabla_auditoria, use_container_width=True, hide_index=True)

            st.warning(
                "Conclusión rápida: el CSV sí aporta muchos precios unitarios, pero NO trae por sí solo GG, BI o IVA, y el modelo actual NO recoge todas las familias de líneas del CSV."
            )
        except Exception as exc:
            st.error(f"No se ha podido analizar el CSV: {exc}")
