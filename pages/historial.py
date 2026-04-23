"""Página de historial de presupuestos generados."""

from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

from src.aplicacion.historial import (
    listar_presupuestos,
    obtener_presupuesto,
    eliminar_presupuesto,
    contar_presupuestos,
)
from src.infraestructura.utils import euro
from src.ui.session import claves as sk

_ETIQUETAS_TRAZ = ["Entibación", "Pozo de registro", "Valvulería", "Desmontaje"]


def _mostrar_trazabilidad(traz: dict[str, list[str]], *, titulo: str = "Decisiones del sistema experto") -> None:
    """Renderiza la trazabilidad de un presupuesto en un expander."""
    if not traz:
        return
    with st.expander(titulo, expanded=False):
        for red, explicaciones in traz.items():
            if explicaciones:
                st.markdown(f"**Red {red}**")
                for etiqueta, frase in zip(_ETIQUETAS_TRAZ, explicaciones):
                    st.markdown(f"- **{etiqueta}:** {frase}")


# ─── Cabecera ────────────────────────────────────────────────────────────────

st.title("Historial de presupuestos")
st.caption("Consulta, compara y revisa los presupuestos generados anteriormente.")

total = contar_presupuestos()
logger.info("Historial cargado: %d presupuestos guardados", total)
if total == 0:
    st.info("Aún no se ha guardado ningún presupuesto. "
            "Genera uno desde la **Calculadora** y pulsa **Guardar en historial** para conservarlo aquí.")
    st.stop()

st.metric("Presupuestos guardados", total)

# ─── Listado ─────────────────────────────────────────────────────────────────

PAGE_SIZE = 20
if sk.HIST_PAGE not in st.session_state:
    st.session_state[sk.HIST_PAGE] = 0

offset = st.session_state[sk.HIST_PAGE] * PAGE_SIZE
lista = listar_presupuestos(limit=PAGE_SIZE, offset=offset)

# Guard: si offset desborda (paginación manual o estado obsoleto), retroceder a página 0
if not lista and offset > 0:
    st.session_state[sk.HIST_PAGE] = 0
    st.rerun()

df = pd.DataFrame(lista)
df = df.rename(columns={
    "id": "ID", "creado_en": "Fecha",
    "descripcion": "Descripción", "pem": "PEM (€)", "total": "Total (€)"
})
if not df.empty:
    df["PEM (€)"] = df["PEM (€)"].apply(lambda x: euro(x))
    df["Total (€)"] = df["Total (€)"].apply(lambda x: euro(x))

st.dataframe(df, use_container_width=True, hide_index=True)

# Paginación
pagina_actual = st.session_state[sk.HIST_PAGE] + 1
total_paginas = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

col_prev, col_info, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("← Anterior", disabled=st.session_state[sk.HIST_PAGE] == 0):
        st.session_state[sk.HIST_PAGE] -= 1
        st.rerun()
with col_info:
    st.markdown(f"Página **{pagina_actual}** de **{total_paginas}**")
with col_next:
    if st.button("Siguiente →", disabled=offset + PAGE_SIZE >= total):
        st.session_state[sk.HIST_PAGE] += 1
        st.rerun()

# ─── Detalle de un presupuesto ───────────────────────────────────────────────

# Diccionario de traducción de claves internas → nombres legibles
_NOMBRES_PARAMETROS = {
    # ── General ──────────────────────────────────────────────────────────────
    "modo":                        "Tipo de actuación",
    # ── ABA - Tubería ─────────────────────────────────────────────────────────
    "aba_tuberia":                 "Tubería ABA",
    "aba_longitud_m":              "Longitud ABA (m)",
    "aba_profundidad_m":           "Profundidad ABA (m)",
    "aba_diametro_mm":             "Diámetro ABA (mm)",
    "instalacion_valvuleria":      "Instalación valvulería",
    # ── ABA - Pavimentación ───────────────────────────────────────────────────
    "pav_aba_acerado_m2":          "Acerado ABA (m²)",
    "pav_aba_acerado_label":       "Tipo acerado ABA",
    "pav_aba_bordillo_m":          "Bordillo ABA (m)",
    "pav_aba_bordillo_label":      "Tipo bordillo ABA",
    "subbase_aba_espesor_m":       "Espesor sub-base ABA (m)",
    # ── ABA - Otros ──────────────────────────────────────────────────────────
    "acometidas_aba_n":            "Acometidas ABA (ud)",
    "conduccion_provisional_m":    "Conducción provisional (m)",
    "pozos_existentes_aba":        "Pozos existentes ABA",
    "desmontaje_tipo":             "Desmontaje tubería",
    # ── SAN - Tubería ─────────────────────────────────────────────────────────
    "san_tuberia":                 "Tubería SAN",
    "san_longitud_m":              "Longitud SAN (m)",
    "san_profundidad_m":           "Profundidad SAN (m)",
    "san_diametro_mm":             "Diámetro SAN (mm)",
    # ── SAN - Pavimentación ───────────────────────────────────────────────────
    "pav_san_calzada_m2":          "Calzada SAN (m²)",
    "pav_san_calzada_label":       "Tipo calzada SAN",
    "pav_san_acera_m2":            "Acera SAN (m²)",
    "pav_san_acera_label":         "Tipo acera SAN",
    "subbase_san_espesor_m":       "Espesor sub-base SAN (m)",
    # ── SAN - Otros ──────────────────────────────────────────────────────────
    "acometidas_san_n":            "Acometidas SAN (ud)",
    "pozos_existentes_san":        "Pozos existentes SAN",
    "imbornales_tipo":             "Imbornales SAN",
    "imbornales_nuevo_label":      "Tipo imbornal nuevo SAN",
    # ── Obra general ─────────────────────────────────────────────────────────
    "pct_manual":                  "% Excavación manual",
    "pct_seguridad":               "% Seguridad y Salud",
    "pct_gestion":                 "% Gestión Ambiental",
    "pct_servicios_afectados":     "% Servicios afectados",
    "espesor_pavimento_m":         "Espesor pavimento demolido (m)",
}

