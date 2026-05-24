"""Sub-formularios de pavimentación: acerados, bordillos, calzadas, demolición.

Cada función devuelve un dict con SOLO las columnas que pide; el use case
(``insertar_variante_catalogo``) enriquece con ``red`` y aplica
``_eur_a_cents`` exactamente UNA vez al persistir.
"""

from __future__ import annotations

import logging
import re

import streamlit as st

from src.presupuesto.materiales import materiales_demo_disponibles


logger = logging.getLogger(__name__)
from src.ui.dialogs.inline_catalogo.mappings import (
    _DEMOLICION_CTX,
    _MATERIALES_DEMOLICION_OPCIONES,
)
from src.ui.materiales import format_material
from src.ui.precios_cache import cargar_precios


_OPCION_OTRO = "__otro__"


def _normalizar_slug(texto: str) -> str:
    """Normaliza la entrada del usuario a un slug `snake_case`.

    Pasos: lowercase → espacios/guiones a `_` → filtra a `[a-z0-9_]` →
    colapsa `__` → strip `_`. Devuelve cadena vacía si no quedan
    caracteres válidos.
    """
    s = (texto or "").lower().replace(" ", "_").replace("-", "_")
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _form_acerados() -> dict:
    """Schema: red, label, unidad CHECK IN ('m','m2','m3','ud'), precio."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)",
            key="_inline_acerados_label",
            placeholder="Baldosa cigarrillo",
        )
    with col2:
        unidad = st.selectbox(
            "Unidad", ["m", "m2", "m3", "ud"], index=1,
            key="_inline_acerados_unidad",
        )
    precio = st.number_input(
        "Precio (BASE EMASESA, en € por unidad seleccionada)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_acerados_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "unidad": unidad,
        "precio": float(precio),
    }


def _form_bordillos() -> dict:
    """Schema: label UNIQUE, unidad CHECK IN ('m','m2','ud'), precio."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)",
            key="_inline_bordillos_label",
            placeholder="Bordillo bicapa 10x20",
        )
    with col2:
        unidad = st.selectbox(
            "Unidad", ["m", "m2", "ud"], index=0,
            key="_inline_bordillos_unidad",
        )
    precio = st.number_input(
        "Precio (BASE EMASESA, en € por unidad)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_bordillos_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "unidad": unidad,
        "precio": float(precio),
    }


def _form_calzadas() -> dict:
    """Schema: label UNIQUE, unidad CHECK IN ('m2','m3'), precio.

    Si `unidad == 'm3'` se pide también `espesor_m` (FK a `espesores_calzada`):
    sin él la calculadora hace `st.stop()` al detectar la calzada en m³ sin
    espesor definido. El dialog principal detecta la presencia de `espesor_m`
    en el dict y delega a `insertar_calzada_con_espesor` para persistir
    ambas filas en una transacción atómica.
    """
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)",
            key="_inline_calzadas_label",
            placeholder="Adoquín",
        )
    with col2:
        unidad = st.selectbox(
            "Unidad", ["m2", "m3"], index=0,
            key="_inline_calzadas_unidad",
        )
    precio = st.number_input(
        "Precio (BASE EMASESA, en € por unidad)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_calzadas_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    item: dict = {
        "label": label.strip(),
        "unidad": unidad,
        "precio": float(precio),
    }
    if unidad == "m3":
        espesor_m = st.number_input(
            "Espesor de la calzada (m)",
            min_value=0.01, value=0.30, step=0.01, format="%.2f",
            key="_inline_calzadas_espesor",
            help=(
                "Necesario para convertir m² a m³ en la calculadora. "
                "Se persiste atómicamente junto con la calzada."
            ),
        )
        item["espesor_m"] = float(espesor_m)
    return item


