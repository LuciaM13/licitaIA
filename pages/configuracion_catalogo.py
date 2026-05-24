"""Pagina de configuracion global y valores por defecto de la calculadora."""

from __future__ import annotations

import copy
import logging
from collections.abc import Mapping
from typing import Any

import streamlit as st

from src.catalogo.editor import ejecutar_guardado
from src.catalogo.repositorio import cargar_todo
from src.ui.precios_cache import cargar_precios
from src.ui.session import claves as sk

logger = logging.getLogger(__name__)


st.title("Configuración y catálogo")

st.caption(
    "Esta pagina contiene solo parametros globales y valores por defecto. "
    "Las variantes nuevas de catalogo se anaden desde la calculadora con el "
    "boton '+' junto al selector correspondiente."
)


try:
    precios = cargar_todo()
except (ValueError, Exception) as e:
    logger.error("Configuracion: no se pudieron cargar los precios: %s", e, exc_info=True)
    st.error(
        f"No se pudieron cargar los precios: {e}\n\n"
        "Comprueba que la base de datos `precios.db` existe en la carpeta data/."
    )
    st.stop()

_en_confirmacion = st.session_state.get(sk.CONFIRMAR_GUARDADO, False)

if sk.PRECIOS_ORIGINALES not in st.session_state or not _en_confirmacion:
    st.session_state[sk.PRECIOS_ORIGINALES] = copy.deepcopy(precios)

if _en_confirmacion:
    precios = st.session_state.get(sk.PRECIOS_PENDIENTES, precios)


def _reset_confirmacion() -> None:
    """Limpia el estado de confirmacion de guardado y fuerza rerun."""
    st.session_state[sk.CONFIRMAR_GUARDADO] = False
    st.session_state.pop(sk.PRECIOS_PENDIENTES, None)
    st.session_state.pop(sk.PRECIOS_ORIGINALES, None)
    st.rerun()


def _flatten_config(data: Mapping[str, Any]) -> dict[str, Any]:
    """Extrae solo la configuracion editable de esta pagina."""
    keys_globales = (
        "pct_gg",
        "pct_bi",
        "pct_iva",
        "factor_esponjamiento",
        "pct_manual_defecto",
        "pct_ci",
        "conduccion_provisional_precio_m",
    )
    plano = {k: data.get(k) for k in keys_globales}
    defaults = data.get("defaults_ui", {})
    if isinstance(defaults, Mapping):
        for k, v in defaults.items():
            plano[f"defaults_ui.{k}"] = v
    return plano


def _resumen_cambios(original: Mapping[str, Any], editado: Mapping[str, Any]) -> list[str]:
    """Devuelve cambios legibles sin depender de los antiguos editores de catalogo."""
    antes = _flatten_config(original)
    despues = _flatten_config(editado)
    cambios = []
    for key in sorted(despues):
        if antes.get(key) != despues.get(key):
            cambios.append(f"{key}: {antes.get(key)!r} -> {despues.get(key)!r}")
    return cambios


with st.expander("Financiero y generales - GG, BI, IVA, esponjamiento, % manual"):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        precios["pct_gg"] = round(st.number_input(
            "Gastos Generales (%)",
            value=precios["pct_gg"] * 100, step=0.5,
            disabled=_en_confirmacion) / 100, 6)
    with fc2:
        precios["pct_bi"] = round(st.number_input(
            "Beneficio Industrial (%)",
            value=precios["pct_bi"] * 100, step=0.5,
            disabled=_en_confirmacion) / 100, 6)
    with fc3:
        precios["pct_iva"] = round(st.number_input(
            "IVA (%)",
            value=precios["pct_iva"] * 100, step=0.5,
            disabled=_en_confirmacion) / 100, 6)

    pg1, pg2, pg3 = st.columns(3)
    with pg1:
        precios["factor_esponjamiento"] = round(st.number_input(
            "Factor esponjamiento (canon vertido)",
            value=float(precios.get("factor_esponjamiento", 1.30)),
            step=0.05, min_value=1.0, format="%.2f",
            disabled=_en_confirmacion), 4)
    with pg2:
        precios["pct_manual_defecto"] = round(st.number_input(
            "% Excavacion manual por defecto",
            value=float(precios.get("pct_manual_defecto", 0.30)) * 100,
            step=5.0, min_value=0.0, max_value=100.0,
            disabled=_en_confirmacion) / 100, 4)
    with pg3:
        precios["pct_ci"] = round(st.number_input(
            "Margen de seguridad global",
            value=float(precios.get("pct_ci", 1.0)),
            step=0.01, min_value=1.0, max_value=1.20, format="%.2f",
            disabled=_en_confirmacion), 4)

    precios["conduccion_provisional_precio_m"] = round(st.number_input(
        "Precio conduccion provisional PE (EUR/m, base sin CI)",
        value=float(precios.get("conduccion_provisional_precio_m", 12.0)),
        step=0.5, min_value=0.0, format="%.2f",
        help="Precio base (Excel / 1.05). El Excel oficial es 12.60 EUR/m, por lo que aqui deberias introducir 12.00.",
        disabled=_en_confirmacion), 2)


