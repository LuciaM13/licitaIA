"""Ranking y desempate de candidatos elegibles.

Funciones puras que reciben indices de candidatos + catalogo
y devuelven el item seleccionado (o lista ordenada).
Sin dependencia de CLIPS ni IO.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def desempatar_entibacion(candidatos_idx: list[int], catalogo: list[dict]) -> dict | None:
    """Desempate entibacion: mayor umbral_m; si empate, primer item segun orden de catalogo.

    Reproduce exactamente el comportamiento original de calcular.py:
    sorted(..., key=umbral_m, reverse=True) + first match = mayor umbral que cumple.
    """
    if not candidatos_idx:
        return None

    items_candidatos = [(idx, catalogo[idx]) for idx in candidatos_idx]

    # Ordenar por umbral_m descendente; si empate, menor idx (orden de catalogo)
    items_candidatos.sort(key=lambda x: (-float(x[1].get("umbral_m", 0)), x[0]))

    mejor_idx, mejor_item = items_candidatos[0]
    logger.debug(
        "Entibacion: %d candidatos elegibles. Seleccionado idx=%d (umbral=%.2f)",
        len(candidatos_idx), mejor_idx, float(mejor_item.get("umbral_m", 0))
    )
    return mejor_item


def desempatar_pozo(candidatos_idx: list[int], catalogo: list[dict]) -> dict | None:
    """Desempate pozo: mas especifico = priorizar red definida, menor profundidad_max,
    menor dn_max, primer item segun orden de catalogo.

    Reproduce la funcion _especificidad del codigo original:
      (sin_red, p_max, d_max) con min() -> prioriza red definida, luego menor p_max, menor d_max.
    """
    if not candidatos_idx:
        return None

    items_candidatos = [(idx, catalogo[idx]) for idx in candidatos_idx]

    def _especificidad(item_tuple):
        idx, item = item_tuple
        sin_red = item.get("red") is None
        p_max = float(item["profundidad_max"]) if item.get("profundidad_max") is not None else 9999
        d_max = int(item["dn_max"]) if item.get("dn_max") is not None else 99999
        return (sin_red, p_max, d_max, idx)  # idx as final tiebreaker (catalog order)

    mejor_idx, mejor_item = min(items_candidatos, key=_especificidad)
    logger.debug(
        "Pozo: %d candidatos elegibles. Seleccionado idx=%d (%s)",
        len(candidatos_idx), mejor_idx, mejor_item.get("label", "?")
    )
    return mejor_item


def ordenar_valvuleria(candidatos_idx: list[int], catalogo: list[dict]) -> list[dict]:
    """Valvuleria: devuelve todos los candidatos en el mismo orden del catalogo original.

    El orden de catalogo es la fuente de verdad (propiedad de la lista Python original).
    """
    # Ordenar por indice original para mantener orden de catalogo
    candidatos_idx_sorted = sorted(candidatos_idx)
    items = [catalogo[idx] for idx in candidatos_idx_sorted]
    logger.debug(
        "Valvuleria: %d candidatos elegibles (indices: %s)",
        len(items), candidatos_idx_sorted
    )
    return items


def desempatar_desmontaje(candidatos_idx: list[int], catalogo: list[dict]) -> dict | None:
    """Desempate desmontaje: menor dn_max que cumpla; si empate, primer item segun orden de catalogo.

    Reproduce el min(candidatos, key=lambda x: int(x['dn_max'])) del codigo original.
    """
    if not candidatos_idx:
        return None

    items_candidatos = [(idx, catalogo[idx]) for idx in candidatos_idx]

    # Ordenar por dn_max ascendente; si empate, menor idx (orden de catalogo)
    items_candidatos.sort(key=lambda x: (int(x[1]["dn_max"]), x[0]))

    mejor_idx, mejor_item = items_candidatos[0]
    logger.debug(
        "Desmontaje: %d candidatos elegibles. Seleccionado idx=%d (dn_max=%d)",
        len(candidatos_idx), mejor_idx, int(mejor_item["dn_max"])
    )
    return mejor_item
