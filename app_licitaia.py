
from __future__ import annotations
import os, sys
from typing import List, Dict, Any
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

def indice_seguro(labels: List[str], valor: str, default: int = 0) -> int:
    return labels.index(valor) if valor in labels else default

def item_por_label(catalogo: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
    for item in catalogo:
        if item["label"] == label:
            return item
    return catalogo[0]

def input_qty(label: str, unidad: str, key: str, help_text: str = "") -> float:
    return st.number_input(f"{label} ({unidad})", min_value=0.0, value=float(st.session_state.get(key, 0.0)), key=key, help=help_text)

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
        Interfaz simplificada y estricta. Solo usa partidas y precios que aparecen en la base CSV
        y en la estructura económica del pliego. La app calcula automáticamente <b>cantidad × precio</b>,
        agrupa por capítulos y genera un bloque final listo para copiar a Word.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="note-box">
<b>Cómo usarla:</b><br>
1. Introduce las cantidades directamente en la unidad de la base: m, m², m³ o ud.<br>
2. En saneamiento, primero eliges la <b>familia</b> y luego el <b>tipo</b> para evitar errores.<br>
3. La app calcula automáticamente los importes y recompone el resumen económico final.
</div>
""", unsafe_allow_html=True)

st.markdown("## 1) Capítulo 01 · Obra civil abastecimiento")
st.markdown('<div class="soft-box">Solo aparecen partidas de la base. No hay tuberías ABA ni precios manuales porque no tienen precio visible en el CSV usado en esta versión.</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    cap01 = {}
    for key in ["exc_mec_hasta", "exc_mec_mas", "exc_man_hasta", "exc_man_mas", "ent_hasta", "ent_mas"]:
        item = d.EXCAVACION[key]
        cap01[key] = input_qty(item["label"], item["unidad"], f"c01_{key}", f"Precio base: {item['precio']} €/ {item['unidad']}")
with c2:
    for key in ["carga", "transporte", "canon_tierras", "arena", "relleno"]:
        item = d.EXCAVACION[key]
        cap01[key] = input_qty(item["label"], item["unidad"], f"c01_{key}", f"Precio base: {item['precio']} €/ {item['unidad']}")

st.markdown("## 2) Capítulo 02 · Obra civil saneamiento")
st.markdown('<div class="soft-box">Aquí eliges la familia de tubería de saneamiento y después solo se muestran las opciones de esa familia. Así se evita elegir materiales que no corresponden.</div>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    familias = list(d.SAN_FAMILIAS.keys())
    familia_san = st.selectbox("Familia de tubería SAN", familias, help="Primero elige la familia.")
    san_labels = [x["label"] for x in d.SAN_FAMILIAS[familia_san]]
    tipo_san = st.selectbox("Tipo tubería SAN", san_labels, help="Ahora solo ves opciones de la familia elegida.")
    san_item = item_por_label(d.SAN_FAMILIAS[familia_san], tipo_san)
    st.markdown(f'<div class="price-chip">Precio base: {san_item["precio"]} €/ {san_item["unidad"]}</div>', unsafe_allow_html=True)
    metros_san = input_qty("Longitud tubería SAN", san_item["unidad"], "metros_san", "Cantidad directa en la unidad de la base.")
    cap02 = {}
    for key in ["exc_mec_hasta", "exc_mec_mas", "exc_man_hasta", "exc_man_mas", "ent_hasta", "ent_mas"]:
        item = d.EXCAVACION[key]
        cap02[key] = input_qty(f"{item['label']} SAN", item["unidad"], f"c02_{key}", f"Precio base: {item['precio']} €/ {item['unidad']}")
with right:
    for key in ["carga", "transporte", "canon_tierras", "canon_mixto", "arena", "relleno"]:
        item = d.EXCAVACION[key]
        cap02[key] = input_qty(f"{item['label']} SAN", item["unidad"], f"c02_{key}", f"Precio base: {item['precio']} €/ {item['unidad']}")
    pozo_labels = [x["label"] for x in d.POZOS]
    pozo_label = st.selectbox("Tipo de pozo", pozo_labels)
    pozo_item = item_por_label(d.POZOS, pozo_label)
    uds_pozos = int(st.number_input("Nº pozos", min_value=0, value=0))
    imbornal_labels = [x["label"] for x in d.IMBORNALES]
    imbornal_label = st.selectbox("Tipo de imbornal", imbornal_labels)
    imbornal_item = item_por_label(d.IMBORNALES, imbornal_label)
    uds_imbornales = int(st.number_input("Nº imbornales", min_value=0, value=0))
    marco_labels = [x["label"] for x in d.MARCOS]
    marco_label = st.selectbox("Tipo de marco", marco_labels)
    marco_item = item_por_label(d.MARCOS, marco_label)
    uds_marcos = int(st.number_input("Nº marcos", min_value=0, value=0))
    uds_tapas = int(st.number_input("Nº tapas de pozo", min_value=0, value=0, help="Precio base fijo: 160,37 €/ud"))
    uds_pates = int(st.number_input("Nº pates de pozo", min_value=0, value=0, help="Precio base fijo: 1,94 €/ud"))
    uds_dem_pozo = int(st.number_input("Nº demoliciones de pozo", min_value=0, value=0))
    dem_pozo_item = item_por_label(d.POZOS, "Demolición de pozo")

def pav_block(prefix: str, title: str):
    st.markdown(title)
    st.markdown('<div class="soft-box">Selecciona el tipo de acabado y mete la cantidad directa en la unidad de la base. Si eliges un tipo, el precio se aplica automáticamente.</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        dem_bordillo_label = st.selectbox(f"Tipo bordillo demolido {prefix}", [x["label"] for x in d.DEMOLICION_BORDILLO], key=f"{prefix}_db_lbl")
        dem_bordillo_item = item_por_label(d.DEMOLICION_BORDILLO, dem_bordillo_label)
        dem_bordillo_qty = input_qty(f"Demolición bordillo {prefix}", dem_bordillo_item["unidad"], f"{prefix}_db_qty", f"Precio base: {dem_bordillo_item['precio']} €/ {dem_bordillo_item['unidad']}")
        dem_acerado_label = st.selectbox(f"Tipo acerado demolido {prefix}", [x["label"] for x in d.DEMOLICION_ACERADO], key=f"{prefix}_da_lbl")
        dem_acerado_item = item_por_label(d.DEMOLICION_ACERADO, dem_acerado_label)
        dem_acerado_qty = input_qty(f"Demolición acerado {prefix}", dem_acerado_item["unidad"], f"{prefix}_da_qty", f"Precio base: {dem_acerado_item['precio']} €/ {dem_acerado_item['unidad']}")
        dem_calzada_label = st.selectbox(f"Tipo calzada demolida {prefix}", [x["label"] for x in d.DEMOLICION_CALZADA], key=f"{prefix}_dc_lbl")
        dem_calzada_item = item_por_label(d.DEMOLICION_CALZADA, dem_calzada_label)
        dem_calzada_qty = input_qty(f"Demolición calzada {prefix}", dem_calzada_item["unidad"], f"{prefix}_dc_qty", f"Precio base: {dem_calzada_item['precio']} €/ {dem_calzada_item['unidad']}")
        dem_arqueta_qty = st.number_input(f"Demolición arqueta de imbornal {prefix} (ud)", min_value=0, value=0, key=f"{prefix}_dai")
        dem_imb_tub_qty = st.number_input(f"Demolición imbornal y tubería {prefix} (ud)", min_value=0, value=0, key=f"{prefix}_dit")
        canon_mixto_qty = input_qty(f"Canon vertido mixto {prefix}", d.EXCAVACION["canon_mixto"]["unidad"], f"{prefix}_cm", f"Precio base: {d.EXCAVACION['canon_mixto']['precio']} €/ {d.EXCAVACION['canon_mixto']['unidad']}")
    with b:
        rep_bordillo_label = st.selectbox(f"Tipo bordillo a reponer {prefix}", [x["label"] for x in d.BORDILLOS_REPOSICION], key=f"{prefix}_rb_lbl")
        rep_bordillo_item = item_por_label(d.BORDILLOS_REPOSICION, rep_bordillo_label)
        rep_bordillo_qty = input_qty(f"Reposición bordillo {prefix}", rep_bordillo_item["unidad"], f"{prefix}_rb_qty", f"Precio base: {rep_bordillo_item['precio']} €/ {rep_bordillo_item['unidad']}")
        rep_acerado_label = st.selectbox(f"Tipo acerado a reponer {prefix}", [x["label"] for x in d.ACERADOS_REPOSICION], key=f"{prefix}_ra_lbl")
        rep_acerado_item = item_por_label(d.ACERADOS_REPOSICION, rep_acerado_label)
        rep_acerado_qty = input_qty(f"Reposición acerado {prefix}", rep_acerado_item["unidad"], f"{prefix}_ra_qty", f"Precio base: {rep_acerado_item['precio']} €/ {rep_acerado_item['unidad']}")
        adoquin_qty = input_qty(f"Reposición adoquín {prefix}", d.REPOSICION_CALZADA["adoquin"]["unidad"], f"{prefix}_ado", f"Precio base: {d.REPOSICION_CALZADA['adoquin']['precio']} €/ {d.REPOSICION_CALZADA['adoquin']['unidad']}")
        rodadura_qty = input_qty(f"Capa de rodadura {prefix}", d.REPOSICION_CALZADA["rodadura"]["unidad"], f"{prefix}_rod", f"Precio base: {d.REPOSICION_CALZADA['rodadura']['precio']} €/ {d.REPOSICION_CALZADA['rodadura']['unidad']}")
        base_pav_qty = input_qty(f"Base de pavimento {prefix}", d.REPOSICION_CALZADA["base_pav"]["unidad"], f"{prefix}_bp", f"Precio base: {d.REPOSICION_CALZADA['base_pav']['precio']} €/ {d.REPOSICION_CALZADA['base_pav']['unidad']}")
        hormigon_qty = input_qty(f"Hormigón {prefix}", d.REPOSICION_CALZADA["hormigon"]["unidad"], f"{prefix}_hor", f"Precio base: {d.REPOSICION_CALZADA['hormigon']['precio']} €/ {d.REPOSICION_CALZADA['hormigon']['unidad']}")
        base_gran_qty = input_qty(f"Base granular {prefix}", d.REPOSICION_CALZADA["base_gran"]["unidad"], f"{prefix}_bg", f"Precio base: {d.REPOSICION_CALZADA['base_gran']['precio']} €/ {d.REPOSICION_CALZADA['base_gran']['unidad']}")
    return {
        "dem_bordillo_item": dem_bordillo_item, "dem_bordillo_qty": dem_bordillo_qty,
        "dem_acerado_item": dem_acerado_item, "dem_acerado_qty": dem_acerado_qty,
        "dem_calzada_item": dem_calzada_item, "dem_calzada_qty": dem_calzada_qty,
        "dem_arqueta_qty": dem_arqueta_qty, "dem_arqueta_precio": d.REPOSICION_CALZADA["dem_arqueta"]["precio"],
        "dem_imb_tub_qty": dem_imb_tub_qty, "dem_imb_tub_precio": d.REPOSICION_CALZADA["dem_imb_tub"]["precio"],
        "canon_mixto_qty": canon_mixto_qty, "canon_mixto_precio": d.EXCAVACION["canon_mixto"]["precio"],
        "rep_bordillo_item": rep_bordillo_item, "rep_bordillo_qty": rep_bordillo_qty,
        "rep_acerado_item": rep_acerado_item, "rep_acerado_qty": rep_acerado_qty,
        "adoquin_qty": adoquin_qty, "adoquin_precio": d.REPOSICION_CALZADA["adoquin"]["precio"],
        "rodadura_qty": rodadura_qty, "rodadura_precio": d.REPOSICION_CALZADA["rodadura"]["precio"],
        "base_pav_qty": base_pav_qty, "base_pav_precio": d.REPOSICION_CALZADA["base_pav"]["precio"],
        "hormigon_qty": hormigon_qty, "hormigon_precio": d.REPOSICION_CALZADA["hormigon"]["precio"],
        "base_gran_qty": base_gran_qty, "base_gran_precio": d.REPOSICION_CALZADA["base_gran"]["precio"],
    }

cap03 = pav_block("aba", "## 3) Capítulo 03 · Pavimentación abastecimiento")
cap04 = pav_block("san", "## 4) Capítulo 04 · Pavimentación saneamiento")

st.markdown("## 5) Capítulos 05 y 06 · Acometidas")
st.markdown('<div class="soft-box">Las acometidas están separadas para que no se mezclen tipos de ABA y SAN. El precio se aplica automáticamente según la opción elegida.</div>', unsafe_allow_html=True)
x, y = st.columns(2)
with x:
    aba_acom_label = st.selectbox("Tipo acometida ABA", [x["label"] for x in d.ACOMETIDAS_ABA])
    acom_aba_item = item_por_label(d.ACOMETIDAS_ABA, aba_acom_label)
    uds_acom_aba = int(st.number_input("Nº acometidas ABA", min_value=0, value=0))
with y:
    san_acom_label = st.selectbox("Tipo acometida SAN", [x["label"] for x in d.ACOMETIDAS_SAN])
    acom_san_item = item_por_label(d.ACOMETIDAS_SAN, san_acom_label)
    uds_acom_san = int(st.number_input("Nº acometidas SAN", min_value=0, value=0))

st.markdown("## 6) Capítulos 07 y 08 · Seguridad y salud / Gestión ambiental")
u, v = st.columns(2)
with u:
    importe_ss = st.number_input("Importe Seguridad y Salud (€)", min_value=0.0, value=float(d.IMPORTE_SS_DEFAULT), help="Importe fijo del capítulo 07 según el pliego.")
with v:
    importe_ga = st.number_input("Importe Gestión ambiental (€)", min_value=0.0, value=float(d.IMPORTE_GA_DEFAULT), help="Importe fijo del capítulo 08 según el pliego.")

st.markdown("## 7) Calcular")
if st.button("Calcular presupuesto", type="primary", use_container_width=True):
    p = ParametrosProyecto(
        cap01=cap01,
        san_item=san_item,
        metros_san=metros_san,
        cap02=cap02,
        pozo_item=pozo_item,
        uds_pozos=uds_pozos,
        imbornal_item=imbornal_item,
        uds_imbornales=uds_imbornales,
        marco_item=marco_item,
        uds_marcos=uds_marcos,
        uds_tapas=uds_tapas,
        uds_pates=uds_pates,
        uds_dem_pozo=uds_dem_pozo,
        dem_pozo_item=dem_pozo_item,
        cap03=cap03,
        cap04=cap04,
        acom_aba_item=acom_aba_item,
        uds_acom_aba=uds_acom_aba,
        acom_san_item=acom_san_item,
        uds_acom_san=uds_acom_san,
        importe_ss=importe_ss,
        importe_ga=importe_ga,
    )
    r = calcular_presupuesto(p)
    st.markdown("## 8) Resumen económico")
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

    st.markdown("### Bloque listo para copiar a Word")
    st.text_area("Texto del presupuesto", value=r["texto_word"], height=320)
else:
    st.info("Introduce las cantidades y pulsa “Calcular presupuesto”.")
