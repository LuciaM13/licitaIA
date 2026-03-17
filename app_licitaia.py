import streamlit as st
from datos import CATALOGO_ABA, CATALOGO_SAN, TIPOS_REURB
from calcular import calcular_presupuesto

st.set_page_config(page_title="LicitaIA", layout="centered")
st.title("LicitaIA")
st.write("Calculadora de presupuesto")

opciones_aba = [item["label"] for item in CATALOGO_ABA]
opciones_san = [item["label"] for item in CATALOGO_SAN]
opciones_reurb = [item["label"] for item in TIPOS_REURB]

metros_aba = st.number_input("Metros ABA", min_value=0.0, value=100.0, step=1.0)
aba_label = st.selectbox("Tipo ABA", opciones_aba, index=6)

metros_san = st.number_input("Metros SAN", min_value=0.0, value=150.0, step=1.0)
san_label = st.selectbox("Tipo SAN", opciones_san, index=4)

reurb_label = st.selectbox("Tipo de reurbanización", opciones_reurb, index=0)

precios_aba = next(item for item in CATALOGO_ABA if item["label"] == aba_label)
precios_san = next(item for item in CATALOGO_SAN if item["label"] == san_label)
reurbanizacion = next(item for item in TIPOS_REURB if item["label"] == reurb_label)

if st.button("Calcular presupuesto"):
    resultado = calcular_presupuesto(
        metros_aba=metros_aba,
        precios_aba=precios_aba,
        metros_san=metros_san,
        precios_san=precios_san,
        reurbanizacion=reurbanizacion,
    )

    st.subheader("Resultado del cálculo")
    for clave, valor in resultado.items():
        st.write(f"**{clave}**: {valor:,.2f} €")    
