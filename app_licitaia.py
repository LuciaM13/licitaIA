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

st.title("Cálculo de presupuestos")

st.header("1) Abastecimiento")
aba_longitud_m = st.number_input("Longitud ABA (m)", 0.0, 10000.0, 100.0)
aba_tipo = st.selectbox("Tipo ABA", sorted({x["tipo"] for x in d.CATALOGO_ABA}))
aba_diametro = st.selectbox("Diámetro ABA", sorted({x["diametro_mm"] for x in d.CATALOGO_ABA if x["tipo"] == aba_tipo}))
aba_profundidad_m = st.number_input("Profundidad ABA (m)", 0.0, 10.0, 1.2)

aba_item = find_item(d.CATALOGO_ABA, aba_tipo, aba_diametro)

st.header("2) Saneamiento")
san_longitud_m = st.number_input("Longitud SAN (m)", 0.0, 10000.0, 150.0)
san_tipo = st.selectbox("Tipo SAN", sorted({x["tipo"] for x in d.CATALOGO_SAN}))
san_diametro = st.selectbox("Diámetro SAN", sorted({x["diametro_mm"] for x in d.CATALOGO_SAN if x["tipo"] == san_tipo}))
san_profundidad_m = st.number_input("Profundidad SAN (m)", 0.0, 10.0, 1.5)

san_item = find_item(d.CATALOGO_SAN, san_tipo, san_diametro)

st.header("3) Pavimentación ABA")
pav_aba_acerado_m2 = st.number_input("m² acerado ABA", 0.0, 10000.0, 200.0)
pav_aba_acerado_label = st.selectbox("Tipo acerado ABA", [x["label"] for x in d.ACERADOS_REPOSICION])
pav_aba_bordillo_m = st.number_input("m bordillo ABA", 0.0, 10000.0, 100.0)
pav_aba_bordillo_label = st.selectbox("Tipo bordillo ABA", [x["label"] for x in d.BORDILLOS_REPOSICION])

pav_aba_acerado_item = next(x for x in d.ACERADOS_REPOSICION if x["label"] == pav_aba_acerado_label)
pav_aba_bordillo_item = next(x for x in d.BORDILLOS_REPOSICION if x["label"] == pav_aba_bordillo_label)

st.header("4) Pavimentación SAN")
pav_san_calzada_m2 = st.number_input("m² calzada SAN", 0.0, 10000.0, 300.0)
pav_san_calzada_label = st.selectbox("Tipo calzada SAN", [x["label"] for x in d.CALZADAS_REPOSICION])
pav_san_acera_m2 = st.number_input("m² acera SAN", 0.0, 10000.0, 200.0)
pav_san_acera_label = st.selectbox("Tipo acera SAN", [x["label"] for x in d.ACERADOS_REPOSICION])

pav_san_calzada_item = next(x for x in d.CALZADAS_REPOSICION if x["label"] == pav_san_calzada_label)
pav_san_acera_item = next(x for x in d.ACERADOS_REPOSICION if x["label"] == pav_san_acera_label)

st.header("5) Acometidas")
acometidas_aba_n = int(st.number_input("Nº acometidas ABA", 0, 1000, 10))
acometidas_san_n = int(st.number_input("Nº acometidas SAN", 0, 1000, 10))

st.header("6) Seguridad y gestión")
pct_seguridad = st.number_input("Seguridad (%)", 0.0, 100.0, 3.0) / 100
pct_gestion = st.number_input("Gestión (%)", 0.0, 100.0, 4.0) / 100

if st.button("Calcular presupuesto"):
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
    st.write("PEM:", euro(r["pem"]))
    st.write("TOTAL:", euro(r["total"]))
else:
    st.info("Introduce los datos mínimos y pulsa 'Calcular presupuesto'.")
