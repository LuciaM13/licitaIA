
from __future__ import annotations
import os
import sys
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
    Esta versión pide solo los datos mínimos:
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
    aba_tipo = st.selectbox("ABAS Tipo de tubería", sorted({x["tipo"] for x in d.CATALOGO_ABA}), help="Material de la conducción ABA.")
with a3:
    aba_diametro = st.selectbox("ABAS Diámetro (mm)", sorted({x["diametro_mm"] for x in d.CATALOGO_ABA if x["tipo"] == aba_tipo}), help="Diámetro de la conducción ABA.")
with a4:
    aba_profundidad_m = st.number_input("ABAS Profundidad (m)", min_value=0.0, value=1.20, help="Profundidad media de la zanja ABA.")
aba_item = find_item(d.CATALOGO_ABA, aba_tipo, aba_diametro)
st.markdown(f'<div class="price-chip">Tubería ABA seleccionada: {aba_item["label"]} · {aba_item["precio_m"]} €/m</div>', unsafe_allow_html=True)

st.markdown("## 2) Saneamiento")
s1, s2, s3, s4 = st.columns(4)
with s1:
    san_longitud_m = st.number_input("SAN Longitud (m)", min_value=0.0, value=132.0, help="Longitud de la conducción SAN.")
with s2:
    san_tipo = st.selectbox("SAN Tipo de tubería", sorted({x["tipo"] for x in d.CATALOGO_SAN}), help="Material de la conducción SAN.")
with s3:
    san_diametro = st.selectbox("SAN Diámetro (mm)", sorted({x["diametro_mm"] for x in d.CATALOGO_SAN if x["tipo"] == san_tipo}), help="Diámetro de la conducción SAN.")
with s4:
    san_profundidad_m = st.number_input("SAN Profundidad (m)", min_value=0.0, value=1.60, help="Profundidad media de la zanja SAN.")
san_item = find_item(d.CATALOGO_SAN, san_tipo, san_diametro)
st.markdown(f'<div class="price-chip">Tubería SAN seleccionada: {san_item["label"]} · {san_item["precio_m"]} €/m</div>', unsafe_allow_html=True)

st.markdown("## 3) Pavimentación abastecimiento")
p1, p2, p3, p4 = st.columns(4)
with p1:
    pav_aba_acerado_m2 = st.number_input("Pav ABAS · m² de acerado", min_value=0.0, value=390.0)
with p2:
    pav_aba_acerado_label = st.selectbox("Pav ABAS · tipo de acerado", [x["label"] for x in d.ACERADOS_REPOSICION])
with p3:
    pav_aba_bordillo_m = st.number_input("Pav ABAS · longitud bordillo (m)", min_value=0.0, value=310.0)
with p4:
    pav_aba_bordillo_label = st.selectbox("Pav ABAS · tipo de bordillo", [x["label"] for x in d.BORDILLOS_REPOSICION])
pav_aba_acerado_item = next(x for x in d.ACERADOS_REPOSICION if x["label"] == pav_aba_acerado_label)
pav_aba_bordillo_item = next(x for x in d.BORDILLOS_REPOSICION if x["label"] == pav_aba_bordillo_label)

st.markdown("## 4) Pavimentación saneamiento")
q1, q2, q3, q4 = st.columns(4)
with q1:
    pav_san_calzada_m2 = st.number_input("Pav SAN · m² de calzada", min_value=0.0, value=760.0)
with q2:
    pav_san_calzada_label = st.selectbox("Pav SAN · tipo de calzada", [x["label"] for x in d.CALZADAS_REPOSICION])
with q3:
    pav_san_acera_m2 = st.number_input("Pav SAN · m² de acera", min_value=0.0, value=390.0)
with q4:
    pav_san_acera_label = st.selectbox("Pav SAN · tipo de acera", [x["label"] for x in d.ACERADOS_REPOSICION])
