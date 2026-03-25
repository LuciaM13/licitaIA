from __future__ import annotations

"""
===============
Aplicación Streamlit de Cálculo de presupuestos.

Objetivo:
- Recoger los datos de una actuación
- Transformarlos en un presupuesto orientativo pero bastante detallado
- Enseñar claramente de dónde sale cada cifra

Correcciones respecto a la versión anterior:
- Soporte para dos tramos ABA con distintos diámetros.
- El transporte y cánon de vertedero de tierras ya descuenta arena y relleno.
- Se añade cánon de vertedero mixto (RCD) para demoliciones de calzada.
- Partida propia de fibrocemento / amianto.
- Partida propia de redes provisionales de suministro.
- Conexiones ABA como campo independiente (antes solo existían en SAN).
- Tapas y pates de pozo son seleccionables, no hardcodeados.
"""

import os
import sys
from typing import Dict, List

import pandas as pd
import streamlit as st

# ----------------------------------------------------------
# Hacemos que los imports funcionen también en despliegue
# ----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from calcular import ParametrosProyecto, calcular_presupuesto
import datos as d

st.set_page_config(page_title="Cálculo de presupuestos", layout="wide")


# ----------------------------------------------------------
# Utilidades de formato y búsqueda
# ----------------------------------------------------------
def euro(valor: float) -> str:
    """Formatea un número como euros usando estilo español."""
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_por_label(catalogo: List[Dict], label: str) -> Dict:
    """Devuelve el elemento del catálogo cuyo texto visible coincide con el label."""
    return next(item for item in catalogo if item["label"] == label)


def indice_seguro(labels: List[str], valor: str, default: int = 0) -> int:
    """Evita errores si el valor guardado no existe ya en el catálogo."""
    return labels.index(valor) if valor in labels else default


# ----------------------------------------------------------
# Estilo visual básico
# ----------------------------------------------------------
st.markdown(
    """
    <style>
    .main-card {
        background: linear-gradient(135deg, #153a5b 0%, #1f5f8b 100%);
        color: white;
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 18px;
    }
    .soft-box {
        background: #f6f9fc;
        border: 1px solid #dbe7f3;
        color: #000000;
        padding: 14px 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    .note-box {
        background: #eef6ff;
        border-left: 6px solid #1f5f8b;
        color: #000000;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 10px 0 16px 0;
    }
    .warn-box {
        background: #fff8e1;
        border-left: 6px solid #f5a623;
        color: #000000;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 10px 0 16px 0;
    }
    .small-text {
        color: #000000;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-card">
        <h2 style="margin-bottom: 0.35rem;">Cálculo de presupuestos</h2>
        <div style="font-size: 1.03rem;">
            Esta app genera un <b>presupuesto desglosado</b> para obras de abastecimiento,
            saneamiento y reposición urbana.
            <br><br>
            <b>Qué calcula:</b> tuberías (hasta dos tramos ABA distintos), excavaciones,
            entibación, carga y transporte de tierras (neto, sin arena ni relleno), cánon de
            vertedero de tierras y de residuos mixtos de demolición, arena, rellenos,
            demoliciones, reposición de acerados y calzada, fibrocemento/amianto, redes
            provisionales, acometidas, pozos, imbornales, marcos, servicios afectados,
            seguridad y salud, gestión ambiental, GG, BI e IVA.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="note-box">
        <b>Cómo usar la página:</b><br>
        1. Rellena las redes principales (puedes añadir un segundo tramo ABA).<br>
        2. Revisa la geometría de zanja si quieres afinar excavación y materiales.<br>
        3. Indica demoliciones y reposiciones.<br>
        4. Añade acometidas y elementos singulares.<br>
        5. Rellena fibrocemento y redes provisionales si aplica.<br>
        6. Pulsa <b>Calcular presupuesto</b> para ver el desglose completo.
    </div>
    """,
    unsafe_allow_html=True,
)


# Etiquetas visibles
aba_labels        = [x["label"] for x in d.CATALOGO_ABA]
san_labels        = [x["label"] for x in d.CATALOGO_SAN]
ovoide_labels     = [x["label"] for x in d.CATALOGO_OVOIDE]
dem_bordillo_labels = [x["label"] for x in d.DEMOLICION_BORDILLO]
dem_acerado_labels  = [x["label"] for x in d.DEMOLICION_ACERADO]
dem_calzada_labels  = [x["label"] for x in d.DEMOLICION_CALZADA]
rep_acerado_labels  = [x["label"] for x in d.ACERADOS_REPOSICION]
rep_bordillo_labels = [x["label"] for x in d.BORDILLOS_REPOSICION]
acometida_labels  = [x["label"] for x in d.ACOMETIDAS]
pozo_labels       = [x["label"] for x in d.POZOS]
imbornal_labels   = [x["label"] for x in d.IMBORNALES]
marco_labels      = [x["label"] for x in d.MARCOS]
mat_pozo_labels   = [x["label"] for x in d.MATERIALES_POZO]
servicios_labels  = [x["label"] for x in d.SERVICIOS_AFECTADOS]

