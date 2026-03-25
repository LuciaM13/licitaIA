from __future__ import annotations

import os
import sys
from typing import Dict, List

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from calcular import ParametrosProyecto, calcular_presupuesto
import datos as d

st.set_page_config(page_title="Cálculo de presupuestos", layout="wide")


def euro(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_por_label(catalogo: List[Dict], label: str) -> Dict:
    for item in catalogo:
        if item["label"] == label:
            return item
    return catalogo[0]


def indice_seguro(labels: List[str], valor: str, default: int = 0) -> int:
    return labels.index(valor) if valor in labels else default


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
            Esta versión usa solo datos de la base de precios y de la estructura del pliego.
            No incluye precios manuales fuera del Excel. El resultado se desglosa por capítulos
            para poder copiarlo fácilmente a Word.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="note-box">
        <b>Cómo usar la página:</b><br>
        1. Rellena las redes principales.<br>
        2. Ajusta la geometría de zanja si lo necesitas.<br>
        3. Introduce las demoliciones y reposiciones de abastecimiento y saneamiento.<br>
        4. Añade acometidas y elementos que sí tengan precio en la base.<br>
        5. Pulsa <b>Calcular presupuesto</b> para ver capítulos, resumen y texto para Word.
    </div>
    """,
    unsafe_allow_html=True,
)

aba_labels = [x["label"] for x in d.CATALOGO_ABA]
san_labels = [x["label"] for x in d.CATALOGO_SAN]
ovoide_labels = [x["label"] for x in d.CATALOGO_OVOIDE]
dem_bordillo_labels = [x["label"] for x in d.DEMOLICION_BORDILLO]
dem_acerado_labels = [x["label"] for x in d.DEMOLICION_ACERADO]
dem_calzada_labels = [x["label"] for x in d.DEMOLICION_CALZADA]
rep_acerado_labels = [x["label"] for x in d.ACERADOS_REPOSICION]
rep_bordillo_labels = [x["label"] for x in d.BORDILLOS_REPOSICION]
acometida_labels = [x["label"] for x in d.ACOMETIDAS]
pozo_labels = [x["label"] for x in d.POZOS]
imbornal_labels = [x["label"] for x in d.IMBORNALES]
marco_labels = [x["label"] for x in d.MARCOS]
servicios_labels = [x["label"] for x in d.SERVICIOS_AFECTADOS]

def seccion_pav(prefix: str, titulo: str) -> dict:
    st.markdown(f"### {titulo}")
    st.markdown(
        """
        <div class="soft-box">
        Aquí indicas qué pavimento se demuele y cuál se repone. La app usa solo tipos y precios que
        existen en la base. En la calzada demolida se pide también un espesor medio para valorar el
        volumen de residuo mixto (RCD) y aplicar el canon correspondiente.
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        dem_bordillo_m = st.number_input(
            f"Demolición bordillo {prefix} (m)", min_value=0.0, value=0.0, key=f"dem_bordillo_{prefix}",
            help="Longitud de bordillo que se retira en este capítulo de pavimentación.")
        tipo_dem_bordillo = st.selectbox(
            f"Tipo bordillo demolido {prefix}", dem_bordillo_labels, key=f"tipo_dem_bordillo_{prefix}",
            help="Tipo de bordillo existente a demoler según la base de precios.")
        dem_acerado_m2 = st.number_input(
            f"Demolición acerado {prefix} (m²)", min_value=0.0, value=0.0, key=f"dem_acerado_{prefix}",
            help="Superficie de acerado a demoler.")
        tipo_dem_acerado = st.selectbox(
            f"Tipo acerado demolido {prefix}", dem_acerado_labels, key=f"tipo_dem_acerado_{prefix}",
            help="Tipo de acerado existente según la base.")
        dem_calzada_m2 = st.number_input(
            f"Demolición calzada {prefix} (m²)", min_value=0.0, value=0.0, key=f"dem_calzada_{prefix}",
            help="Superficie de calzada a demoler.")
        tipo_dem_calzada = st.selectbox(
            f"Tipo calzada demolida {prefix}", dem_calzada_labels, key=f"tipo_dem_calzada_{prefix}",
            help="Tipo de calzada existente según la base.")
        espesor_dem_calzada = st.number_input(
            f"Espesor calzada demolida {prefix} (m)", min_value=0.0, value=0.25, key=f"espesor_dem_calzada_{prefix}",
            help="Espesor medio del paquete demolido para valorar el residuo mixto.")
    with c2:
        rep_acerado_m2 = st.number_input(
            f"Reposición acerado {prefix} (m²)", min_value=0.0, value=0.0, key=f"rep_acerado_{prefix}",
            help="Superficie de acerado que se repone.")
        tipo_rep_acerado = st.selectbox(
            f"Tipo acerado a reponer {prefix}", rep_acerado_labels, key=f"tipo_rep_acerado_{prefix}",
            help="Tipo de acabado de acerado a reponer.")
        rep_bordillo_m = st.number_input(
            f"Reposición bordillo {prefix} (m)", min_value=0.0, value=0.0, key=f"rep_bordillo_{prefix}",
            help="Longitud de bordillo nuevo.")
        tipo_rep_bordillo = st.selectbox(
            f"Tipo bordillo a reponer {prefix}", rep_bordillo_labels, key=f"tipo_rep_bordillo_{prefix}",
            help="Tipo de bordillo nuevo según la base.")
        rep_adoquin_m2 = st.number_input(
            f"Reposición adoquín {prefix} (m²)", min_value=0.0, value=0.0, key=f"rep_adoquin_{prefix}",
            help="Superficie de adoquín a reponer.")
        rep_rodadura_m2 = st.number_input(
            f"Capa de rodadura {prefix} (m²)", min_value=0.0, value=0.0, key=f"rep_rodadura_{prefix}",
            help="Superficie de mezcla bituminosa de rodadura.")
        rep_base_pavimento_m2 = st.number_input(
            f"Base de pavimento {prefix} (m²)", min_value=0.0, value=0.0, key=f"rep_base_pavimento_{prefix}",
            help="Superficie de base de pavimento que se repone.")
        rep_hormigon_m2 = st.number_input(
            f"Hormigón {prefix} (m²)", min_value=0.0, value=0.0, key=f"rep_hormigon_{prefix}",
            help="Superficie de hormigón a reponer.")
        rep_base_granular_m2 = st.number_input(
            f"Base granular {prefix} (m²)", min_value=0.0, value=0.0, key=f"rep_base_granular_{prefix}",
            help="Superficie de base granular a reponer.")
    return {
        "dem_bordillo_m": dem_bordillo_m,
        "tipo_dem_bordillo": tipo_dem_bordillo,
        "dem_acerado_m2": dem_acerado_m2,
        "tipo_dem_acerado": tipo_dem_acerado,
        "dem_calzada_m2": dem_calzada_m2,
        "tipo_dem_calzada": tipo_dem_calzada,
        "espesor_dem_calzada": espesor_dem_calzada,
        "rep_acerado_m2": rep_acerado_m2,
        "tipo_rep_acerado": tipo_rep_acerado,
        "rep_bordillo_m": rep_bordillo_m,
        "tipo_rep_bordillo": tipo_rep_bordillo,
        "rep_adoquin_m2": rep_adoquin_m2,
        "rep_rodadura_m2": rep_rodadura_m2,
        "rep_base_pavimento_m2": rep_base_pavimento_m2,
        "rep_hormigon_m2": rep_hormigon_m2,
        "rep_base_granular_m2": rep_base_granular_m2,
    }

st.markdown("## 1) Redes principales")
st.markdown(
    """
    <div class="soft-box">
    Aquí indicas los metros de red que quieres presupuestar. Si el abastecimiento tiene dos tramos
    con diámetros distintos, usa el segundo tramo ABA. Si no existe, déjalo en 0.
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    metros_aba = st.number_input("Longitud ABA tramo 1 (m)", min_value=0.0, value=100.0, help="Metros del primer tramo de abastecimiento.")
    tipo_aba = st.selectbox("Tipo ABA tramo 1", aba_labels, help="Material y diámetro del primer tramo ABA.")
    metros_aba2 = st.number_input("Longitud ABA tramo 2 (m)", min_value=0.0, value=0.0, help="Segundo tramo de ABA. Déjalo en 0 si no aplica.")
    tipo_aba2 = st.selectbox("Tipo ABA tramo 2", aba_labels, index=indice_seguro(aba_labels, "FD Ø 100 mm", 0), help="Material y diámetro del segundo tramo ABA.")
with c2:
    metros_san = st.number_input("Longitud SAN (m)", min_value=0.0, value=150.0, help="Metros de saneamiento circular.")
    tipo_san = st.selectbox("Tipo SAN", san_labels, help="Material y diámetro de saneamiento.")
with c3:
    metros_ovoide = st.number_input("Longitud ovoide (m)", min_value=0.0, value=0.0, help="Colector ovoide, solo si existe en la actuación.")
    tipo_ovoide = st.selectbox("Tipo ovoide", ovoide_labels, help="Tipo de ovoide según la base.")

st.markdown("## 2) Geometría y excavación")
st.markdown(
    """
    <div class="soft-box">
    Estos datos sirven para calcular excavación, entibación, arena, relleno, carga, transporte y canon de tierras.
    El volumen de tierras a vertedero descuenta la arena y el relleno que se quedan en la zanja.
    </div>
    """,
    unsafe_allow_html=True,
)

g1, g2 = st.columns(2)
with g1:
    ancho_zanja_aba = st.number_input("Ancho zanja ABA (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["ancho_zanja_aba_m"], help="Ancho medio de zanja de abastecimiento.")
    profundidad_aba = st.number_input("Profundidad ABA (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["profundidad_aba_m"], help="Profundidad media de la zanja de abastecimiento.")
    pct_manual_aba = st.number_input("Excavación manual ABA (%)", min_value=0.0, max_value=100.0, value=d.GEOMETRIA_DEFAULT["porcentaje_excavacion_manual_aba"], help="Porcentaje de excavación manual sobre el volumen de ABA.")
    pct_entibacion_aba = st.number_input("Tramo entibado ABA (%)", min_value=0.0, max_value=100.0, value=d.GEOMETRIA_DEFAULT["porcentaje_entibacion_aba"], help="Porcentaje de longitud ABA que necesita entibación.")
    espesor_arena_aba = st.number_input("Espesor arena ABA (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["espesor_arena_aba_m"], help="Espesor de cama de arena de abastecimiento.")
    espesor_relleno_aba = st.number_input("Espesor relleno ABA (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["espesor_relleno_aba_m"], help="Espesor de relleno en la zanja de abastecimiento.")
with g2:
    ancho_zanja_san = st.number_input("Ancho zanja SAN (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["ancho_zanja_san_m"], help="Ancho medio de zanja de saneamiento.")
    profundidad_san = st.number_input("Profundidad SAN (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["profundidad_san_m"], help="Profundidad media de la zanja de saneamiento.")
    pct_manual_san = st.number_input("Excavación manual SAN (%)", min_value=0.0, max_value=100.0, value=d.GEOMETRIA_DEFAULT["porcentaje_excavacion_manual_san"], help="Porcentaje de excavación manual sobre el volumen de SAN.")
    pct_entibacion_san = st.number_input("Tramo entibado SAN (%)", min_value=0.0, max_value=100.0, value=d.GEOMETRIA_DEFAULT["porcentaje_entibacion_san"], help="Porcentaje de longitud SAN que necesita entibación.")
    espesor_arena_san = st.number_input("Espesor arena SAN (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["espesor_arena_san_m"], help="Espesor de cama de arena de saneamiento.")
    espesor_relleno_san = st.number_input("Espesor relleno SAN (m)", min_value=0.0, value=d.GEOMETRIA_DEFAULT["espesor_relleno_san_m"], help="Espesor de relleno en la zanja de saneamiento.")

st.markdown("## 3) Pavimentación")
aba_pav = seccion_pav("aba", "Pavimentación abastecimiento")
san_pav = seccion_pav("san", "Pavimentación saneamiento")

st.markdown("### Demoliciones específicas saneamiento")
st.markdown(
    """
    <div class="soft-box">
    Estas partidas solo se usan cuando la actuación de saneamiento incluye demolición de arquetas de imbornal
    o de imbornal con tubería.
    </div>
    """,
    unsafe_allow_html=True,
)

dspec1, dspec2 = st.columns(2)
with dspec1:
    uds_dem_arqueta_imbornal = st.number_input("Demolición arqueta de imbornal (ud)", min_value=0, value=0, help="Número de arquetas de imbornal a demoler.")
with dspec2:
    uds_dem_imbornal_tuberia = st.number_input("Demolición imbornal y tubería (ud)", min_value=0, value=0, help="Número de imbornales con tubería a demoler.")

st.markdown("### Espesores de reposición")
st.markdown(
    """
    <div class="soft-box">
    La base de precios valora varias capas por m³. Por eso aquí introduces el espesor medio para convertir las superficies en volumen.
    </div>
    """,
    unsafe_allow_html=True,
)

e1, e2, e3, e4 = st.columns(4)
with e1:
    espesor_rodadura = st.number_input("Espesor rodadura (m)", min_value=0.0, value=d.ESPESORES_REPOSICION_DEFAULT["espesor_rodadura_m"], help="Espesor medio de la capa de rodadura.")
with e2:
    espesor_base_pavimento = st.number_input("Espesor base pavimento (m)", min_value=0.0, value=d.ESPESORES_REPOSICION_DEFAULT["espesor_base_pavimento_m"], help="Espesor medio de la base de pavimento.")
with e3:
    espesor_hormigon = st.number_input("Espesor hormigón (m)", min_value=0.0, value=d.ESPESORES_REPOSICION_DEFAULT["espesor_hormigon_m"], help="Espesor medio del hormigón de reposición.")
with e4:
    espesor_base_granular = st.number_input("Espesor base granular (m)", min_value=0.0, value=d.ESPESORES_REPOSICION_DEFAULT["espesor_base_granular_m"], help="Espesor medio de la base granular.")

st.markdown("## 4) Elementos con precio disponible en la base")
st.markdown(
    """
    <div class="soft-box">
    Aquí solo aparecen elementos con precio identificable en la base: acometidas, pozos, imbornales, marcos, tapas y pates.
    Las tapas y los pates están separados para evitar selecciones ambiguas.
    </div>
    """,
    unsafe_allow_html=True,
)

a1, a2, a3 = st.columns(3)
with a1:
    tipo_acometida_aba = st.selectbox("Tipo acometida ABA", acometida_labels, help="Tipo de acometida de abastecimiento.")
    uds_acometidas_aba = st.number_input("Nº acometidas ABA", min_value=0, value=0, help="Número de acometidas de abastecimiento.")
    tipo_acometida_san = st.selectbox("Tipo acometida SAN", acometida_labels, index=indice_seguro(acometida_labels, "GRES - Adaptación", 0), help="Tipo de acometida de saneamiento.")
    uds_acometidas_san = st.number_input("Nº acometidas SAN", min_value=0, value=0, help="Número de acometidas de saneamiento.")
with a2:
    tipo_pozo = st.selectbox("Tipo de pozo", pozo_labels, help="Tipo de pozo según la base.")
    uds_pozos = st.number_input("Nº pozos", min_value=0, value=0, help="Número de pozos de registro.")
    tipo_imbornal = st.selectbox("Tipo de imbornal", imbornal_labels, help="Tipo de imbornal según la base.")
    uds_imbornales = st.number_input("Nº imbornales", min_value=0, value=0, help="Número de imbornales.")
with a3:
    tipo_marco = st.selectbox("Tipo de marco", marco_labels, help="Tipo de marco según la base.")
    uds_marcos = st.number_input("Nº marcos", min_value=0, value=0, help="Número de marcos.")
    uds_tapas_pozo = st.number_input("Nº tapas de pozo", min_value=0, value=0, help="Número de tapas de pozo de registro.")
    uds_pates_pozo = st.number_input("Nº pates de pozo", min_value=0, value=0, help="Número de pates para los pozos.")

st.markdown("## 5) Servicios afectados, seguridad y salud, gestión ambiental")
st.markdown(
    """
    <div class="soft-box">
    Los servicios afectados se aplican como porcentaje sobre el subtotal directo. Seguridad y salud y gestión ambiental pueden ir como importe fijo o como porcentaje.
    </div>
    """,
    unsafe_allow_html=True,
)

o1, o2, o3 = st.columns(3)
with o1:
    nivel_servicios = st.selectbox("Nivel de servicios afectados", servicios_labels, help="Nivel estimado de afecciones a servicios existentes.")
with o2:
    modo_ss = st.radio("Seguridad y salud", ["fijo", "porcentaje"], horizontal=True, index=0 if d.MODO_SS_DEFAULT == "fijo" else 1, help="Elige si quieres valorar SS con importe fijo o porcentaje.")
    importe_ss = st.number_input("Importe SS (€)", min_value=0.0, value=d.IMPORTE_SS_DEFAULT, help="Importe fijo del capítulo de Seguridad y Salud.")
    pct_ss = st.number_input("SS (%)", min_value=0.0, max_value=100.0, value=d.PCT_SS_CSV * 100, help="Porcentaje de SS si eliges modo porcentaje.")
with o3:
    modo_ga = st.radio("Gestión ambiental", ["fijo", "porcentaje"], horizontal=True, index=0 if d.MODO_GA_DEFAULT == "fijo" else 1, help="Elige si quieres valorar GA con importe fijo o porcentaje.")
    importe_ga = st.number_input("Importe GA (€)", min_value=0.0, value=d.IMPORTE_GA_DEFAULT, help="Importe fijo del capítulo de Gestión Ambiental.")
    pct_ga = st.number_input("GA (%)", min_value=0.0, max_value=100.0, value=4.0, help="Porcentaje de GA si eliges modo porcentaje.")

precios_aba = buscar_por_label(d.CATALOGO_ABA, tipo_aba)
precios_aba2 = buscar_por_label(d.CATALOGO_ABA, tipo_aba2)
precios_san = buscar_por_label(d.CATALOGO_SAN, tipo_san)
precio_ovoide = buscar_por_label(d.CATALOGO_OVOIDE, tipo_ovoide)["tuberia_m"]
precio_acometida_aba = buscar_por_label(d.ACOMETIDAS, tipo_acometida_aba)["precio_ud"]
precio_acometida_san = buscar_por_label(d.ACOMETIDAS, tipo_acometida_san)["precio_ud"]
precio_pozo = buscar_por_label(d.POZOS, tipo_pozo)["precio_ud"]
precio_imbornal = buscar_por_label(d.IMBORNALES, tipo_imbornal)["precio_ud"]
precio_marco = buscar_por_label(d.MARCOS, tipo_marco)["precio_ud"]
precio_tapa_pozo = d.MATERIALES_POZO_TAPA[0]["precio_ud"]
precio_pate_pozo = d.MATERIALES_POZO_PATE[0]["precio_ud"]
pct_servicios = buscar_por_label(d.SERVICIOS_AFECTADOS, nivel_servicios)["pct"]

st.markdown("## 6) Calcular")
st.markdown(
    """
    <div class="soft-box">
    Al pulsar el botón verás el presupuesto por capítulos, el resumen económico y un bloque de texto preparado para copiar y pegar en Word.
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("Calcular presupuesto", type="primary", use_container_width=True):
    p = ParametrosProyecto(
        metros_aba=metros_aba,
        precios_aba=precios_aba,
        metros_aba2=metros_aba2,
        precios_aba2=precios_aba2,
        metros_san=metros_san,
        precios_san=precios_san,
        metros_ovoide=metros_ovoide,
        precio_ovoide_m=precio_ovoide,
        ancho_zanja_aba_m=ancho_zanja_aba,
        profundidad_aba_m=profundidad_aba,
        ancho_zanja_san_m=ancho_zanja_san,
        profundidad_san_m=profundidad_san,
        pct_exc_manual_aba=pct_manual_aba / 100,
        pct_exc_manual_san=pct_manual_san / 100,
        pct_entibacion_aba=pct_entibacion_aba / 100,
        pct_entibacion_san=pct_entibacion_san / 100,
        espesor_arena_aba_m=espesor_arena_aba,
        espesor_arena_san_m=espesor_arena_san,
        espesor_relleno_aba_m=espesor_relleno_aba,
        espesor_relleno_san_m=espesor_relleno_san,
        dem_bordillo_aba_m=aba_pav["dem_bordillo_m"],
        precio_dem_bordillo_aba_m=buscar_por_label(d.DEMOLICION_BORDILLO, aba_pav["tipo_dem_bordillo"])["precio_m"],
        dem_acerado_aba_m2=aba_pav["dem_acerado_m2"],
        precio_dem_acerado_aba_m2=buscar_por_label(d.DEMOLICION_ACERADO, aba_pav["tipo_dem_acerado"])["precio_m2"],
        dem_calzada_aba_m2=aba_pav["dem_calzada_m2"],
        precio_dem_calzada_aba_m2=buscar_por_label(d.DEMOLICION_CALZADA, aba_pav["tipo_dem_calzada"])["precio_m2"],
        espesor_dem_calzada_aba_m=aba_pav["espesor_dem_calzada"],
        rep_acerado_aba_m2=aba_pav["rep_acerado_m2"],
        precio_rep_acerado_aba_m2=buscar_por_label(d.ACERADOS_REPOSICION, aba_pav["tipo_rep_acerado"])["precio_m2"],
        rep_bordillo_aba_m=aba_pav["rep_bordillo_m"],
        precio_rep_bordillo_aba_m=buscar_por_label(d.BORDILLOS_REPOSICION, aba_pav["tipo_rep_bordillo"])["precio_m"],
        rep_adoquin_aba_m2=aba_pav["rep_adoquin_m2"],
        precio_rep_adoquin_aba_m2=d.REPOSICION_CALZADA["adoquin_m2"],
        rep_rodadura_aba_m2=aba_pav["rep_rodadura_m2"],
        precio_rodadura_m3=d.REPOSICION_CALZADA["rodadura_m3"],
        espesor_rodadura_m=espesor_rodadura,
        rep_base_pavimento_aba_m2=aba_pav["rep_base_pavimento_m2"],
        precio_base_pavimento_m3=d.REPOSICION_CALZADA["base_pavimento_m3"],
        espesor_base_pavimento_m=espesor_base_pavimento,
        rep_hormigon_aba_m2=aba_pav["rep_hormigon_m2"],
        precio_hormigon_m3=d.REPOSICION_CALZADA["hormigon_m3"],
        espesor_hormigon_m=espesor_hormigon,
        rep_base_granular_aba_m2=aba_pav["rep_base_granular_m2"],
        precio_base_granular_m3=d.REPOSICION_CALZADA["base_granular_m3"],
        espesor_base_granular_m=espesor_base_granular,
        dem_bordillo_san_m=san_pav["dem_bordillo_m"],
        precio_dem_bordillo_san_m=buscar_por_label(d.DEMOLICION_BORDILLO, san_pav["tipo_dem_bordillo"])["precio_m"],
        dem_acerado_san_m2=san_pav["dem_acerado_m2"],
        precio_dem_acerado_san_m2=buscar_por_label(d.DEMOLICION_ACERADO, san_pav["tipo_dem_acerado"])["precio_m2"],
        dem_calzada_san_m2=san_pav["dem_calzada_m2"],
        precio_dem_calzada_san_m2=buscar_por_label(d.DEMOLICION_CALZADA, san_pav["tipo_dem_calzada"])["precio_m2"],
        espesor_dem_calzada_san_m=san_pav["espesor_dem_calzada"],
        uds_dem_arqueta_imbornal=uds_dem_arqueta_imbornal,
        precio_dem_arqueta_imbornal_ud=d.REPOSICION_CALZADA["demolicion_arqueta_imbornal_ud"],
        uds_dem_imbornal_tuberia=uds_dem_imbornal_tuberia,
        precio_dem_imbornal_tuberia_ud=d.REPOSICION_CALZADA["demolicion_imbornal_tuberia_ud"],
        rep_acerado_san_m2=san_pav["rep_acerado_m2"],
        precio_rep_acerado_san_m2=buscar_por_label(d.ACERADOS_REPOSICION, san_pav["tipo_rep_acerado"])["precio_m2"],
        rep_bordillo_san_m=san_pav["rep_bordillo_m"],
        precio_rep_bordillo_san_m=buscar_por_label(d.BORDILLOS_REPOSICION, san_pav["tipo_rep_bordillo"])["precio_m"],
        rep_adoquin_san_m2=san_pav["rep_adoquin_m2"],
        precio_rep_adoquin_m2=d.REPOSICION_CALZADA["adoquin_m2"],
        rep_rodadura_san_m2=san_pav["rep_rodadura_m2"],
        rep_base_pavimento_san_m2=san_pav["rep_base_pavimento_m2"],
        rep_hormigon_san_m2=san_pav["rep_hormigon_m2"],
        rep_base_granular_san_m2=san_pav["rep_base_granular_m2"],
        precio_exc_mecanica_hasta_25_m3=d.EXCAVACION["mecanica_hasta_2_5_m3"],
        precio_exc_mecanica_mas_25_m3=d.EXCAVACION["mecanica_mas_2_5_m3"],
        precio_exc_manual_hasta_25_m3=d.EXCAVACION["manual_hasta_2_5_m3"],
        precio_exc_manual_mas_25_m3=d.EXCAVACION["manual_mas_2_5_m3"],
        precio_entibacion_hasta_25_m2=d.EXCAVACION["entibacion_blindada_hasta_2_5_m2"],
        precio_entibacion_mas_25_m2=d.EXCAVACION["entibacion_blindada_mas_2_5_m2"],
        precio_carga_m3=d.EXCAVACION["carga_tierras_m3"],
        precio_transporte_m3=d.EXCAVACION["transporte_vertedero_m3"],
        precio_canon_tierras_m3=d.EXCAVACION["canon_vertedero_tierras_m3"],
        precio_canon_mixto_m3=d.EXCAVACION["canon_vertedero_mixto_m3"],
        precio_arena_m3=d.EXCAVACION["arena_m3"],
        precio_relleno_m3=d.EXCAVACION["relleno_albero_m3"],
        uds_acometidas_aba=uds_acometidas_aba,
        precio_acometida_aba_ud=precio_acometida_aba,
        uds_acometidas_san=uds_acometidas_san,
        precio_acometida_san_ud=precio_acometida_san,
        uds_pozos=uds_pozos,
        precio_pozo_ud=precio_pozo,
        uds_imbornales=uds_imbornales,
        precio_imbornal_ud=precio_imbornal,
        uds_marcos=uds_marcos,
        precio_marco_ud=precio_marco,
        uds_tapas_pozo=uds_tapas_pozo,
        precio_tapa_pozo_ud=precio_tapa_pozo,
        uds_pates_pozo=uds_pates_pozo,
        precio_pate_pozo_ud=precio_pate_pozo,
        pct_servicios_afectados=pct_servicios,
        modo_ss=modo_ss,
        importe_ss=importe_ss,
        pct_ss=pct_ss / 100,
        modo_ga=modo_ga,
        importe_ga=importe_ga,
        pct_ga=pct_ga / 100,
    )

    r = calcular_presupuesto(p)

    st.markdown("## 7) Resultado económico")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PEM", euro(r["pem"]))
    m2.metric("PBL sin IVA", euro(r["pbl_sin_iva"]))
    m3.metric("IVA", euro(r["iva"]))
    m4.metric("Total", euro(r["total"]))

    capitulos = [
        ("01 OBRA CIVIL ABASTECIMIENTO", r["capitulo_01"]),
        ("02 OBRA CIVIL SANEAMIENTO", r["capitulo_02"]),
        ("03 PAVIMENTACIÓN ABASTECIMIENTO", r["capitulo_03"]),
        ("04 PAVIMENTACIÓN SANEAMIENTO", r["capitulo_04"]),
        ("05 ACOMETIDAS ABASTECIMIENTO", r["capitulo_05"]),
        ("06 ACOMETIDAS SANEAMIENTO", r["capitulo_06"]),
        ("07 SEGURIDAD Y SALUD", r["capitulo_07"]),
        ("08 GESTIÓN AMBIENTAL", r["capitulo_08"]),
    ]
    st.markdown("### Desglose por capítulos")
    st.dataframe(pd.DataFrame([{"Capítulo": c, "Subtotal": euro(v)} for c, v in capitulos]), use_container_width=True, hide_index=True)

    st.markdown("### Resumen final")
    resumen = [
        ("Presupuesto de Ejecución Material", r["pem"]),
        ("13 % Gastos Generales", r["gastos_generales"]),
        ("6 % Beneficio Industrial", r["beneficio_industrial"]),
        ("Presupuesto Base de Licitación excluido IVA", r["pbl_sin_iva"]),
        ("21 % IVA", r["iva"]),
        ("Presupuesto Base de Licitación incluido IVA", r["total"]),
    ]
    st.dataframe(pd.DataFrame([{"Concepto": c, "Importe": euro(v)} for c, v in resumen]), use_container_width=True, hide_index=True)

    st.markdown("### Texto listo para copiar a Word")
    st.text_area("Presupuesto", value=r["texto_word"].replace(",", "X").replace(".", ",").replace("X", "."), height=260)

    st.markdown("### Cantidades auxiliares")
    aux_cols = st.columns(4)
    aux_cols[0].metric("Vol. zanja ABA", f"{r['vol_zanja_aba']:.2f} m³")
    aux_cols[1].metric("Vol. zanja SAN", f"{r['vol_zanja_san']:.2f} m³")
    aux_cols[2].metric("Arena total", f"{r['vol_arena_total']:.2f} m³")
    aux_cols[3].metric("Relleno total", f"{r['vol_relleno_total']:.2f} m³")
    aux_cols2 = st.columns(3)
    aux_cols2[0].metric("Tierras a vertedero", f"{r['vol_total_tierras']:.2f} m³")
    aux_cols2[1].metric("RCD calzada", f"{r['vol_rcd_calzada']:.2f} m³")
    aux_cols2[2].metric("Control calidad ref.", euro(r["control_calidad_referencia"]))
else:
    st.info("Rellena los datos y pulsa “Calcular presupuesto”.")
