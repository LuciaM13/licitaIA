"""Página de cálculo de presupuestos EMASESA."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import config as dc
from src.presupuesto import calcular_presupuesto
from src.config import ParametrosProyecto
from src.utils import validar_parametros
from src.precios import cargar_precios
from src.precios import euro
from src.utils import find_by_label, find_item, generar_texto_word


# ─── Cargar precios desde JSON ────────────────────────────────────────────────

precios = cargar_precios()

CATALOGO_ABA = precios["catalogo_aba"]
CATALOGO_SAN = precios["catalogo_san"]
ACERADOS_ABA = precios["acerados_aba"]
ACERADOS_SAN = precios["acerados_san"]
BORDILLOS_REPOSICION = precios["bordillos_reposicion"]
CALZADAS_REPOSICION = precios["calzadas_reposicion"]


# ─── Cabecera ────────────────────────────────────────────────────────────────

st.title("Cálculo de presupuestos")
st.caption("Introduce los datos mínimos del proyecto. "
           "La app calcula automáticamente excavación, elementos "
           "(válvulas, pozos, conexiones, desagües, hidrantes, ventosas), "
           "conducción provisional, materiales, GG, BI e IVA.")


# ─── Selector de modo ──────────────────────────────────────────────────────

modo = st.radio(
    "Tipo de actuación",
    ["Solo Abastecimiento", "Solo Saneamiento", "Abastecimiento + Saneamiento"],
    horizontal=True,
)
incluir_aba = modo in ("Solo Abastecimiento", "Abastecimiento + Saneamiento")
incluir_san = modo in ("Solo Saneamiento", "Abastecimiento + Saneamiento")


# ─── Helpers de UI ────────────────────────────────────────────────────────


def _mostrar_resultados(r: dict) -> None:
    st.markdown("## Resumen económico")

    if r.get("pct_seguridad_info", 0) > 0 or r.get("pct_gestion_info", 0) > 0:
        st.info(f"Seguridad y Salud representa el **{r['pct_seguridad_info']:.2f}%** del subtotal de obra · "
                f"Gestión Ambiental representa el **{r['pct_gestion_info']:.2f}%** del subtotal de obra")

    metrics = [
        ("PEM", r["pem"]),
        ("PBL sin IVA", r["pbl_sin_iva"]),
        ("IVA", r["iva"]),
        ("TOTAL", r["total"]),
    ]
    for col, (label, val) in zip(st.columns(len(metrics)), metrics):
        col.metric(label, euro(val))

    st.markdown("### Partidas de cada capítulo")
    for cap, info in r["capitulos"].items():
        with st.expander(f"{cap} · {euro(info['subtotal'])}"):
            df = pd.DataFrame([{"Partida": nombre, "Importe": euro(v)}
                               for nombre, v in info["partidas"].items() if v != 0])
            if df.empty:
                st.info("Sin partidas en este capítulo.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Cálculos automáticos de zanja")
    aux_rows = []
    if r["auxiliares"]["aba"]:
        aux_rows.append({"Red": "ABA", **r["auxiliares"]["aba"]})
    if r["auxiliares"]["san"]:
        aux_rows.append({"Red": "SAN", **r["auxiliares"]["san"]})
    if aux_rows:
        st.dataframe(pd.DataFrame(aux_rows), use_container_width=True, hide_index=True)

    st.markdown("### Bloque listo para copiar a Word")
    st.text_area("Texto del presupuesto", value=generar_texto_word(r), height=320)


def _input_tuberia(prefix: str, catalogo: list, default_longitud: float,
                   default_profundidad: float) -> tuple[dict, float, float]:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        longitud = st.number_input(f"{prefix} Longitud (m)", min_value=0.0, value=default_longitud)
    with c2:
        tipo = st.selectbox(f"{prefix} Tipo de tubería", sorted({x["tipo"] for x in catalogo}))
    with c3:
        diametro = st.selectbox(f"{prefix} Diámetro (mm)",
                                sorted({x["diametro_mm"] for x in catalogo if x["tipo"] == tipo}))
    with c4:
        profundidad = st.number_input(f"{prefix} Profundidad (m)", min_value=0.0, value=default_profundidad)
    item = find_item(catalogo, tipo, diametro)
    st.info(f"Tubería {prefix}: {item['label']} · {item['precio_m']} €/m")
    return item, longitud, profundidad


# ─── Valores por defecto para secciones no activas ─────────────────────────
aba_item = None
aba_longitud_m = 0.0
aba_profundidad_m = dc.ABA_PROFUNDIDAD_M
pav_aba_acerado_m2 = 0.0
pav_aba_acerado_item = ACERADOS_ABA[0]
pav_aba_bordillo_m = 0.0
pav_aba_bordillo_item = BORDILLOS_REPOSICION[0]
acometidas_aba_n = 0

san_item = None
san_longitud_m = 0.0
san_profundidad_m = dc.SAN_PROFUNDIDAD_M
pav_san_calzada_m2 = 0.0
pav_san_calzada_item = CALZADAS_REPOSICION[0]
pav_san_acera_m2 = 0.0
pav_san_acera_item = ACERADOS_SAN[0]
acometidas_san_n = 0


# ─── Sección ABA ───────────────────────────────────────────────────────────

if incluir_aba:
    st.markdown("## 1) Abastecimiento")
    aba_item, aba_longitud_m, aba_profundidad_m = _input_tuberia(
        "ABAS", CATALOGO_ABA, dc.ABA_LONGITUD_M, dc.ABA_PROFUNDIDAD_M)


# ─── Sección SAN ───────────────────────────────────────────────────────────

if incluir_san:
    st.markdown("## 2) Saneamiento")
    san_item, san_longitud_m, san_profundidad_m = _input_tuberia(
        "SAN", CATALOGO_SAN, dc.SAN_LONGITUD_M, dc.SAN_PROFUNDIDAD_M)


# ─── Pavimentación ABA ─────────────────────────────────────────────────────

if incluir_aba:
    st.markdown("## 3) Pavimentación abastecimiento")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        pav_aba_acerado_m2 = st.number_input("Pav ABAS · m² de acerado", min_value=0.0, value=dc.PAV_ABA_ACERADO_M2)
    with p2:
        pav_aba_acerado_label = st.selectbox("Pav ABAS · tipo de acerado", [x["label"] for x in ACERADOS_ABA])
    with p3:
        pav_aba_bordillo_m = st.number_input("Pav ABAS · longitud bordillo (m)", min_value=0.0, value=dc.PAV_ABA_BORDILLO_M)
    with p4:
        pav_aba_bordillo_label = st.selectbox("Pav ABAS · tipo de bordillo", [x["label"] for x in BORDILLOS_REPOSICION])
    pav_aba_acerado_item = find_by_label(ACERADOS_ABA, pav_aba_acerado_label)
    pav_aba_bordillo_item = find_by_label(BORDILLOS_REPOSICION, pav_aba_bordillo_label)


# ─── Pavimentación SAN ─────────────────────────────────────────────────────

if incluir_san:
    st.markdown("## 4) Pavimentación saneamiento")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        pav_san_calzada_m2 = st.number_input("Pav SAN · m² de calzada", min_value=0.0, value=dc.PAV_SAN_CALZADA_M2)
    with q2:
        pav_san_calzada_label = st.selectbox("Pav SAN · tipo de calzada", [x["label"] for x in CALZADAS_REPOSICION])
    with q3:
        pav_san_acera_m2 = st.number_input("Pav SAN · m² de acera", min_value=0.0, value=dc.PAV_SAN_ACERA_M2)
    with q4:
        pav_san_acera_label = st.selectbox("Pav SAN · tipo de acera", [x["label"] for x in ACERADOS_SAN])
    pav_san_calzada_item = find_by_label(CALZADAS_REPOSICION, pav_san_calzada_label)
    pav_san_acera_item = find_by_label(ACERADOS_SAN, pav_san_acera_label)
    espesores = precios["espesores_calzada"]
    if pav_san_calzada_item["unidad"] == "m3":
        esp = espesores[pav_san_calzada_item["label"]]
        st.info(f"Calzada {pav_san_calzada_item['label']}: conversión automática m² → m³ con espesor {esp:.2f} m.")


# ─── Acometidas ─────────────────────────────────────────────────────────────

st.markdown("## 5) Acometidas")
c1, c2 = st.columns(2)
with c1:
    if incluir_aba:
        acometidas_aba_n = int(st.number_input("Nº acometidas ABA", min_value=0, value=dc.ACOMETIDAS_N))
with c2:
    if incluir_san:
        acometidas_san_n = int(st.number_input("Nº acometidas SAN", min_value=0, value=dc.ACOMETIDAS_N))


# ─── Seguridad y Gestión ──────────────────────────────────────────────────

st.markdown("## 6) Seguridad y Gestión")
g1, g2 = st.columns(2)
with g1:
    importe_seguridad = st.number_input("Seguridad y Salud (€)", min_value=0.0, value=dc.IMPORTE_SEGURIDAD)
with g2:
    importe_gestion = st.number_input("Gestión Ambiental (€)", min_value=0.0, value=dc.IMPORTE_GESTION)


# ─── Calcular ──────────────────────────────────────────────────────────────

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
        importe_seguridad=importe_seguridad,
        importe_gestion=importe_gestion,
    )
    errores = validar_parametros(p)
    if errores:
        for e in errores:
            st.error(e)
        st.stop()

    r = calcular_presupuesto(p, precios)
    _mostrar_resultados(r)
else:
    st.info("Introduce los datos mínimos y pulsa 'Calcular presupuesto'.")
