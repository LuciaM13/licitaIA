import streamlit as st
import pandas as pd

from datos import CATALOGO_ABA, CATALOGO_SAN, TIPOS_REURB
from calcular import calcular_presupuesto

st.set_page_config(
    page_title="LicitaIA",
    layout="wide"
)

def euro(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown("""
<style>

body {
background-color:#f4f6f9;
}

.title-box {
background:#1f3b5b;
color:white;
padding:20px;
border-radius:8px;
margin-bottom:25px;
}

.section {
background:white;
padding:20px;
border-radius:8px;
border:1px solid #e5e7eb;
margin-bottom:20px;
}

.metric {
background:white;
border:1px solid #e5e7eb;
padding:15px;
border-radius:8px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-box">
<h2>LicitaIA</h2>
Estimación de presupuesto para redes de abastecimiento, saneamiento y reurbanización
</div>
""", unsafe_allow_html=True)

aba_labels = [i["label"] for i in CATALOGO_ABA]
san_labels = [i["label"] for i in CATALOGO_SAN]
reurb_labels = [i["label"] for i in TIPOS_REURB]

st.markdown("### Parámetros del proyecto")

col1, col2, col3 = st.columns(3)

with col1:
    metros_aba = st.number_input("Longitud ABA (m)", value=100.0)
    aba_label = st.selectbox("Tipo ABA", aba_labels)

with col2:
    metros_san = st.number_input("Longitud SAN (m)", value=150.0)
    san_label = st.selectbox("Tipo SAN", san_labels)

with col3:
    reurb_label = st.selectbox("Reurbanización", reurb_labels)

st.write("")

calcular = st.button("Calcular presupuesto")

precios_aba = next(i for i in CATALOGO_ABA if i["label"] == aba_label)
precios_san = next(i for i in CATALOGO_SAN if i["label"] == san_label)
reurbanizacion = next(i for i in TIPOS_REURB if i["label"] == reurb_label)

if calcular:

    resultado = calcular_presupuesto(
        metros_aba=metros_aba,
        precios_aba=precios_aba,
        metros_san=metros_san,
        precios_san=precios_san,
        reurbanizacion=reurbanizacion
    )

    st.markdown("### Resumen económico")

    c1, c2, c3 = st.columns(3)

    c1.metric("Presupuesto total", euro(resultado["total"]))
    c2.metric("PEM", euro(resultado["pem"]))
    c3.metric("PBL sin IVA", euro(resultado["pbl_sin_iva"]))

    st.write("")

    st.markdown("### Desglose del presupuesto")

    etiquetas = {
        "obra_civil_aba": "Obra civil ABA",
        "obra_civil_san": "Obra civil SAN",
        "pavimentacion_aba": "Pavimentación ABA",
        "pavimentacion_san": "Pavimentación SAN",
        "acometidas_aba": "Acometidas ABA",
        "acometidas_san": "Acometidas SAN",
        "seguridad_salud": "Seguridad y salud",
        "gestion_ambiental": "Gestión ambiental",
        "pem": "PEM",
        "gastos_generales": "Gastos generales",
        "beneficio_industrial": "Beneficio industrial",
        "pbl_base": "PBL base",
        "margen_seguridad": "Margen de seguridad",
        "pbl_sin_iva": "PBL sin IVA",
        "iva": "IVA",
        "total": "Total"
    }

    df = pd.DataFrame([
        {"Concepto": etiquetas.get(k, k), "Importe": euro(v)}
        for k, v in resultado.items()
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("Introduzca los parámetros del proyecto y pulse 'Calcular presupuesto'.")