st.markdown("---")
st.markdown("## Consultar detalle")
st.caption("Selecciona un presupuesto de la lista para ver su desglose completo.")

ids_disponibles = [item["id"] for item in lista]
if not ids_disponibles:
    st.stop()

presupuesto_id = st.selectbox(
    "Presupuesto",
    ids_disponibles,
    format_func=lambda x: next(
        (f"#{x} · {item['descripcion'] or 'Sin descripción'}  -  {item['creado_en']}"
         for item in lista if item["id"] == x),
        str(x),
    ),
)

if st.button("Ver detalle", type="primary"):
    logger.info("Consultando detalle del presupuesto #%s", presupuesto_id)
    st.session_state[sk.VER_DETALLE_ID] = presupuesto_id

# Mostrar detalle solo si el usuario ha pulsado el botón
# (o si ya había uno cargado previamente en session_state)
_detalle_id = st.session_state.get(sk.VER_DETALLE_ID)
if _detalle_id is not None:
    detalle = obtener_presupuesto(_detalle_id)
    if detalle is None:
        st.error("Presupuesto no encontrado.")
    else:
        st.markdown(f"### Presupuesto #{_detalle_id} - {detalle.get('descripcion') or 'Sin descripción'}")

        # ── Resumen financiero ────────────────────────────────────────────
        st.markdown("#### Resumen económico")

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"**PEM**\n\n### {euro(detalle['pem'])}")
        m2.markdown(f"**PBL sin IVA**\n\n### {euro(detalle['pbl_sin_iva'])}")
        m3.markdown(f"**IVA (21%)**\n\n### {euro(detalle['iva'])}")
        m4.markdown(f"**TOTAL**\n\n### {euro(detalle['total'])}")

        f1, f2 = st.columns(2)
        f1.markdown(
            f"**Gastos Generales - GG** ({detalle['pct_gg']*100:.0f}%): {euro(detalle['gg'])}"
        )
        f2.markdown(
            f"**Beneficio Industrial - BI** ({detalle['pct_bi']*100:.0f}%): {euro(detalle['bi'])}"
        )

        # ── Capítulos ─────────────────────────────────────────────────────
        st.markdown("#### Capítulos")
        st.caption("Cada capítulo agrupa las partidas de obra de una categoría. Pulsa para desplegar el desglose.")
        for cap_nombre, cap_info in detalle.get("capitulos", {}).items():
            with st.expander(f"{cap_nombre} · {euro(cap_info['subtotal'])}"):
                partidas = cap_info.get("partidas", {})
                if partidas:
                    df_p = pd.DataFrame([
                        {"Partida": nombre, "Importe": euro(v)}
                        for nombre, v in partidas.items() if v != 0
                    ])
                    if not df_p.empty:
                        st.dataframe(df_p, use_container_width=True, hide_index=True)
                    else:
                        st.info("Sin partidas con importe en este capítulo.")
                else:
                    st.info("Sin partidas en este capítulo.")

        # ── Trazabilidad (decisiones del sistema experto) ──────────────────
        _mostrar_trazabilidad(detalle.get("trazabilidad", {}))

        # ── Parámetros de entrada ─────────────────────────────────────────
        params = detalle.get("parametros", {})
        if params:
            st.markdown("#### Parámetros de entrada")
            st.caption("Valores introducidos por el usuario al generar este presupuesto.")
            df_params = pd.DataFrame([
                {"Parámetro": _NOMBRES_PARAMETROS.get(k, k), "Valor": v}
                for k, v in sorted(params.items())
            ])
            st.dataframe(df_params, use_container_width=True, hide_index=True)

# ─── Comparación de dos presupuestos ─────────────────────────────────────────