with st.expander("Valores por defecto - Mediciones e importes iniciales del formulario"):
    _dui = precios["defaults_ui"]

    st.markdown("**Geometria de tramo**")
    d1, d2 = st.columns(2)
    with d1:
        _dui["aba_longitud_m"] = st.number_input(
            "Longitud ABA por defecto (m)", value=float(_dui["aba_longitud_m"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["san_longitud_m"] = st.number_input(
            "Longitud SAN por defecto (m)", value=float(_dui["san_longitud_m"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
    with d2:
        _dui["aba_profundidad_m"] = st.number_input(
            "Profundidad ABA por defecto (m)", value=float(_dui["aba_profundidad_m"]),
            min_value=0.0, step=0.1, format="%.2f", disabled=_en_confirmacion)
        _dui["san_profundidad_m"] = st.number_input(
            "Profundidad SAN por defecto (m)", value=float(_dui["san_profundidad_m"]),
            min_value=0.0, step=0.1, format="%.2f", disabled=_en_confirmacion)
    st.divider()

    st.markdown("**Superficies y acometidas**")
    d3, d4 = st.columns(2)
    with d3:
        _dui["pav_aba_acerado_m2"] = st.number_input(
            "Acerado ABA por defecto (m2)", value=float(_dui["pav_aba_acerado_m2"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["pav_san_calzada_m2"] = st.number_input(
            "Calzada SAN por defecto (m2)", value=float(_dui["pav_san_calzada_m2"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["acometidas_n"] = int(st.number_input(
            "Numero acometidas por defecto", value=int(_dui["acometidas_n"]),
            min_value=0, step=1, disabled=_en_confirmacion))
    with d4:
        _dui["pav_aba_bordillo_m"] = st.number_input(
            "Bordillo ABA por defecto (m)", value=float(_dui["pav_aba_bordillo_m"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["pav_san_acera_m2"] = st.number_input(
            "Acera SAN por defecto (m2)", value=float(_dui["pav_san_acera_m2"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
    st.divider()

    st.markdown("**Porcentajes de obra**")
    d5, d6 = st.columns(2)
    with d5:
        _dui["pct_seguridad"] = round(st.number_input(
            "Seguridad y Salud por defecto (%)", value=float(_dui["pct_seguridad"]) * 100,
            min_value=0.0, max_value=20.0, step=0.5, format="%.1f",
            disabled=_en_confirmacion) / 100, 4)
    with d6:
        _dui["pct_gestion"] = round(st.number_input(
            "Gestion Ambiental por defecto (%)", value=float(_dui["pct_gestion"]) * 100,
            min_value=0.0, max_value=20.0, step=0.5, format="%.1f",
            disabled=_en_confirmacion) / 100, 4)


st.divider()

if sk.CONFIRMAR_GUARDADO not in st.session_state:
    st.session_state[sk.CONFIRMAR_GUARDADO] = False

if not st.session_state[sk.CONFIRMAR_GUARDADO]:
    if st.button("Guardar cambios", type="primary", use_container_width=True):
        st.session_state[sk.CONFIRMAR_GUARDADO] = True
        st.session_state[sk.PRECIOS_PENDIENTES] = copy.deepcopy(precios)
        st.rerun()
else:
    original = st.session_state.get(sk.PRECIOS_ORIGINALES, {})
    cambios = _resumen_cambios(original, precios)

    if cambios:
        st.warning("Revisa los cambios antes de guardarlos.")
        with st.expander(f"Cambios pendientes ({len(cambios)})", expanded=True):
            for cambio in cambios:
                st.write(f"- {cambio}")
    else:
        st.info("No hay cambios que guardar.")

    col_si, col_no = st.columns(2)
    with col_si:
        if st.button(
            "Si, guardar",
            type="primary",
            use_container_width=True,
            disabled=not cambios,
        ):
            try:
                logger.info("Configuracion: guardando configuracion global")
                ejecutar_guardado(precios)
                cargar_precios.clear()
                st.success("Configuracion guardada correctamente.")
                _reset_confirmacion()
            except ValueError as e:
                logger.error("Configuracion: error guardando configuracion: %s", e)
                st.error(str(e))
    with col_no:
        if st.button("Cancelar", use_container_width=True):
            _reset_confirmacion()
