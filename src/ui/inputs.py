"""Widgets Streamlit reutilizables para la página de cálculo."""

from __future__ import annotations

import streamlit as st

from src.soporte.busquedas import find_by_label, find_item
from src.ui.session import claves as sk


# Mapeo target_inline -> red SQL para auto-selección post-rerun.
# Usado para validar que INLINE_CREATE_RESULT corresponde al input que
# está renderizándose (BLOCK 6: lectura read-only; el `pop` lo hace
# `_consumir_inline_result` en `pages/calculadora.py`).
_RED_POR_TARGET = {"tuberias_aba": "ABA", "tuberias_san": "SAN"}


def input_tuberia(
    prefix: str,
    catalogo: list,
    default_longitud: float,
    default_profundidad: float,
    target_inline: str | None = None,
) -> tuple[dict, float, float]:
    """Renderiza inputs de tubería (longitud, tipo, diámetro, profundidad).

    Si `target_inline` es `"tuberias_aba"` o `"tuberias_san"`, añade un
    botón '+' en una columna extra que abre el dialog de creación inline.
    Tras un INSERT exitoso, los selectbox de tipo y diámetro auto-seleccionan
    la fila recién creada calculando `index=` con `lista.index(...)` envuelto
    en `try/except ValueError -> 0` (BLOCK 5: NUNCA pre-set de session_state
    para keys de widget ya creado en un rerun anterior).

    `INLINE_CREATE_RESULT` se lee aquí en read-only; el consumo (pop) ocurre
    al final del render de la calculadora vía `_consumir_inline_result` para
    que selectboxes espejo del mismo catálogo también auto-seleccionen el
    item nuevo (BLOCK 6).
    """
    # Lectura read-only de INLINE_CREATE_RESULT para auto-selección.
    _res = st.session_state.get(sk.INLINE_CREATE_RESULT)
    _label_nuevo = None
    if (
        target_inline
        and _res
        and _res[0] == "tuberias"
        and _res[1] == _RED_POR_TARGET.get(target_inline)
    ):
        _label_nuevo = _res[2]
    _match = (
        next((x for x in catalogo if x.get("label") == _label_nuevo), None)
        if _label_nuevo
        else None
    )

    if target_inline is not None:
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c5 = None

    with c1:
        longitud = st.number_input(
            f"{prefix} Longitud (m)", min_value=0.0, value=default_longitud,
            key=f"{prefix}_longitud")
    with c2:
        tipos = sorted({x["tipo"] for x in catalogo})
        # BLOCK 5: index= via .index() con try/except, NO pre-set de session_state.
        try:
            _idx_tipo = tipos.index(_match["tipo"]) if _match else 0
        except ValueError:
            _idx_tipo = 0
        tipo = st.selectbox(
            f"{prefix} Tipo de tubería", tipos,
            index=_idx_tipo, key=f"{prefix}_tipo")
    with c3:
        # BLOCK 5: la lista de DNs depende del tipo YA seleccionado.
        # Primero filtrar la lista, luego calcular el index.
        dns = sorted({x["diametro_mm"] for x in catalogo if x["tipo"] == tipo})
        try:
            _idx_dn = (
                dns.index(_match["diametro_mm"])
                if (_match and _match.get("tipo") == tipo)
                else 0
            )
        except ValueError:
            _idx_dn = 0
        diametro = st.selectbox(
            f"{prefix} Diámetro (mm)", dns,
            index=_idx_dn, key=f"{prefix}_diametro")
    with c4:
        profundidad = st.number_input(
            f"{prefix} Profundidad (m)", min_value=0.0, value=default_profundidad,
            key=f"{prefix}_profundidad")
    if c5 is not None and target_inline is not None:
        with c5:
            st.write("")  # padding vertical para alinear con el label
            if st.button(
                "+",
                key=f"{prefix}_btn_add",
                help="Añadir nueva tubería al catálogo",
            ):
                sk.arm_inline_dialog(st.session_state, target_inline)
                st.rerun()

    try:
        item = find_item(catalogo, tipo, diametro)
    except ValueError as e:
        st.error(f"Error en catálogo de tuberías: {e}")
        st.stop()
    st.info(f"Tubería {prefix}: {item['label']} · {item['precio_m']} €/m")
    return item, longitud, profundidad


def input_subbase(red: str, subbases: list) -> tuple[float, dict | None]:
    """Renderiza inputs de sub-base y retorna (espesor, item) o (0.0, None).

    Sub-bases queda fuera del set de catálogos con alta inline (decisión
    Phase 03-03 reducción a 10 ítems). El selectbox sigue leyendo del
    catálogo persistido pero ya no expone botón '+'.
    """
    item: dict | None = None

    sb1, sb2 = st.columns(2)

    with sb1:
        espesor = st.number_input(
            f"Espesor sub-base {red} (m)", min_value=0.0, value=0.0, step=0.05,
            format="%.2f", key=f"subbase_{red.lower()}_espesor")
    with sb2:
        if espesor > 0 and subbases:
            opciones = [x["label"] for x in subbases]
            label = st.selectbox(
                f"Material sub-base {red}",
                opciones, index=0, key=f"subbase_{red.lower()}_label")
            item = find_by_label(subbases, label)
        elif espesor > 0 and not subbases:
            st.caption(
                f"Catálogo de sub-bases {red} vacío. Configura el catálogo "
                f"desde la página de administración de precios."
            )
            item = None
        else:
            item = None

    return espesor, item