st.markdown("---")
st.markdown("## Comparar presupuestos")

todos_ids = [item["id"] for item in listar_presupuestos(limit=200)]
if len(todos_ids) >= 2:
    c1, c2 = st.columns(2)
    with c1:
        id_a = st.selectbox("Presupuesto A", todos_ids, index=0, key="comp_a")
    with c2:
        id_b = st.selectbox("Presupuesto B", todos_ids,
                            index=min(1, len(todos_ids) - 1), key="comp_b")

    if id_a != id_b and st.button("Comparar", type="primary"):
        logger.info("Comparando presupuestos #%s y #%s", id_a, id_b)
        det_a = obtener_presupuesto(id_a)
        det_b = obtener_presupuesto(id_b)
        if det_a and det_b:
            campos = ["pem", "gg", "bi", "pbl_sin_iva", "iva", "total"]
            labels = ["PEM", "GG", "BI", "PBL sin IVA", "IVA", "Total"]
            rows = []
            for campo, label in zip(campos, labels):
                va = det_a[campo]
                vb = det_b[campo]
                diff = vb - va
                pct = (diff / va * 100) if va != 0 else 0
                rows.append({
                    "Concepto": label,
                    f"#{id_a}": euro(va),
                    f"#{id_b}": euro(vb),
                    "Diferencia": euro(diff),
                    "Δ %": f"{pct:+.1f}%",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Comparación por capítulos
            caps_a = det_a.get("capitulos", {})
            caps_b = det_b.get("capitulos", {})
            all_caps = list(dict.fromkeys(list(caps_a.keys()) + list(caps_b.keys())))
            if all_caps:
                st.markdown("#### Por capítulos")
                rows_cap = []
                for cap in all_caps:
                    sa = caps_a.get(cap, {}).get("subtotal", 0)
                    sb = caps_b.get(cap, {}).get("subtotal", 0)
                    diff = sb - sa
                    rows_cap.append({
                        "Capítulo": cap,
                        f"#{id_a}": euro(sa),
                        f"#{id_b}": euro(sb),
                        "Diferencia": euro(diff),
                    })
                st.dataframe(pd.DataFrame(rows_cap), use_container_width=True,
                             hide_index=True)

            # Trazabilidad lado a lado
            traz_a = det_a.get("trazabilidad", {})
            traz_b = det_b.get("trazabilidad", {})
            if traz_a or traz_b:
                st.markdown("#### Decisiones del sistema experto")
                col_ta, col_tb = st.columns(2)
                with col_ta:
                    _mostrar_trazabilidad(
                        traz_a, titulo=f"Presupuesto #{id_a}")
                with col_tb:
                    _mostrar_trazabilidad(
                        traz_b, titulo=f"Presupuesto #{id_b}")
    elif id_a == id_b:
        st.warning("Selecciona dos presupuestos distintos para comparar.")
else:
    st.info("Necesitas al menos 2 presupuestos guardados para comparar.")

# ─── Eliminar ────────────────────────────────────────────────────────────────

st.markdown("---")
with st.expander("Eliminar presupuesto", expanded=False):
    st.warning("Esta acción es irreversible.")

    id_eliminar = st.selectbox(
        "Selecciona el presupuesto a eliminar",
        ids_disponibles,
        format_func=lambda x: next(
            (f"#{x} · {item['descripcion'] or 'Sin descripción'}  -  {item['creado_en']}"
             for item in lista if item["id"] == x),
            str(x),
        ),
        key="del_id",
    )

    # Vista previa del presupuesto seleccionado
    _prev = obtener_presupuesto(id_eliminar)
    if _prev:
        st.markdown("**Vista previa:**")
        p1, p2, p3, p4 = st.columns(4)
        p1.markdown(f"**PEM**\n\n{euro(_prev['pem'])}")
        p2.markdown(f"**PBL sin IVA**\n\n{euro(_prev['pbl_sin_iva'])}")
        p3.markdown(f"**IVA**\n\n{euro(_prev['iva'])}")
        p4.markdown(f"**TOTAL**\n\n{euro(_prev['total'])}")

        caps = _prev.get("capitulos", {})
        if caps:
            df_prev = pd.DataFrame([
                {"Capítulo": nombre, "Importe": euro(info["subtotal"])}
                for nombre, info in caps.items()
            ])
            st.dataframe(df_prev, use_container_width=True, hide_index=True)

    if st.button("Eliminar definitivamente", type="secondary"):
        logger.info("Eliminando presupuesto #%s", id_eliminar)
        if eliminar_presupuesto(id_eliminar):
            logger.info("Presupuesto #%s eliminado correctamente", id_eliminar)
            st.success(f"Presupuesto #{id_eliminar} eliminado.")
            st.rerun()
        else:
            logger.warning("Presupuesto #%s no encontrado al intentar eliminar", id_eliminar)
            st.error("No se encontró el presupuesto.")
