from __future__ import annotations

import os
import sys
from typing import Dict, List

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


def item_por_label(catalogo: List[Dict], label: str) -> Dict:
    for item in catalogo:
        if item["label"] == label:
            return item
    return catalogo[0]


st.markdown(
    """
    <style>
    .main-card {background: linear-gradient(135deg,#153a5b 0%,#1f5f8b 100%); color:white; padding:22px; border-radius:14px; margin-bottom:18px;}
    .soft-box {background:#f6f9fc; border:1px solid #dbe7f3; color:#000; padding:14px 16px; border-radius:12px; margin-bottom:12px;}
    .note-box {background:#eef6ff; border-left:6px solid #1f5f8b; color:#000; padding:14px 16px; border-radius:10px; margin:10px 0 16px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-card">
        <h2 style="margin-bottom:0.35rem;">Cálculo de presupuestos</h2>
        <div style="font-size:1.03rem;">
            Versión estricta: solo usa familias, unidades y precios que aparecen en la base de precios CSV
            y en la estructura del PPTP. No hay geometrías auxiliares, no hay conversiones de unidades y no hay
            precios manuales.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="note-box">
        <b>Cómo funciona esta versión:</b><br>
        Introduces directamente las cantidades en la misma unidad de la base: m, m², m³ o ud.<br>
        La app multiplica <b>cantidad × precio de la base</b> y recompone el presupuesto por capítulos
        para que puedas copiarlo fácilmente a Word.
        <br><br>
        <b>Importante:</b> si una familia no tiene precio visible en la base aportada, no aparece en la app.
        </div>
    """,
    unsafe_allow_html=True,
)

san_labels = [x["label"] for x in d.CATALOGO_SAN]
ovoide_labels = [x["label"] for x in d.CATALOGO_OVOIDE]
dem_bordillo_labels = [x["label"] for x in d.DEMOLICION_BORDILLO]
dem_acerado_labels = [x["label"] for x in d.DEMOLICION_ACERADO]
dem_calzada_labels = [x["label"] for x in d.DEMOLICION_CALZADA]
rep_bordillo_labels = [x["label"] for x in d.BORDILLOS_REPOSICION]
rep_acerado_labels = [x["label"] for x in d.ACERADOS_REPOSICION]
acometida_labels = [x["label"] for x in d.ACOMETIDAS]
pozo_labels = [x["label"] for x in d.POZOS]
imbornal_labels = [x["label"] for x in d.IMBORNALES]
marco_labels = [x["label"] for x in d.MARCOS]


