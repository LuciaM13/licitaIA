"""
Ranking y desempate entre candidatos elegibles.

Funciones puras: reciben índices de candidatos + catálogo y devuelven
el item ganador (o lista ordenada). Sin dependencias de CLIPS ni I/O.

Criterios:
  Entibación  → mayor umbral_m; si empate, menor índice (orden de catálogo)
  Pozo        → más específico: red definida > menor profundidad_max > menor dn_max
  Valvulería  → todos los candidatos en orden de catálogo original
  Desmontaje  → menor dn_max que cumpla; si empate, menor índice
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def desempatar_entibacion(
    candidatos_idx: list[int], catalogo: list[dict]
) -> dict | None:
    if not candidatos_idx:
        return None

    items = [(i, catalogo[i]) for i in candidatos_idx]
    items.sort(key=lambda x: (-float(x[1].get("umbral_m", 0)), x[0]))
    idx, item = items[0]
    logger.debug("Entibación: %d candidatos → seleccionado idx=%d (umbral=%.2f)",
                 len(candidatos_idx), idx, float(item.get("umbral_m", 0)))
    return item


def desempatar_pozo(
    candidatos_idx: list[int], catalogo: list[dict]
) -> dict | None:
    if not candidatos_idx:
        return None

    def _especificidad(t):
        i, item = t
        sin_red = item.get("red") is None
        p_max = float(item["profundidad_max"]) if item.get("profundidad_max") is not None else 9999.0
        d_max = int(item["dn_max"]) if item.get("dn_max") is not None else 99999
        return (sin_red, p_max, d_max, i)

    items = [(i, catalogo[i]) for i in candidatos_idx]
    idx, item = min(items, key=_especificidad)
    logger.debug("Pozo: %d candidatos → seleccionado idx=%d (%s)",
                 len(candidatos_idx), idx, item.get("label", "?"))
    return item


def ordenar_valvuleria(
    candidatos_idx: list[int], catalogo: list[dict]
) -> list[dict]:
    """Devuelve todos los candidatos en el orden original del catálogo."""
    return [catalogo[i] for i in sorted(candidatos_idx)]


def desempatar_desmontaje(
    candidatos_idx: list[int], catalogo: list[dict]
) -> dict | None:
    if not candidatos_idx:
        return None

    items = [(i, catalogo[i]) for i in candidatos_idx]
    items.sort(key=lambda x: (int(x[1]["dn_max"]), x[0]))
    idx, item = items[0]
    logger.debug("Desmontaje: %d candidatos → seleccionado idx=%d (dn_max=%d)",
                 len(candidatos_idx), idx, int(item["dn_max"]))
    return item
