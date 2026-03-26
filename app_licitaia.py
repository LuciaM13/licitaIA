from __future__ import annotations
import os, sys
from typing import Any, Dict, List
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import datos as d
from calcular import ParametrosProyecto, calcular_presupuesto

st.set_page_config(page_title="Cálculo de presupuestos", layout="wide")

def euro(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def find_item(items: List[Dict[str, Any]], tipo: str, diametro: int) -> Dict[str, Any]:
    for item in items:
        if item["tipo"] == tipo and int(item["diametro_mm"]) == int(diametro):
            return item
    return items[0]

st.markdown("""
<style>
.main-card{background:linear-gradient(135deg,#153a5b 0%,#1f5f8b 100%); color:white; padding:24px; border-radius:16px; margin-bottom:18px;}
.soft-box{background:#f6f9fc; border:1px solid #dbe7f3; color:#000; padding:14px 16px; border-radius:12px; margin-bottom:12px;}
.note-box{background:#eef6ff; border-left:6px solid #1f5f8b; color:#000; padding:14px 16px; border-radius:10px; margin:10px 0 16px 0;}
.price-chip{background:#ffffff; border:1px solid #dbe7f3; border-radius:999px; padding:6px 10px; display:inline-block; margin-top:6px; color:#153a5b; font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-card">
  <h2 style="margin-bottom:0.35rem;">Cálculo de presupuestos</h2>
  <div style="font-size:1.03rem;">
    Esta versión pide solo los datos mínimos que has indicado:
    <b>ABA</b>, <b>SAN</b>, <b>pavimentación ABA</b>, <b>pavimentación SAN</b>,
    <b>nº de acometidas</b> y <b>% de Seguridad / Gestión</b>.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="note-box">
<b>Qué calcula automáticamente:</b><br>
- Precio de tubería a partir del tipo y diámetro.<br>
- Ancho de zanja según diámetro.<br>
- Excavación, carga, transporte, canon, arena y relleno a partir de longitud + profundidad.<br>
- En calzada, si eliges aglomerado u hormigón, convierte automáticamente de m² a m³ con un espesor estándar.<br>
- GG 13%, BI 6% e IVA 21% al final.
</div>
""", unsafe_allow_html=True)

st.markdown("## 1) Abastecimiento")
a1, a2, a3, a4 = st.columns(4)
with a1:
    aba_longitud_m = st.number_input("ABAS Longitud (m)", min_value=0.0, value=100.0, help="Longitud de la conducción de abastecimiento.")
with a2:
    aba_tipo = st.selectbox("ABAS Tipo de tubería", sorted({x["tipo"] for x in d.CATALOGO_ABA}))
with a3:
    aba_diametro = st.selectbox("ABAS Diámetro (mm)", sorted({x["diametro_mm"] for x in d.CATALOGO_ABA if x["tipo"] == aba_tipo}))
with a4:
    aba_profundidad_m = st.number_input("ABAS Profundidad (m)", min_value=0.0, value=1.20)
aba_item = find_item(d.CATALOGO_ABA, aba_tipo, aba_diametro)
st.markdown(f'<div class="price-chip">Tubería ABA seleccionada: {aba_item["label"]} · {aba_item["precio_m"]} €/m</div>', unsafe_allow_html=True)

st.markdown("## 2) Saneamiento")
s1, s2, s3, s4 = st.columns(4)
with s1:
    san_longitud_m = st.number_input("SAN Longitud (m)", min_value=0.0, value=132.0)
with s2:
    san_tipo = st.selectbox("SAN Tipo de tubería", sorted({x["tipo"] for x in d.CATALOGO_SAN}))
with s3:
    san_diametro = st.selectbox("SAN Diámetro (mm)", sorted({x["diametro_mm"] for x in d.CATALOGO_SAN if x["tipo"] == san_tipo}))
with s4:
    san_profundidad_m = st.number_input("SAN Profundidad (m)", min_value=0.0, value=1.60)
san_item = find_item(d.CATALOGO_SAN, san_tipo, san_diametro)
    st.info("Introduce los datos mínimos y pulsa “Calcular presupuesto”.")