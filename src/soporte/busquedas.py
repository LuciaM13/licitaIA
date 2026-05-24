"""Búsquedas genéricas en listas de dicts (catálogos).

Helpers transversales sin lógica de dominio: simplemente recorren un
catálogo y devuelven el item que cumpla un criterio. Se separa de
``src.modelo`` porque no son conceptos del dominio sino utilidades de
acceso.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def find_item(items: list[dict], tipo: str, diametro: int) -> dict:
    """Busca una tubería por tipo y diámetro en un catálogo."""
    for item in items:
        if item["tipo"] == tipo and int(item["diametro_mm"]) == int(diametro):
            logger.debug("find_item: encontrado tipo=%s DN=%d → '%s'", tipo, diametro, item["label"])
            return item
    logger.error("find_item: NO ENCONTRADO tipo=%s DN=%d en catálogo de %d items "
                 "(labels disponibles: %s)",
                 tipo, diametro, len(items), [i.get("label") for i in items])
    raise ValueError(f"No se encontró tubería tipo={tipo}, diámetro={diametro}mm")


def find_by_label(items: list[dict], label: str) -> dict:
    """Busca un item por su label en un catálogo de materiales."""
    for item in items:
        if item["label"] == label:
            logger.debug("find_by_label: encontrado '%s'", label)
            return item
    logger.error("find_by_label: NO ENCONTRADO label='%s' en catálogo de %d items "
                 "(labels disponibles: %s)",
                 label, len(items), [i.get("label") for i in items])
    raise ValueError(f"No se encontró item con label='{label}'")