# ==============================================================
# BLOQUE 1 · Redes principales
# ==============================================================
st.markdown("## 1) Redes principales")
st.markdown(
    """
    <div class="soft-box">
    Indica los metros de red a presupuestar. Si tu obra tiene <b>dos tramos ABA con diámetros
    distintos</b> (por ejemplo FD Ø80 + FD Ø100), rellena el Tramo 2 ABA; si no, déjalo en 0.
    La excavación ABA se calcula sobre la suma de ambos tramos con la misma geometría de zanja.
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### Abastecimiento — Tramo 1")
    metros_aba = st.number_input(
        "Longitud ABA tramo 1 (m)",
        min_value=0.0,
        value=float(st.session_state.get("longitud_aba", 100.0)),
        help="Metros de red de abastecimiento, primer diámetro.",
    )
    tipo_aba = st.selectbox(
        "Tipo ABA tramo 1",
        aba_labels,
        index=indice_seguro(aba_labels, st.session_state.get("tipo_aba", aba_labels[0])),
        help="Material y diámetro de la red ABA principal.",
    )
    st.markdown("### Abastecimiento — Tramo 2 *(opcional)*")
    metros_aba2 = st.number_input(
        "Longitud ABA tramo 2 (m)",
        min_value=0.0,
        value=float(st.session_state.get("longitud_aba2", 0.0)),
        help="Deja en 0 si no hay segundo tramo ABA.",
    )
    tipo_aba2 = st.selectbox(
        "Tipo ABA tramo 2",
        aba_labels,
        index=indice_seguro(aba_labels, st.session_state.get("tipo_aba2", aba_labels[0])),
        help="Material y diámetro del segundo tramo ABA.",
    )

with c2:
    st.markdown("### Saneamiento")
    metros_san = st.number_input(
        "Longitud SAN (m)",
        min_value=0.0,
        value=float(st.session_state.get("longitud_san", 150.0)),
        help="Metros de red de saneamiento circular.",
    )
    tipo_san = st.selectbox(
        "Tipo SAN",
        san_labels,
        index=indice_seguro(san_labels, st.session_state.get("tipo_san", san_labels[0])),
        help="Material y diámetro de la red de saneamiento.",
    )

with c3:
    st.markdown("### Ovoide *(opcional)*")
    metros_ovoide = st.number_input(
        "Longitud ovoide (m)",
        min_value=0.0,
        value=float(st.session_state.get("longitud_ovoide", 0.0)),
        help="Si tu obra tiene colector ovoide, indícalo aquí. Si no, déjalo en 0.",
    )
    tipo_ovoide = st.selectbox(
        "Tipo ovoide",
        ovoide_labels,
        index=indice_seguro(ovoide_labels, st.session_state.get("tipo_ovoide", ovoide_labels[0])),
        help="Se usa solo si has indicado metros de ovoide.",
    )

# ==============================================================
# BLOQUE 2 · Geometría y excavación
# ==============================================================
st.markdown("## 2) Geometría de zanja, excavación y materiales auxiliares")
st.markdown(
    """
    <div class="soft-box">
    Este bloque sirve para calcular <b>excavación, entibación, carga, transporte, cánon de
    vertedero de tierras, arena de cama y relleno</b>.
    <br><br>
    <b>Fórmula base:</b> volumen bruto de zanja = longitud × ancho × profundidad.
    El volumen neto a transportar descuenta la arena y el relleno que quedan en la zanja.<br>
    Si superas los 2,5 m de profundidad, la app cambia automáticamente a los precios profundos.
    </div>
    """,
    unsafe_allow_html=True,
)

g1, g2 = st.columns(2)
with g1:
    st.markdown("### Abastecimiento (ABA)")
    ancho_zanja_aba = st.number_input(
        "Ancho de zanja ABA (m)",
        min_value=0.0,
        value=float(st.session_state.get("ancho_zanja_aba_m", d.GEOMETRIA_DEFAULT["ancho_zanja_aba_m"])),
        help="Ancho medio de zanja para la red ABA (se aplica a ambos tramos).",
    )
    profundidad_aba = st.number_input(
        "Profundidad media ABA (m)",
        min_value=0.0,
        value=float(st.session_state.get("profundidad_aba_m", d.GEOMETRIA_DEFAULT["profundidad_aba_m"])),
        help="Si supera 2,5 m, la app cambia automáticamente a los precios profundos del CSV.",
    )
    pct_manual_aba = st.number_input(
        "Excavación manual ABA (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get("excavacion_manual_aba", d.GEOMETRIA_DEFAULT["porcentaje_excavacion_manual_aba"])),
        step=1.0,
        help="Porcentaje del volumen de zanja ABA que se excava manualmente.",
    )
    pct_entibacion_aba = st.number_input(
        "Tramo entibado ABA (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get("entibacion_aba", d.GEOMETRIA_DEFAULT["porcentaje_entibacion_aba"])),
        step=1.0,
        help="Porcentaje de la longitud ABA que necesita entibación.",
    )
    espesor_arena_aba = st.number_input(
        "Espesor arena ABA (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_arena_aba_m", d.GEOMETRIA_DEFAULT["espesor_arena_aba_m"])),
        help="Espesor de cama de arena para ABA. Se descuenta del volumen a transportar.",
    )
    espesor_relleno_aba = st.number_input(
        "Espesor relleno ABA (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_relleno_aba_m", d.GEOMETRIA_DEFAULT["espesor_relleno_aba_m"])),
        help="Espesor de relleno/albero en zanja. Se descuenta del volumen a transportar.",
    )

with g2:
    st.markdown("### Saneamiento (SAN)")
    ancho_zanja_san = st.number_input(
        "Ancho de zanja SAN (m)",
        min_value=0.0,
        value=float(st.session_state.get("ancho_zanja_san_m", d.GEOMETRIA_DEFAULT["ancho_zanja_san_m"])),
        help="Ancho medio de zanja para la red SAN.",
    )
    profundidad_san = st.number_input(
        "Profundidad media SAN (m)",
        min_value=0.0,
        value=float(st.session_state.get("profundidad_san_m", d.GEOMETRIA_DEFAULT["profundidad_san_m"])),
        help="Si supera 2,5 m, la app usa automáticamente el precio profundo.",
    )
    pct_manual_san = st.number_input(
        "Excavación manual SAN (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get("excavacion_manual_san", d.GEOMETRIA_DEFAULT["porcentaje_excavacion_manual_san"])),
        step=1.0,
        help="Porcentaje del volumen de zanja SAN que se excava manualmente.",
    )
    pct_entibacion_san = st.number_input(
        "Tramo entibado SAN (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get("entibacion_san", d.GEOMETRIA_DEFAULT["porcentaje_entibacion_san"])),
        step=1.0,
        help="Porcentaje de la longitud SAN que necesita entibación.",
    )
    espesor_arena_san = st.number_input(
        "Espesor arena SAN (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_arena_san_m", d.GEOMETRIA_DEFAULT["espesor_arena_san_m"])),
        help="Espesor de cama de arena para SAN. Se descuenta del volumen a transportar.",
    )
    espesor_relleno_san = st.number_input(
        "Espesor relleno SAN (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_relleno_san_m", d.GEOMETRIA_DEFAULT["espesor_relleno_san_m"])),
        help="Espesor de relleno/albero en zanja SAN. Se descuenta del volumen a transportar.",
    )

# ==============================================================
# BLOQUE 3 · Demoliciones y reposiciones
# ==============================================================
st.markdown("## 3) Demoliciones y reposición urbana")
st.markdown(
    """
    <div class="soft-box">
    Aquí introduces lo que rompes y lo que después tienes que reponer.
    <br><br>
    <b>Nota sobre el cánon de vertedero:</b> el volumen de calzada demolida (hormigón, asfalto,
    adoquín) es un residuo de construcción y demolición (RCD), no tierra limpia, y se le aplica
    el cánon mixto (13,22 €/m³). Para ello necesitas indicar el espesor medio de la calzada demolida.
    </div>
    """,
    unsafe_allow_html=True,
)

d1, d2 = st.columns(2)
with d1:
    st.markdown("### Demoliciones")
    dem_bordillo_m = st.number_input(
        "Demolición de bordillo (m)",
        min_value=0.0,
        value=float(st.session_state.get("dem_bordillo_m", 0.0)),
    )
    tipo_dem_bordillo = st.selectbox(
        "Tipo de bordillo demolido",
        dem_bordillo_labels,
        index=indice_seguro(dem_bordillo_labels, st.session_state.get("tipo_dem_bordillo", dem_bordillo_labels[0])),
    )

    dem_acerado_m2 = st.number_input(
        "Demolición de acerado (m²)",
        min_value=0.0,
        value=float(st.session_state.get("dem_acerado_m2", 0.0)),
    )
    tipo_dem_acerado = st.selectbox(
        "Tipo de acerado demolido",
        dem_acerado_labels,
        index=indice_seguro(dem_acerado_labels, st.session_state.get("tipo_dem_acerado", dem_acerado_labels[0])),
    )

    dem_calzada_m2 = st.number_input(
        "Demolición de calzada (m²)",
        min_value=0.0,
        value=float(st.session_state.get("dem_calzada_m2", 0.0)),
    )
    tipo_dem_calzada = st.selectbox(
        "Tipo de calzada demolida",
        dem_calzada_labels,
        index=indice_seguro(dem_calzada_labels, st.session_state.get("tipo_dem_calzada", dem_calzada_labels[0])),
    )
    espesor_dem_calzada = st.number_input(
        "Espesor medio calzada demolida (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_dem_calzada_m", 0.25)),
        help="Se usa para calcular el volumen de RCD y aplicar el cánon mixto (13,22 €/m³) en lugar del de tierras.",
    )

    uds_dem_arqueta_imbornal = st.number_input(
        "Demolición de arqueta de imbornal (ud)",
        min_value=0,
        value=int(st.session_state.get("uds_dem_arqueta_imbornal", 0)),
    )
    uds_dem_imbornal_tuberia = st.number_input(
        "Demolición de imbornal y tubería (ud)",
        min_value=0,
        value=int(st.session_state.get("uds_dem_imbornal_tuberia", 0)),
    )

with d2:
    st.markdown("### Reposiciones")
    rep_acerado_m2 = st.number_input(
        "Reposición de acerado (m²)",
        min_value=0.0,
        value=float(st.session_state.get("rep_acerado_m2", 0.0)),
    )
    tipo_rep_acerado = st.selectbox(
        "Tipo de acerado a reponer",
        rep_acerado_labels,
        index=indice_seguro(rep_acerado_labels, st.session_state.get("tipo_rep_acerado", rep_acerado_labels[0])),
    )

    rep_bordillo_m = st.number_input(
        "Reposición de bordillo (m)",
        min_value=0.0,
        value=float(st.session_state.get("rep_bordillo_m", 0.0)),
    )
    tipo_rep_bordillo = st.selectbox(
        "Tipo de bordillo a reponer",
        rep_bordillo_labels,
        index=indice_seguro(rep_bordillo_labels, st.session_state.get("tipo_rep_bordillo", rep_bordillo_labels[0])),
    )

    rep_adoquin_m2 = st.number_input(
        "Reposición de adoquín (m²)",
        min_value=0.0,
        value=float(st.session_state.get("rep_adoquin_m2", 0.0)),
        help="Partida directa en m².",
    )
    rep_rodadura_m2 = st.number_input(
        "Superficie de capa de rodadura (m²)",
        min_value=0.0,
        value=float(st.session_state.get("rep_rodadura_m2", 0.0)),
        help="La app multiplica superficie × espesor × precio por m³.",
    )
    rep_base_pavimento_m2 = st.number_input(
        "Superficie de base de pavimento (m²)",
        min_value=0.0,
        value=float(st.session_state.get("rep_base_pavimento_m2", 0.0)),
    )
    rep_hormigon_m2 = st.number_input(
        "Superficie de hormigón (m²)",
        min_value=0.0,
        value=float(st.session_state.get("rep_hormigon_m2", 0.0)),
    )
    rep_base_granular_m2 = st.number_input(
        "Superficie de base granular (m²)",
        min_value=0.0,
        value=float(st.session_state.get("rep_base_granular_m2", 0.0)),
    )

st.markdown("### Espesores de reposición de calzada")
st.markdown(
    """
    <div class="soft-box small-text">
    Las partidas de capa de rodadura, base de pavimento, hormigón y base granular están en el CSV
    en <b>m³</b>. Aquí introduces la <b>superficie</b> y la app la convierte con estos espesores.
    </div>
    """,
    unsafe_allow_html=True,
)
e1, e2, e3, e4 = st.columns(4)
with e1:
    espesor_rodadura = st.number_input(
        "Espesor rodadura (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_rodadura_m", d.ESPESORES_REPOSICION_DEFAULT["espesor_rodadura_m"])),
    )
with e2:
    espesor_base_pavimento = st.number_input(
        "Espesor base de pavimento (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_base_pavimento_m", d.ESPESORES_REPOSICION_DEFAULT["espesor_base_pavimento_m"])),
    )
with e3:
    espesor_hormigon = st.number_input(
        "Espesor hormigón (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_hormigon_m", d.ESPESORES_REPOSICION_DEFAULT["espesor_hormigon_m"])),
    )
with e4:
    espesor_base_granular = st.number_input(
        "Espesor base granular (m)",
        min_value=0.0,
        value=float(st.session_state.get("espesor_base_granular_m", d.ESPESORES_REPOSICION_DEFAULT["espesor_base_granular_m"])),
    )

# ==============================================================
# BLOQUE 4 · Elementos singulares y acometidas
# ==============================================================
st.markdown("## 4) Acometidas y elementos singulares")
st.markdown(
    """
    <div class="soft-box">
    Acometidas, válvulas, tomas de agua, conexiones a red existente (ABA y SAN),
    pozos, imbornales, marcos, tapas y pates.
    </div>
    """,
    unsafe_allow_html=True,
)

s1, s2, s3 = st.columns(3)
with s1:
    st.markdown("### Acometidas y válvulas")
    tipo_acometida_aba = st.selectbox(
        "Tipo acometida ABA",
        acometida_labels,
        index=indice_seguro(acometida_labels, st.session_state.get("tipo_acometida_aba", acometida_labels[0])),
    )
    uds_acometidas_aba = st.number_input(
        "Nº acometidas ABA",
        min_value=0,
        value=int(st.session_state.get("uds_acometidas_aba", 0)),
    )

    tipo_acometida_san = st.selectbox(
        "Tipo acometida SAN",
        acometida_labels,
        index=indice_seguro(acometida_labels, st.session_state.get("tipo_acometida_san", acometida_labels[0])),
    )
    uds_acometidas_san = st.number_input(
        "Nº acometidas SAN",
        min_value=0,
        value=int(st.session_state.get("uds_acometidas_san", 0)),
    )

    uds_valvulas = st.number_input(
        "Nº válvulas",
        min_value=0,
        value=int(st.session_state.get("uds_valvulas", 0)),
    )
    precio_valvula = st.number_input(
        "Precio unitario válvula (€)",
        min_value=0.0,
        value=float(st.session_state.get("precio_valvula", 950.0)),
        help="Importe editable — no viene completo en el CSV aportado.",
    )
    uds_tomas_agua = st.number_input(
        "Nº tomas de agua",
        min_value=0,
        value=int(st.session_state.get("uds_tomas_agua", 0)),
    )
    precio_toma_agua = st.number_input(
        "Precio unitario toma de agua (€)",
        min_value=0.0,
        value=float(st.session_state.get("precio_toma_agua", 600.0)),
        help="Importe editable.",
    )

    st.markdown("### Conexiones a red existente")
    uds_conexiones_aba = st.number_input(
        "Nº conexiones ABA",
        min_value=0,
        value=int(st.session_state.get("uds_conexiones_aba", 0)),
        help="Conexiones de la red nueva a la red existente de abastecimiento.",
    )
    precio_conexion_aba = st.number_input(
        "Precio unitario conexión ABA (€)",
        min_value=0.0,
        value=float(st.session_state.get("precio_conexion_aba", 950.0)),
        help="Importe editable según tipo y diámetro de la conexión.",
    )
    uds_conexiones_san = st.number_input(
        "Nº conexiones SAN",
        min_value=0,
        value=int(st.session_state.get("uds_conexiones_san", 0)),
        help="Conexiones de la red nueva a la red existente de saneamiento.",
    )
    precio_conexion_san = st.number_input(
        "Precio unitario conexión SAN (€)",
        min_value=0.0,
        value=float(st.session_state.get("precio_conexion_san", 850.0)),
        help="Importe editable.",
    )

with s2:
    st.markdown("### Pozos e imbornales")
    tipo_pozo = st.selectbox(
        "Tipo de pozo",
        pozo_labels,
        index=indice_seguro(pozo_labels, st.session_state.get("tipo_pozo", pozo_labels[0])),
    )
    uds_pozos = st.number_input(
        "Nº pozos",
        min_value=0,
        value=int(st.session_state.get("uds_pozos", 0)),
    )

    tipo_imbornal = st.selectbox(
        "Tipo de imbornal",
        imbornal_labels,
        index=indice_seguro(imbornal_labels, st.session_state.get("tipo_imbornal", imbornal_labels[0])),
    )
    uds_imbornales = st.number_input(
        "Nº imbornales",
        min_value=0,
        value=int(st.session_state.get("uds_imbornales", 0)),
    )

with s3:
    st.markdown("### Marcos y materiales de pozo")
    tipo_marco = st.selectbox(
        "Tipo de marco",
        marco_labels,
        index=indice_seguro(marco_labels, st.session_state.get("tipo_marco", marco_labels[0])),
    )
    uds_marcos = st.number_input(
        "Nº marcos",
        min_value=0,
        value=int(st.session_state.get("uds_marcos", 0)),
    )

    # Tapas de pozo — ahora seleccionables, no hardcodeadas
    tipo_tapa_pozo = st.selectbox(
        "Tipo de tapa/material de pozo",
        mat_pozo_labels,
        index=indice_seguro(mat_pozo_labels, st.session_state.get("tipo_tapa_pozo", mat_pozo_labels[0])),
        help="Selecciona el elemento de la lista de materiales de pozo.",
    )
    uds_tapas_pozo = st.number_input(
        "Nº tapas de pozo",
        min_value=0,
        value=int(st.session_state.get("uds_tapas_pozo", 0)),
    )
    uds_pates_pozo = st.number_input(
        "Nº pates de pozo",
        min_value=0,
        value=int(st.session_state.get("uds_pates_pozo", 0)),
    )

# ==============================================================
# BLOQUE 5 · Fibrocemento y redes provisionales
# ==============================================================
st.markdown("## 5) Fibrocemento / amianto y redes provisionales")
st.markdown(
    """
    <div class="warn-box">
    <b>Fibrocemento:</b> si las tuberías existentes son de fibrocemento, su retirada requiere
    empresa especializada, Plan de Trabajo con Amianto (PTWA) y gestor autorizado de residuos
    peligrosos (RD 396/2006). Estos costes pueden ser <b>significativos</b>. Deja en 0 si no aplica.<br><br>
    <b>Redes provisionales:</b> el PPTP exige mantener servicio a los abonados durante la obra.
    Incluye tubería provisional, conexiones, desinfección y retirada final.
    </div>
    """,
    unsafe_allow_html=True,
)

fb1, fb2 = st.columns(2)
with fb1:
    st.markdown("### Fibrocemento / amianto")
    metros_fibrocemento = st.number_input(
        "Metros de tubería de fibrocemento a retirar (m)",
        min_value=0.0,
        value=float(st.session_state.get("metros_fibrocemento", 0.0)),
        help="Longitud total de tubería de fibrocemento que hay que retirar y gestionar.",
    )
    precio_fibrocemento_m = st.number_input(
        "Precio retirada fibrocemento (€/m)",
        min_value=0.0,
        value=float(st.session_state.get("precio_fibrocemento_m", d.FIBROCEMENTO["retirada_m"])),
        help="Precio orientativo: embolsado, transporte y gestión en vertedero autorizado.",
    )
    importe_plan_amianto = st.number_input(
        "Importe Plan de Trabajo con Amianto — fijo (€)",
        min_value=0.0,
        value=float(st.session_state.get("importe_plan_amianto", d.FIBROCEMENTO["plan_trabajo_fijo"])),
        help="Coste fijo de redacción del PTWA, coordinación y documentación. Ajustar según empresa.",
    )

with fb2:
    st.markdown("### Redes provisionales de suministro")
    metros_red_provisional = st.number_input(
        "Metros de red provisional (m)",
        min_value=0.0,
        value=float(st.session_state.get("metros_red_provisional", 0.0)),
        help="Metros de tubería provisional para mantener servicio a abonados durante la obra.",
    )
    precio_red_provisional_m = st.number_input(
        "Precio red provisional (€/m)",
        min_value=0.0,
        value=float(st.session_state.get("precio_red_provisional_m", d.REDES_PROVISIONALES["tuberia_provisional_m"])),
        help="Precio orientativo por metro de tubería flexible provisional instalada y retirada.",
    )
    importe_montaje_provisional = st.number_input(
        "Montaje y desmontaje provisional — fijo (€)",
        min_value=0.0,
        value=float(st.session_state.get("importe_montaje_provisional", d.REDES_PROVISIONALES["montaje_desmontaje_fijo"])),
        help="Coste fijo de conexiones, llaves de corte provisionales, desinfección y retirada final.",
    )

# ==============================================================
# BLOQUE 6 · Costes indirectos, SS, GA
# ==============================================================
st.markdown("## 6) Servicios afectados, seguridad y salud, gestión ambiental")
st.markdown(
    """
    <div class="soft-box">
    <b>Servicios afectados</b> se aplica como porcentaje sobre el subtotal directo.
    <b>Seguridad y salud</b> y <b>gestión ambiental</b> pueden ir como importe fijo o porcentaje.
    </div>
    """,
    unsafe_allow_html=True,
)

o1, o2, o3 = st.columns(3)
with o1:
    nivel_servicios = st.selectbox(
        "Nivel de servicios afectados",
        servicios_labels,
        index=indice_seguro(servicios_labels, st.session_state.get("nivel_servicios", servicios_labels[0])),
        help="Porcentaje tomado de la familia 'Servicios afectados' del CSV.",
    )
with o2:
    modo_ss = st.radio(
        "Seguridad y salud",
        ["fijo", "porcentaje"],
        horizontal=True,
        index=0 if st.session_state.get("modo_ss", d.MODO_SS_DEFAULT) == "fijo" else 1,
    )
    importe_ss = st.number_input(
        "Importe SS (€)",
        min_value=0.0,
        value=float(st.session_state.get("importe_ss", d.IMPORTE_SS_DEFAULT)),
    )
    pct_ss = st.number_input(
        "SS (%)",
        min_value=0.0, max_value=100.0,
        value=float(d.PCT_SS_CSV * 100),
        help="Valor de referencia del CSV: 3%.",
    )
with o3:
    modo_ga = st.radio(
        "Gestión ambiental",
        ["fijo", "porcentaje"],
        horizontal=True,
        index=0 if st.session_state.get("modo_ga", d.MODO_GA_DEFAULT) == "fijo" else 1,
    )
    importe_ga = st.number_input(
        "Importe GA (€)",
        min_value=0.0,
        value=float(st.session_state.get("importe_ga", d.IMPORTE_GA_DEFAULT)),
    )
    pct_ga = st.number_input(
        "GA (%)",
        min_value=0.0, max_value=100.0,
        value=4.0,
        help="Si prefieres estimarla como porcentaje.",
    )

st.markdown("### Ajuste comercial opcional")
aj1, aj2 = st.columns(2)
with aj1:
    activar_colchon = st.checkbox(
        "Añadir colchón comercial",
        value=bool(st.session_state.get("activar_colchon", d.COLCHON_ACTIVO_DEFAULT)),
        help="No es obligatorio. Sirve solo para simulación comercial.",
    )
with aj2:
    pct_colchon = st.number_input(
        "Colchón (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get("pct_colchon", 10.0)),
    )

# ==============================================================
# Preparación de catálogos elegidos
# ==============================================================
precios_aba   = buscar_por_label(d.CATALOGO_ABA, tipo_aba)
precios_aba2  = buscar_por_label(d.CATALOGO_ABA, tipo_aba2)
precios_san   = buscar_por_label(d.CATALOGO_SAN, tipo_san)
precio_ovoide = buscar_por_label(d.CATALOGO_OVOIDE, tipo_ovoide)["tuberia_m"]

precio_dem_bordillo = buscar_por_label(d.DEMOLICION_BORDILLO, tipo_dem_bordillo)["precio_m"]
precio_dem_acerado  = buscar_por_label(d.DEMOLICION_ACERADO,  tipo_dem_acerado)["precio_m2"]
precio_dem_calzada  = buscar_por_label(d.DEMOLICION_CALZADA,  tipo_dem_calzada)["precio_m2"]
precio_rep_acerado  = buscar_por_label(d.ACERADOS_REPOSICION, tipo_rep_acerado)["precio_m2"]
precio_rep_bordillo = buscar_por_label(d.BORDILLOS_REPOSICION, tipo_rep_bordillo)["precio_m"]

precio_acometida_aba = buscar_por_label(d.ACOMETIDAS, tipo_acometida_aba)["precio_ud"]
precio_acometida_san = buscar_por_label(d.ACOMETIDAS, tipo_acometida_san)["precio_ud"]
precio_pozo          = buscar_por_label(d.POZOS,      tipo_pozo)["precio_ud"]
precio_imbornal      = buscar_por_label(d.IMBORNALES, tipo_imbornal)["precio_ud"]
precio_marco         = buscar_por_label(d.MARCOS,     tipo_marco)["precio_ud"]
precio_tapa_pozo     = buscar_por_label(d.MATERIALES_POZO, tipo_tapa_pozo)["precio_ud"]
precio_pate_pozo     = buscar_por_label(d.MATERIALES_POZO, "Pate para pozos")["precio_ud"]
pct_servicios        = buscar_por_label(d.SERVICIOS_AFECTADOS, nivel_servicios)["pct"]

# ==============================================================
# Cálculo
# ==============================================================
st.markdown("## 7) Calcular")
st.markdown(
    """
    <div class="soft-box">
    Cuando pulses el botón, la app construirá el presupuesto completo y te enseñará:
    resumen económico, capítulos detallados y cantidades auxiliares.
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("Calcular presupuesto", type="primary", use_container_width=True):
    parametros = ParametrosProyecto(
        # Redes
        metros_aba=metros_aba,
        precios_aba=precios_aba,
        metros_aba2=metros_aba2,
        precios_aba2=precios_aba2,
        metros_san=metros_san,
        precios_san=precios_san,
        metros_ovoide=metros_ovoide,
        precio_ovoide_m=precio_ovoide,

        # Geometría y excavación
        ancho_zanja_aba_m=ancho_zanja_aba,
        profundidad_aba_m=profundidad_aba,
        ancho_zanja_san_m=ancho_zanja_san,
        profundidad_san_m=profundidad_san,
        pct_exc_manual_aba=pct_manual_aba / 100,
        pct_exc_manual_san=pct_manual_san / 100,
        pct_entibacion_aba=pct_entibacion_aba / 100,
        pct_entibacion_san=pct_entibacion_san / 100,

        # Materiales auxiliares
        espesor_arena_aba_m=espesor_arena_aba,
        espesor_arena_san_m=espesor_arena_san,
        espesor_relleno_aba_m=espesor_relleno_aba,
        espesor_relleno_san_m=espesor_relleno_san,

        # Demoliciones
        dem_bordillo_m=dem_bordillo_m,
        precio_dem_bordillo_m=precio_dem_bordillo,
        dem_acerado_m2=dem_acerado_m2,
        precio_dem_acerado_m2=precio_dem_acerado,
        dem_calzada_m2=dem_calzada_m2,
        precio_dem_calzada_m2=precio_dem_calzada,
        espesor_dem_calzada_m=espesor_dem_calzada,
        uds_dem_arqueta_imbornal=uds_dem_arqueta_imbornal,
        precio_dem_arqueta_imbornal_ud=d.REPOSICION_CALZADA["demolicion_arqueta_imbornal_ud"],
        uds_dem_imbornal_tuberia=uds_dem_imbornal_tuberia,
        precio_dem_imbornal_tuberia_ud=d.REPOSICION_CALZADA["demolicion_imbornal_tuberia_ud"],

        # Reposiciones
        rep_acerado_m2=rep_acerado_m2,
        precio_rep_acerado_m2=precio_rep_acerado,
        rep_bordillo_m=rep_bordillo_m,
        precio_rep_bordillo_m=precio_rep_bordillo,
        rep_adoquin_m2=rep_adoquin_m2,
        precio_rep_adoquin_m2=d.REPOSICION_CALZADA["adoquin_m2"],
        rep_rodadura_m2=rep_rodadura_m2,
        precio_rodadura_m3=d.REPOSICION_CALZADA["rodadura_m3"],
        espesor_rodadura_m=espesor_rodadura,
        rep_base_pavimento_m2=rep_base_pavimento_m2,
        precio_base_pavimento_m3=d.REPOSICION_CALZADA["base_pavimento_m3"],
        espesor_base_pavimento_m=espesor_base_pavimento,
        rep_hormigon_m2=rep_hormigon_m2,
        precio_hormigon_m3=d.REPOSICION_CALZADA["hormigon_m3"],
        espesor_hormigon_m=espesor_hormigon,
        rep_base_granular_m2=rep_base_granular_m2,
        precio_base_granular_m3=d.REPOSICION_CALZADA["base_granular_m3"],
        espesor_base_granular_m=espesor_base_granular,

        # Excavación y transporte — precios unitarios
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

        # Elementos singulares
        uds_valvulas=uds_valvulas,
        precio_valvula=precio_valvula,
        uds_tomas_agua=uds_tomas_agua,
        precio_toma_agua=precio_toma_agua,
        uds_conexiones_aba=uds_conexiones_aba,
        precio_conexion_aba=precio_conexion_aba,
        uds_conexiones_san=uds_conexiones_san,
        precio_conexion_san=precio_conexion_san,

        # Acometidas
        uds_acometidas_aba=uds_acometidas_aba,
        precio_acometida_aba_ud=precio_acometida_aba,
        uds_acometidas_san=uds_acometidas_san,
        precio_acometida_san_ud=precio_acometida_san,

        # Pozos, imbornales, marcos y materiales
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

        # Fibrocemento / amianto
        metros_fibrocemento=metros_fibrocemento,
        precio_fibrocemento_m=precio_fibrocemento_m,
        importe_plan_amianto=importe_plan_amianto,

        # Redes provisionales
        metros_red_provisional=metros_red_provisional,
        precio_red_provisional_m=precio_red_provisional_m,
        importe_montaje_provisional=importe_montaje_provisional,

        # Otros costes
        pct_servicios_afectados=pct_servicios,
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

    # ----------------------------------------------------------
    # RESUMEN ECONÓMICO
    # ----------------------------------------------------------
    st.markdown("## 8) Resultado económico")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PEM",              euro(resultado["pem"]))
    m2.metric("PBL sin IVA",      euro(resultado["pbl_sin_iva"]))
    m3.metric("IVA",              euro(resultado["iva"]))
    m4.metric("Total presupuesto", euro(resultado["total"]))

    st.markdown(
        f"""
        <div class="note-box">
        <b>Cómo se forma el total:</b><br>
        Presupuesto directo → PEM → + {int(d.PCT_GG*100)}% GG → + {int(d.PCT_BI*100)}% BI
        → + {int(d.PCT_IVA*100)}% IVA.
        <br><br>
        <b>Control de calidad de referencia:</b> {euro(resultado["control_calidad_referencia"])}
        ({int(d.PCT_CONTROL_CALIDAD*100)}% del PEM). Se muestra como referencia interna y no se
        suma al total.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # TABLAS DE DESGLOSE
    # ----------------------------------------------------------
    st.markdown("### Desglose por partidas")

    filas_directas = [
        ("Tubería ABA — Tramo 1",              resultado["tuberia_aba"]),
        ("Tubería ABA — Tramo 2",              resultado["tuberia_aba2"]),
        ("Tubería SAN",                        resultado["tuberia_san"]),
        ("Tubería ovoide",                     resultado["tuberia_ovoide"]),
        ("Excavación mecánica ABA",            resultado["exc_mecanica_aba"]),
        ("Excavación manual ABA",              resultado["exc_manual_aba"]),
        ("Excavación mecánica SAN",            resultado["exc_mecanica_san"]),
        ("Excavación manual SAN",              resultado["exc_manual_san"]),
        ("Entibación ABA",                     resultado["entibacion_aba"]),
        ("Entibación SAN",                     resultado["entibacion_san"]),
        ("Carga de tierras (neto)",            resultado["carga_tierras"]),
        ("Transporte a vertedero (neto)",      resultado["transporte_tierras"]),
        ("Cánon vertedero — tierras",          resultado["canon_tierras"]),
        ("Cánon vertedero — RCD demolición",   resultado["canon_mixto"]),
        ("Arena",                              resultado["arena"]),
        ("Relleno / albero",                   resultado["relleno"]),
        ("Demolición de bordillo",             resultado["dem_bordillo"]),
        ("Demolición de acerado",              resultado["dem_acerado"]),
        ("Demolición de calzada",              resultado["dem_calzada"]),
        ("Demolición de arqueta de imbornal",  resultado["dem_arqueta_imbornal"]),
        ("Demolición de imbornal y tubería",   resultado["dem_imbornal_tuberia"]),
        ("Reposición de acerado",              resultado["rep_acerado"]),
        ("Reposición de bordillo",             resultado["rep_bordillo"]),
        ("Reposición de adoquín",              resultado["rep_adoquin"]),
        ("Capa de rodadura",                   resultado["rep_rodadura"]),
        ("Base de pavimento",                  resultado["rep_base_pavimento"]),
        ("Hormigón",                           resultado["rep_hormigon"]),
        ("Base granular",                      resultado["rep_base_granular"]),
        ("Válvulas",                           resultado["valvulas"]),
        ("Tomas de agua",                      resultado["tomas_agua"]),
        ("Conexiones ABA",                     resultado["conexiones_aba"]),
        ("Conexiones SAN",                     resultado["conexiones_san"]),
        ("Acometidas ABA",                     resultado["acometidas_aba"]),
        ("Acometidas SAN",                     resultado["acometidas_san"]),
        ("Pozos",                              resultado["pozos"]),
        ("Imbornales",                         resultado["imbornales"]),
        ("Marcos",                             resultado["marcos"]),
        ("Tapas de pozo",                      resultado["tapas_pozo"]),
        ("Pates de pozo",                      resultado["pates_pozo"]),
        ("Retirada fibrocemento",              resultado["fibrocemento"]),
        ("Plan de Trabajo con Amianto (PTWA)", resultado["plan_amianto"]),
        ("Tubería provisional",                resultado["red_provisional"]),
        ("Montaje/desmontaje red provisional", resultado["montaje_provisional"]),
    ]

    df_directo = pd.DataFrame(
        [{"Concepto": nombre, "Importe": euro(valor)} for nombre, valor in filas_directas if valor != 0]
    )
    st.dataframe(df_directo, use_container_width=True, hide_index=True)

    st.markdown("### Costes generales y estructura final")
    filas_finales = [
        ("Subtotal directo",      resultado["parcial_directo"]),
        ("Servicios afectados",   resultado["servicios_afectados"]),
        ("Seguridad y salud",     resultado["seguridad_salud"]),
        ("Gestión ambiental",     resultado["gestion_ambiental"]),
        ("PEM",                   resultado["pem"]),
        ("Gastos generales",      resultado["gastos_generales"]),
        ("Beneficio industrial",  resultado["beneficio_industrial"]),
        ("PBL base",              resultado["pbl_base"]),
        ("Colchón comercial",     resultado["colchon_comercial"]),
        ("PBL sin IVA",           resultado["pbl_sin_iva"]),
        ("IVA",                   resultado["iva"]),
        ("TOTAL",                 resultado["total"]),
    ]
    df_final = pd.DataFrame([{"Concepto": n, "Importe": euro(v)} for n, v in filas_finales])
    st.dataframe(df_final, use_container_width=True, hide_index=True)

    st.markdown("### Cantidades auxiliares")
    st.markdown(
        """
        <div class="soft-box small-text">
        Estas cantidades no son el presupuesto final, pero te ayudan a entender de dónde sale:
        volumen bruto de zanja, lo que queda en zanja (arena + relleno), volumen neto a
        transportar, volumen de RCD de demolición y superficies de entibación.
        </div>
        """,
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns(3)
    q1.metric("Vol. bruto zanja ABA", f"{resultado['vol_zanja_aba']:.2f} m³")
    q2.metric("Vol. bruto zanja SAN", f"{resultado['vol_zanja_san']:.2f} m³")
    q3.metric("Vol. en zanja (arena+relleno)", f"{resultado['vol_en_zanja']:.2f} m³")

    q4, q5, q6 = st.columns(3)
    q4.metric("Vol. neto tierras a vertedero", f"{resultado['vol_total_tierras']:.2f} m³")
    q5.metric("Vol. RCD calzada demolida",     f"{resultado['vol_rcd_calzada']:.2f} m³")
    q6.metric("Arena total",                   f"{resultado['vol_arena_total']:.2f} m³")

    q7, q8, q9 = st.columns(3)
    q7.metric("Relleno total",       f"{resultado['vol_relleno_total']:.2f} m³")
    q8.metric("Entibación ABA",      f"{resultado['area_entibacion_aba']:.2f} m²")
    q9.metric("Entibación SAN",      f"{resultado['area_entibacion_san']:.2f} m²")

else:
    st.info("Rellena los datos y pulsa «Calcular presupuesto» para ver el resultado.")
