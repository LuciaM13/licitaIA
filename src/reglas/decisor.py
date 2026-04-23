"""
Decisor determinista de materiales (Python puro, sin CLIPS).

Orquesta los filtros de elegibilidad + desempate + generación de explicaciones
para producir la lista de materiales ganadores de una red (ABA o SAN).

No invoca CLIPS en ningún punto. CLIPS en este proyecto se usa exclusivamente
para emitir alertas técnicas al licitador (ver ``src.reglas.alertas_clips``),
nunca para seleccionar materiales. Esta separación está alineada con la
memoria del TFG.

API pública
-----------
``resolver_decisiones(...)`` recibe los parámetros de una red y devuelve un
dict con los items ganadores, los candidatos considerados y una lista de
explicaciones en castellano (``trazabilidad``).
"""

from __future__ import annotations

import logging

from src.domain.tipos import ItemCatalogo, Precios
from src.reglas.normalizacion import (
    factor_piezas,
    normalizar_tipo,
    normalizar_red,
    normalizar_instalacion,
)
from src.domain.reglas.elegibilidad import (
    elegibles_entibacion,
    elegibles_pozos,
    elegibles_valvuleria,
    elegibles_desmontaje,
)
from src.domain.reglas.desempates import (
    desempatar_entibacion,
    desempatar_pozo,
    ordenar_valvuleria,
    desempatar_desmontaje,
)
from src.reglas.explicaciones import generar_explicaciones

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------

def _buscar_ganador_idx(item: ItemCatalogo | None, catalogo: list[ItemCatalogo]) -> int | None:
    """Devuelve el índice del item ganador en el catálogo, o None."""
    if item is None:
        return None
    label = item.get("label")
    return next(
        (i for i, it in enumerate(catalogo) if it.get("label") == label),
        None,
    )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def resolver_decisiones(
    tipo_tuberia: str,
    diametro_mm: int,
    red: str,
    profundidad: float,
    precios: Precios,
    instalacion: str,
    desmontaje_tipo: str,
) -> dict:
    """
    Resuelve las decisiones de elegibilidad y desempate de materiales.

    Returns:
        {
            "factor_piezas":  float,
            "entibacion":     {"necesaria": bool, "item": dict | None},
            "pozo_registro":  {"item": dict | None},
            "valvuleria":     {"items": list[dict]},
            "desmontaje":     {"item": dict | None},
            "trazabilidad":   list[str],   # Explicaciones en lenguaje natural
            "candidatos":     dict,        # Datos para la UI semi-automática
        }

    La clave ``trazabilidad`` del dict devuelto mantiene su nombre por
    compatibilidad con el historial persistido (tabla
    ``presupuesto_trazabilidad``); internamente el contenido se genera vía
    ``src.reglas.explicaciones.generar_explicaciones``.
    """
    tipo_norm = normalizar_tipo(tipo_tuberia)
    red_norm = normalizar_red(red)
    inst_norm = normalizar_instalacion(instalacion)
    desm_norm = desmontaje_tipo.strip().lower()

    logger.info("resolver_decisiones: tipo=%s DN=%d red=%s prof=%.2f inst=%s desm=%s",
                tipo_norm, diametro_mm, red_norm, profundidad, inst_norm, desm_norm)

    # 1. Factor piezas (determinista por tipo, case-insensitive).
    factor_piezas_val = factor_piezas(tipo_norm)
    logger.debug("  factor_piezas(%s) = %.2f", tipo_norm, factor_piezas_val)

    # 2-5. Catálogos + elegibilidad en Python puro.
    cat_entibacion = precios.get("catalogo_entibacion", [])
    cat_pozos = precios.get("catalogo_pozos", [])
    cat_valvuleria = precios.get("catalogo_valvuleria", [])
    cat_desmontaje = precios.get("catalogo_desmontaje", [])
    if not cat_entibacion:
        logger.warning("[ELEG] Catálogo de entibación vacío")
    if not cat_pozos:
        logger.warning("[ELEG] Catálogo de pozos vacío")
    if not cat_valvuleria:
        logger.warning("[ELEG] Catálogo de valvulería vacío")
    if not cat_desmontaje:
        logger.warning("[ELEG] Catálogo de desmontaje vacío")

    idx_entibacion = elegibles_entibacion(red_norm, profundidad, cat_entibacion)
    idx_pozos = elegibles_pozos(red_norm, profundidad, diametro_mm, cat_pozos)
    idx_valvuleria = elegibles_valvuleria(diametro_mm, inst_norm, cat_valvuleria)
    idx_desmontaje = (
        elegibles_desmontaje(desm_norm, diametro_mm, cat_desmontaje)
        if desm_norm != "none" else []
    )

    # Desempate.
    entib_item = desempatar_entibacion(idx_entibacion, cat_entibacion)
    pozo_item = desempatar_pozo(idx_pozos, cat_pozos)
    valv_items = ordenar_valvuleria(idx_valvuleria, cat_valvuleria)
    desm_item = (
        desempatar_desmontaje(idx_desmontaje, cat_desmontaje)
        if desm_norm != "none" else None
    )
    logger.debug("  Desempate → entib=%s pozo=%s valv=%d desm=%s",
                 entib_item["label"] if entib_item else None,
                 pozo_item["label"] if pozo_item else None,
                 len(valv_items),
                 desm_item["label"] if desm_item else None)

    # Explicaciones en lenguaje natural de cada decisión.
    trazabilidad = generar_explicaciones(
        red=red_norm,
        diametro_mm=diametro_mm,
        profundidad=profundidad,
        instalacion=inst_norm,
        desmontaje_tipo=desm_norm,
        cat_entibacion=cat_entibacion,
        idx_entibacion=idx_entibacion,
        item_entibacion=entib_item,
        idx_pozos=idx_pozos,
        item_pozo=pozo_item,
        items_valvuleria=valv_items,
        idx_desmontaje=idx_desmontaje,
        item_desmontaje=desm_item,
    )

    # Datos de candidatos para UI semi-automática.
    _valv_labels_ganadores = {it.get("label") for it in valv_items}
    valv_ganadores_idx = [
        i for i in idx_valvuleria
        if cat_valvuleria[i].get("label") in _valv_labels_ganadores
    ]

    candidatos = {
        "entibacion": {
            "catalogo": cat_entibacion,
            "elegibles_idx": idx_entibacion,
            "ganador_idx": _buscar_ganador_idx(entib_item, cat_entibacion),
        },
        "pozo_registro": {
            "catalogo": cat_pozos,
            "elegibles_idx": idx_pozos,
            "ganador_idx": _buscar_ganador_idx(pozo_item, cat_pozos),
        },
        "valvuleria": {
            "catalogo": cat_valvuleria,
            "elegibles_idx": idx_valvuleria,
            "ganadores_idx": valv_ganadores_idx,
        },
        "desmontaje": {
            "catalogo": cat_desmontaje,
            "elegibles_idx": idx_desmontaje,
            "ganador_idx": _buscar_ganador_idx(desm_item, cat_desmontaje),
        },
    }

    return {
        "factor_piezas": factor_piezas_val,
        "entibacion": {
            "necesaria": entib_item is not None,
            "item": entib_item,
        },
        "pozo_registro": {
            "item": pozo_item,
        },
        "valvuleria": {
            "items": valv_items,
        },
        "desmontaje": {
            "item": desm_item,
        },
        "trazabilidad": trazabilidad,
        "candidatos": candidatos,
    }