pav_san_calzada_item = next(x for x in d.CALZADAS_REPOSICION if x["label"] == pav_san_calzada_label)
pav_san_acera_item = next(x for x in d.ACERADOS_REPOSICION if x["label"] == pav_san_acera_label)
if pav_san_calzada_item["unidad"] == "m3":
    esp = d.ESPESORES_CALZADA[pav_san_calzada_item["label"]]
    st.markdown(f'<div class="soft-box">La calzada {pav_san_calzada_item["label"]} se convierte automáticamente de m² a m³ con un espesor de {esp:.2f} m.</div>', unsafe_allow_html=True)

st.markdown("## 5) Acometidas")
c1, c2 = st.columns(2)
with c1:
    acometidas_aba_n = int(st.number_input("Nº acometidas ABA", min_value=0, value=26, help=f"Se aplica automáticamente {d.PRECIO_ACOMETIDA_ABA} €/ud"))
with c2:
    acometidas_san_n = int(st.number_input("Nº acometidas SAN", min_value=0, value=26, help=f"Se aplica automáticamente {d.PRECIO_ACOMETIDA_SAN} €/ud"))

st.markdown("## 6) Seguridad y gestión")
g1, g2 = st.columns(2)
with g1:
    pct_seguridad = st.number_input("Seguridad y Salud (%)", min_value=0.0, value=3.0, help="Se aplica sobre la suma de los capítulos 01 a 06.") / 100.0
with g2:
    pct_gestion = st.number_input("Gestión Ambiental (%)", min_value=0.0, value=4.0, help="Se aplica sobre la suma de los capítulos 01 a 06.") / 100.0

if st.button("Calcular presupuesto", type="primary", use_container_width=True):
    p = ParametrosProyecto(
        aba_item=aba_item,
        aba_longitud_m=aba_longitud_m,
        aba_profundidad_m=aba_profundidad_m,
        san_item=san_item,
        san_longitud_m=san_longitud_m,
        san_profundidad_m=san_profundidad_m,
        pav_aba_acerado_m2=pav_aba_acerado_m2,
        pav_aba_acerado_item=pav_aba_acerado_item,
        pav_aba_bordillo_m=pav_aba_bordillo_m,
        pav_aba_bordillo_item=pav_aba_bordillo_item,
        pav_san_calzada_m2=pav_san_calzada_m2,
        pav_san_calzada_item=pav_san_calzada_item,
        pav_san_acera_m2=pav_san_acera_m2,
        pav_san_acera_item=pav_san_acera_item,
        acometidas_aba_n=acometidas_aba_n,
        acometidas_san_n=acometidas_san_n,
        pct_seguridad=pct_seguridad,
        pct_gestion=pct_gestion,
    )
    r = calcular_presupuesto(p)
    st.markdown("## 7) Resumen económico")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PEM", euro(r["pem"]))
    m2.metric("PBL sin IVA", euro(r["pbl_sin_iva"]))
    m3.metric("IVA", euro(r["iva"]))
    m4.metric("TOTAL", euro(r["total"]))

    st.markdown("### Desglose por capítulos")
    filas = [{"Capítulo": k, "Subtotal": euro(v["subtotal"])} for k, v in r["capitulos"].items()]
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    st.markdown("### Partidas de cada capítulo")
    for cap, info in r["capitulos"].items():
        with st.expander(f"{cap} · {euro(info['subtotal'])}"):
            df = pd.DataFrame([{"Partida": n, "Importe": euro(v)} for n, v in info["partidas"].items() if v != 0])
            if df.empty:
                st.info("Sin partidas introducidas en este capítulo.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Cálculos automáticos de zanja")
    aux = pd.DataFrame([{"Red": "ABA", **r["auxiliares"]["aba"]}, {"Red": "SAN", **r["auxiliares"]["san"]}])
    st.dataframe(aux, use_container_width=True, hide_index=True)

    st.markdown("### Bloque listo para copiar a Word")
    st.text_area("Texto del presupuesto", value=r["texto_word"], height=320)
else:
    st.info("Introduce los datos mínimos y pulsa 'Calcular presupuesto'.")