def _form_demolicion(target: str) -> dict:
    """Schema: red, label, unidad CHECK IN ('m','m2','m3','ud'), material, precio.

    UNIQUE(red, unidad, material). El target codifica (red, tipo_elemento)
    y pre-rellena `unidad` desde `_DEMOLICION_CTX`. El usuario elige el
    material entre los 8 canónicos EMASESA (`_MATERIALES_DEMOLICION_OPCIONES`)
    o introduce uno nuevo vía la opción "Otro (slug personalizado)". El use
    case `insertar_variante_catalogo` normaliza y valida el slug final.
    """
    ctx = _DEMOLICION_CTX[target]
    tipo_humano = ctx["tipo"]  # acerado / bordillo / calzada
    unidad_default = ctx["unidad"]

    # Cargar materiales que YA existen en BD para este (red, tipo, unidad)
    # y marcarlos en el selectbox para evitar colisiones UNIQUE silenciosas.
    red = target.split("_")[1]  # "demolicion_aba_acerado" -> "aba"
    clave_cat = f"demolicion_{red}"
    try:
        precios = cargar_precios()
        materiales_existentes = set(
            materiales_demo_disponibles(
                precios.get(clave_cat, []), tipo_humano, unidad_default
            )
        )
    except Exception as exc:
        logger.warning("materiales_existentes fallback: %s", exc)
        materiales_existentes = set()

    st.caption(
        f"Variante de demolición para {tipo_humano} (unidad por defecto "
        f"{unidad_default}). El precio se persiste en €/{unidad_default} BASE EMASESA."
    )

    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)",
            key=f"_inline_demolicion_label_{target}",
            placeholder=f"Demol. {tipo_humano} - granítico variante",
        )
    with col2:
        opciones = list(_MATERIALES_DEMOLICION_OPCIONES) + [_OPCION_OTRO]

        def _format_opcion(slug: str) -> str:
            if slug == _OPCION_OTRO:
                return "Otro (slug personalizado)"
            etiqueta = format_material(slug)
            if slug in materiales_existentes:
                return f"(●) {etiqueta}"
            return etiqueta

        seleccion = st.selectbox(
            "Material",
            opciones,
            index=0,
            format_func=_format_opcion,
            key=f"_inline_demolicion_material_sel_{target}",
            help="(●) ya existe en catálogo para este contexto. "
                 "Selecciona 'Otro' para introducir un material no canónico.",
        )

    if seleccion == _OPCION_OTRO:
        custom = st.text_input(
            "Material personalizado",
            key=f"_inline_demolicion_material_custom_{target}",
            placeholder="ej. Pizarra, Terrazo rojo, Adoquín granítico",
            help="Se normaliza a slug snake_case antes de guardar "
                 "(p.ej. 'Pizarra Roja' → pizarra_roja).",
        )
        material = _normalizar_slug(custom)
        if custom and not material:
            st.error(
                "El material introducido no contiene letras o números. "
                "Usa caracteres alfanuméricos (ej. 'Pizarra Roja')."
            )
        elif material and material in _MATERIALES_DEMOLICION_OPCIONES:
            st.warning(
                f"`{material}` ya está en el desplegable de materiales "
                "canónicos; selecciónalo arriba en lugar de duplicarlo aquí."
            )
        elif material:
            st.info(f"Slug que se va a guardar: `{material}`")
    else:
        material = seleccion

    col3, col4 = st.columns(2)
    with col3:
        try:
            idx_unidad = ["m", "m2", "m3", "ud"].index(unidad_default)
        except ValueError:
            idx_unidad = 1
        unidad = st.selectbox(
            "Unidad", ["m", "m2", "m3", "ud"], index=idx_unidad,
            key=f"_inline_demolicion_unidad_{target}",
        )
    with col4:
        precio = st.number_input(
            "Precio (BASE EMASESA, en € por unidad)",
            min_value=0.0, value=0.0, step=0.01, format="%.2f",
            key=f"_inline_demolicion_precio_{target}",
        )
    return {
        "label": label.strip(),
        "unidad": unidad,
        "material": material,
        "precio": float(precio),
    }