def bloque_obra_civil_aba() -> dict:
    st.markdown("## 1) Capítulo 01 · Obra civil abastecimiento")
    st.markdown("""
    <div class="soft-box">
    Este capítulo solo muestra familias de movimiento de tierras y materiales auxiliares que sí aparecen en la base.
    No se incluyen tuberías FD/PE ni válvulas/tomas porque no tienen precio visible en el CSV aportado.
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        exc_mec_h = st.number_input("Excavación mecánica ≤ 2,5 m (m³)", min_value=0.0, value=0.0, help="Cantidad directa en m³ de la base.")
        exc_mec_m = st.number_input("Excavación mecánica > 2,5 m (m³)", min_value=0.0, value=0.0)
        exc_man_h = st.number_input("Excavación manual ≤ 2,5 m (m³)", min_value=0.0, value=0.0)
        exc_man_m = st.number_input("Excavación manual > 2,5 m (m³)", min_value=0.0, value=0.0)
        ent_h = st.number_input("Entibación blindada ≤ 2,5 m (m²)", min_value=0.0, value=0.0)
        ent_m = st.number_input("Entibación blindada > 2,5 m (m²)", min_value=0.0, value=0.0)
    with c2:
        carga = st.number_input("Carga de tierras (m³)", min_value=0.0, value=0.0)
        transporte = st.number_input("Transporte a vertedero (m³)", min_value=0.0, value=0.0)
        canon = st.number_input("Canon vertido tierras (m³)", min_value=0.0, value=0.0)
        arena = st.number_input("Suministro de arena (m³)", min_value=0.0, value=0.0)
        relleno = st.number_input("Relleno de albero (m³)", min_value=0.0, value=0.0)
    return dict(exc_mec_aba_hasta=exc_mec_h, exc_mec_aba_mas=exc_mec_m, exc_man_aba_hasta=exc_man_h,
                exc_man_aba_mas=exc_man_m, ent_aba_hasta=ent_h, ent_aba_mas=ent_m, carga_aba=carga,
                transporte_aba=transporte, canon_tierras_aba=canon, arena_aba=arena, relleno_aba=relleno)


def bloque_obra_civil_san() -> dict:
    st.markdown("## 2) Capítulo 02 · Obra civil saneamiento")
    st.markdown("""
    <div class="soft-box">
    Aquí introduces cantidades directas de obra civil SAN y los tipos de tubería/colector que sí tienen precio en la base.
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        tipo_san = st.selectbox("Tipo tubería SAN", san_labels)
        metros_san = st.number_input("Longitud tubería SAN (m)", min_value=0.0, value=0.0)
        tipo_ovoide = st.selectbox("Tipo ovoide", ovoide_labels)
        metros_ovoide = st.number_input("Longitud ovoide (m)", min_value=0.0, value=0.0)
        exc_mec_h = st.number_input("Excavación mecánica SAN ≤ 2,5 m (m³)", min_value=0.0, value=0.0)
        exc_mec_m = st.number_input("Excavación mecánica SAN > 2,5 m (m³)", min_value=0.0, value=0.0)
        exc_man_h = st.number_input("Excavación manual SAN ≤ 2,5 m (m³)", min_value=0.0, value=0.0)
        exc_man_m = st.number_input("Excavación manual SAN > 2,5 m (m³)", min_value=0.0, value=0.0)
        ent_h = st.number_input("Entibación SAN ≤ 2,5 m (m²)", min_value=0.0, value=0.0)
        ent_m = st.number_input("Entibación SAN > 2,5 m (m²)", min_value=0.0, value=0.0)
    with c2:
        carga = st.number_input("Carga de tierras SAN (m³)", min_value=0.0, value=0.0)
        transporte = st.number_input("Transporte a vertedero SAN (m³)", min_value=0.0, value=0.0)
        canon_tierras = st.number_input("Canon vertido tierras SAN (m³)", min_value=0.0, value=0.0)
        canon_mixto = st.number_input("Canon vertido mixto SAN (m³)", min_value=0.0, value=0.0)
        arena = st.number_input("Suministro de arena SAN (m³)", min_value=0.0, value=0.0)
        relleno = st.number_input("Relleno de albero SAN (m³)", min_value=0.0, value=0.0)
        tipo_pozo = st.selectbox("Tipo de pozo", pozo_labels)
        uds_pozos = st.number_input("Nº pozos", min_value=0, value=0)
        tipo_imbornal = st.selectbox("Tipo de imbornal", imbornal_labels)
        uds_imbornales = st.number_input("Nº imbornales", min_value=0, value=0)
        tipo_marco = st.selectbox("Tipo de marco", marco_labels)
        uds_marcos = st.number_input("Nº marcos", min_value=0, value=0)
        uds_tapas = st.number_input("Nº tapas de pozo", min_value=0, value=0)
        uds_pates = st.number_input("Nº pates de pozo", min_value=0, value=0)
        uds_dem_pozo = st.number_input("Nº demoliciones de pozo", min_value=0, value=0)
    return dict(
        tipo_san=item_por_label(d.CATALOGO_SAN, tipo_san), metros_san=metros_san,
        tipo_ovoide=item_por_label(d.CATALOGO_OVOIDE, tipo_ovoide), metros_ovoide=metros_ovoide,
        exc_mec_san_hasta=exc_mec_h, exc_mec_san_mas=exc_mec_m, exc_man_san_hasta=exc_man_h,
        exc_man_san_mas=exc_man_m, ent_san_hasta=ent_h, ent_san_mas=ent_m, carga_san=carga,
        transporte_san=transporte, canon_tierras_san=canon_tierras, canon_mixto_san=canon_mixto,
        arena_san=arena, relleno_san=relleno,
        tipo_pozo=item_por_label(d.POZOS, tipo_pozo), uds_pozos=uds_pozos,
        tipo_imbornal=item_por_label(d.IMBORNALES, tipo_imbornal), uds_imbornales=uds_imbornales,
        tipo_marco=item_por_label(d.MARCOS, tipo_marco), uds_marcos=uds_marcos,
        tipo_tapa=d.MATERIALES_POZO_TAPA[0], uds_tapas=uds_tapas,
        tipo_pate=d.MATERIALES_POZO_PATE[0], uds_pates=uds_pates,
        tipo_dem_pozo=item_por_label(d.POZOS, "Demolición de pozo"), uds_dem_pozo=uds_dem_pozo,
    )


def bloque_pavimentacion(nombre: str, key: str) -> dict:
    st.markdown(f"## {nombre}")
    st.markdown("""
    <div class="soft-box">
    Introduce cantidades directas en las unidades de la base: m, m², m³ o ud. No se hacen conversiones automáticas.
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        tipo_dem_bordillo = st.selectbox(f"Tipo bordillo demolido {key}", dem_bordillo_labels, key=f"tdb_{key}")
        dem_bordillo_m = st.number_input(f"Demolición bordillo {key} (m)", min_value=0.0, value=0.0, key=f"db_{key}")
        tipo_dem_acerado = st.selectbox(f"Tipo acerado demolido {key}", dem_acerado_labels, key=f"tda_{key}")
        dem_acerado_m2 = st.number_input(f"Demolición acerado {key} (m²)", min_value=0.0, value=0.0, key=f"da_{key}")
        tipo_dem_calzada = st.selectbox(f"Tipo calzada demolida {key}", dem_calzada_labels, key=f"tdc_{key}")
        dem_calzada_m2 = st.number_input(f"Demolición calzada {key} (m²)", min_value=0.0, value=0.0, key=f"dc_{key}")
        uds_dem_arqueta_imbornal = st.number_input(f"Demolición arqueta de imbornal {key} (ud)", min_value=0, value=0, key=f"dai_{key}")
        uds_dem_imbornal_tuberia = st.number_input(f"Demolición imbornal y tubería {key} (ud)", min_value=0, value=0, key=f"dit_{key}")
        canon_mixto_m3 = st.number_input(f"Canon vertido mixto {key} (m³)", min_value=0.0, value=0.0, key=f"cm_{key}", help="Volumen directo de RCD a gestor autorizado.")
    with c2:
        tipo_rep_bordillo = st.selectbox(f"Tipo bordillo a reponer {key}", rep_bordillo_labels, key=f"trb_{key}")
        rep_bordillo_m = st.number_input(f"Reposición bordillo {key} (m)", min_value=0.0, value=0.0, key=f"rb_{key}")
        tipo_rep_acerado = st.selectbox(f"Tipo acerado a reponer {key}", rep_acerado_labels, key=f"tra_{key}")
        rep_acerado_m2 = st.number_input(f"Reposición acerado {key} (m²)", min_value=0.0, value=0.0, key=f"ra_{key}")
        rep_adoquin_m2 = st.number_input(f"Reposición adoquín {key} (m²)", min_value=0.0, value=0.0, key=f"ado_{key}")
        rep_rodadura_m3 = st.number_input(f"Capa de rodadura {key} (m³)", min_value=0.0, value=0.0, key=f"rod_{key}")
        rep_base_pavimento_m3 = st.number_input(f"Base de pavimento {key} (m³)", min_value=0.0, value=0.0, key=f"bp_{key}")
        rep_hormigon_m3 = st.number_input(f"Hormigón {key} (m³)", min_value=0.0, value=0.0, key=f"hor_{key}")
        rep_base_granular_m3 = st.number_input(f"Base granular {key} (m³)", min_value=0.0, value=0.0, key=f"bg_{key}")
    return {
        "dem_bordillo_m": dem_bordillo_m,
        "precio_dem_bordillo": item_por_label(d.DEMOLICION_BORDILLO, tipo_dem_bordillo)["precio"],
        "dem_acerado_m2": dem_acerado_m2,
        "precio_dem_acerado": item_por_label(d.DEMOLICION_ACERADO, tipo_dem_acerado)["precio"],
        "dem_calzada_m2": dem_calzada_m2,
        "precio_dem_calzada": item_por_label(d.DEMOLICION_CALZADA, tipo_dem_calzada)["precio"],
        "uds_dem_arqueta_imbornal": uds_dem_arqueta_imbornal,
        "precio_dem_arqueta_imbornal": d.REPOSICION_CALZADA["Demolición arqueta de imbornal"]["precio"],
        "uds_dem_imbornal_tuberia": uds_dem_imbornal_tuberia,
        "precio_dem_imbornal_tuberia": d.REPOSICION_CALZADA["Demolición imbornal y tubería"]["precio"],
        "rep_bordillo_m": rep_bordillo_m,
        "precio_rep_bordillo": item_por_label(d.BORDILLOS_REPOSICION, tipo_rep_bordillo)["precio"],
        "rep_acerado_m2": rep_acerado_m2,
        "precio_rep_acerado": item_por_label(d.ACERADOS_REPOSICION, tipo_rep_acerado)["precio"],
        "rep_adoquin_m2": rep_adoquin_m2,
        "precio_rep_adoquin": d.REPOSICION_CALZADA["Reposición adoquín"]["precio"],
        "rep_rodadura_m3": rep_rodadura_m3,
        "precio_rep_rodadura": d.REPOSICION_CALZADA["Capa de rodadura"]["precio"],
        "rep_base_pavimento_m3": rep_base_pavimento_m3,
        "precio_rep_base_pavimento": d.REPOSICION_CALZADA["Base de pavimento"]["precio"],
        "rep_hormigon_m3": rep_hormigon_m3,
        "precio_rep_hormigon": d.REPOSICION_CALZADA["Hormigón"]["precio"],
        "rep_base_granular_m3": rep_base_granular_m3,
        "precio_rep_base_granular": d.REPOSICION_CALZADA["Base granular"]["precio"],
        "canon_mixto_m3": canon_mixto_m3,
        "precio_canon_mixto": d.EXCAVACION["Canon vertido mixto"]["precio"],
    }


def bloque_acometidas() -> dict:
    st.markdown("## 5) Capítulos 05 y 06 · Acometidas")
    st.markdown("""
    <div class="soft-box">
    Selecciona el tipo exacto de acometida de la base y el número de unidades para abastecimiento y saneamiento.
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        tipo_acom_aba = st.selectbox("Tipo acometida ABA", acometida_labels)
        uds_acom_aba = st.number_input("Nº acometidas ABA", min_value=0, value=0)
    with c2:
        tipo_acom_san = st.selectbox("Tipo acometida SAN", acometida_labels, index=indice_seguro(acometida_labels, acometida_labels[min(1, len(acometida_labels)-1)]))
        uds_acom_san = st.number_input("Nº acometidas SAN", min_value=0, value=0)
    return dict(tipo_acom_aba=item_por_label(d.ACOMETIDAS, tipo_acom_aba), uds_acom_aba=uds_acom_aba,
                tipo_acom_san=item_por_label(d.ACOMETIDAS, tipo_acom_san), uds_acom_san=uds_acom_san)


aba = bloque_obra_civil_aba()
san = bloque_obra_civil_san()
pav_aba = bloque_pavimentacion("3) Capítulo 03 · Pavimentación abastecimiento", "aba")
pav_san = bloque_pavimentacion("4) Capítulo 04 · Pavimentación saneamiento", "san")
acom = bloque_acometidas()

st.markdown("## 6) Capítulos 07 y 08 · Seguridad y salud / Gestión ambiental")
col1, col2 = st.columns(2)
with col1:
    importe_ss = st.number_input("Importe Seguridad y Salud (€)", min_value=0.0, value=float(d.IMPORTE_SS_DEFAULT), help="Importe fijo del capítulo 07 según el pliego o expediente.")
with col2:
    importe_ga = st.number_input("Importe Gestión ambiental (€)", min_value=0.0, value=float(d.IMPORTE_GA_DEFAULT), help="Importe fijo del capítulo 08 según el pliego o expediente.")

st.markdown("## 7) Calcular")
if st.button("Calcular presupuesto", type="primary", use_container_width=True):
    p = ParametrosProyecto(**aba, **san, pav_aba=pav_aba, pav_san=pav_san, **acom, importe_ss=importe_ss, importe_ga=importe_ga)
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
            df = pd.DataFrame([
                {"Partida": n, "Importe": euro(v)} for n, v in info["partidas"].items() if v != 0
            ])
            if df.empty:
                st.info("Sin partidas introducidas en este capítulo.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Bloque listo para copiar a Word")
    st.text_area("Texto del presupuesto", value=r["texto_word"], height=320)
else:
    st.info("Introduce las cantidades directas y pulsa “Calcular presupuesto”.")
