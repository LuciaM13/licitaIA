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
        logger.debug("[DESEMP-ENTIB] 0 candidatos → None")
        return None

    items = [(i, catalogo[i]) for i in candidatos_idx]
    for i, it in items:
        logger.debug("[DESEMP-ENTIB]   candidato idx=%d: red=%s umbral=%.2f label=%s",
                     i, it.get("red"), float(it.get("umbral_m", 0)), it.get("label", "?"))
    items.sort(key=lambda x: (-float(x[1].get("umbral_m", 0)), x[0]))
    idx, item = items[0]
    logger.debug("[DESEMP-ENTIB] Criterio: mayor umbral_m → seleccionado idx=%d '%s' (umbral=%.2f)",
                 idx, item.get("label", "?"), float(item.get("umbral_m", 0)))
    return item


def desempatar_pozo(
    candidatos_idx: list[int], catalogo: list[dict]
) -> dict | None:
    if not candidatos_idx:
        logger.debug("[DESEMP-POZO] 0 candidatos → None")
        return None

    def _especificidad(t):
        i, item = t
        sin_red = item.get("red") is None
        p_max = float(item["profundidad_max"]) if item.get("profundidad_max") is not None else 9999.0
        d_max = int(item["dn_max"]) if item.get("dn_max") is not None else 99999
        return (sin_red, p_max, d_max, i)

    items = [(i, catalogo[i]) for i in candidatos_idx]
    for i, it in items:
        score = _especificidad((i, it))
        logger.debug("[DESEMP-POZO]   candidato idx=%d: red=%s p_max=%s dn_max=%s → score=%s label=%s",
                     i, it.get("red"), it.get("profundidad_max", "∞"),
                     it.get("dn_max", "∞"), score, it.get("label", "?"))
    idx, item = min(items, key=_especificidad)
    logger.debug("[DESEMP-POZO] Criterio: (red_definida > menor p_max > menor dn_max) → idx=%d '%s'",
                 idx, item.get("label", "?"))
    return item


def ordenar_valvuleria(
    candidatos_idx: list[int], catalogo: list[dict]
) -> list[dict]:
    """Devuelve todos los candidatos en el orden original del catálogo."""
    resultado = [catalogo[i] for i in sorted(candidatos_idx)]
    logger.debug("[DESEMP-VALV] %d candidatos → %d items: %s",
                 len(candidatos_idx), len(resultado),
                 [it.get("label", "?") for it in resultado])
    return resultado


def desempatar_desmontaje(
    candidatos_idx: list[int], catalogo: list[dict]
) -> dict | None:
    if not candidatos_idx:
        logger.debug("[DESEMP-DESM] 0 candidatos → None")
        return None

    items = [(i, catalogo[i]) for i in candidatos_idx]
    for i, it in items:
        logger.debug("[DESEMP-DESM]   candidato idx=%d: es_fibro=%d dn_max=%d label=%s",
                     i, it.get("es_fibrocemento", 0), int(it["dn_max"]), it.get("label", "?"))
    items.sort(key=lambda x: (int(x[1]["dn_max"]), x[0]))
    idx, item = items[0]
    logger.debug("[DESEMP-DESM] Criterio: menor dn_max → seleccionado idx=%d '%s' (dn_max=%d)",
                 idx, item.get("label", "?"), int(item["dn_max"]))
    return item
