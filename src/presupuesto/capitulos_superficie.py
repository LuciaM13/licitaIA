"""
Capítulos de superficie - demolición, pavimentación, sub-base y acometidas.

Cada función recibe cantidades y precios ya resueltos y devuelve
(subtotal: float, partidas: dict[str, float]) | None.

  - NO importa de src.domain
  - NO importa de src.reglas
  - NO importa streamlit
"""

from __future__ import annotations

import logging
from typing import Any

from src.presupuesto.capitulos_obra_civil import _importe

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Demolición de pavimento
# ---------------------------------------------------------------------------

def capitulo_demolicion(
    qty1: float, item1: dict[str, Any] | None,
    qty2: float, item2: dict[str, Any] | None,
    *,
    factor_item1: float = 1.0,
) -> tuple[float, dict] | None:
    """Calcula el capítulo de demolición de pavimento.

    Args:
        qty1 / item1: primer item (m² - acerado en ABA, calzada en SAN).
        qty2 / item2: segundo item (m - bordillo en ABA, acera en SAN).
        factor_item1: multiplicador sobre item1. En ABA se pasa 1.2 porque
            el Excel aplica ×1.2 sobre la demolición de acerado (J7 fórmula:
            BASE_PRECIOS!D9 × 1.2). En SAN no se aplica (valor 1.0).
    """
    logger.debug("[DEMO] Entrada: qty1=%.2f item1=%s qty2=%.2f item2=%s factor1=%.2f",
                 qty1, item1["label"] if item1 else None,
                 qty2, item2["label"] if item2 else None, factor_item1)
    if qty1 <= 0 and qty2 <= 0:
        logger.debug("[DEMO] Guard: ambas cantidades <= 0 → None")
        return None
    partidas: dict[str, float] = {}
    for idx, (qty, item) in enumerate([(qty1, item1), (qty2, item2)]):
        if qty > 0 and item and "label" in item:
            factor = factor_item1 if idx == 0 else 1.0
            imp = _importe(qty, item["precio"]) * factor
            partidas[item["label"]] = imp
            logger.debug("[DEMO]   '%s': qty=%.2f × precio=%.4f × factor=%.2f = %.2f €",
                         item["label"], qty, item["precio"], factor, imp)
    if not partidas:
        logger.debug("[DEMO] Sin partidas generadas → None")
        return None
    total = sum(partidas.values())
    logger.debug("[DEMO] Total demolición: %.2f €", total)
    return total, partidas


# ---------------------------------------------------------------------------
# Pavimentación (acerado, bordillo, calzada)
# ---------------------------------------------------------------------------

def capitulo_pavimentacion(
    qty1: float, item1: dict[str, Any],
    qty2: float, item2: dict[str, Any],
    *,
    calzada_conversion: bool = False,
    espesores: dict | None = None,
    factor_item1: float = 1.0,
) -> tuple[float, dict] | None:
    """Calcula el capítulo de pavimentación (reposición de pavimento).

    Args:
        qty1 / item1: primer material (acerado en ABA, calzada en SAN).
        qty2 / item2: segundo material (bordillo en ABA, acera en SAN).
        factor_item1: multiplicador sobre item1.
    """
    logger.debug("[PAV] Entrada: qty1=%.2f item1=%s qty2=%.2f item2=%s factor1=%.2f calzada_conv=%s",
                 qty1, item1.get("label") if item1 else None,
                 qty2, item2.get("label") if item2 else None,
                 factor_item1, calzada_conversion)
    if qty1 <= 0 and qty2 <= 0:
        logger.debug("[PAV] Guard: ambas cantidades <= 0 → None")
        return None
    partidas: dict[str, float] = {}

    for idx, (qty, item) in enumerate([(qty1, item1), (qty2, item2)]):
        if qty <= 0:
            continue
        if not item or "label" not in item:
            raise ValueError("Cantidad de pavimentación > 0 pero no se seleccionó material.")
        factor = factor_item1 if idx == 0 else 1.0
        if calzada_conversion and espesores and item.get("unidad", "m2") != "m2":
            espesor = espesores.get(item["label"])
            if espesor is None:
                raise ValueError(
                    f"No existe espesor definido para '{item['label']}'. "
                    "Añádelo en Administración de precios → Espesores de calzada."
                )
            importe = _importe(qty * espesor, item["precio"]) * factor
            logger.debug("[PAV]   '%s': qty=%.2f × espesor=%.4f × precio=%.4f × factor=%.2f = %.2f € (m²→m³)",
                         item["label"], qty, espesor, item["precio"], factor, importe)
        else:
            importe = _importe(qty, item["precio"]) * factor
            logger.debug("[PAV]   '%s': qty=%.2f × precio=%.4f × factor=%.2f = %.2f €",
                         item["label"], qty, item["precio"], factor, importe)
        partidas[item["label"]] = importe

    total = sum(partidas.values())
    logger.debug("[PAV] Total pavimentación: %.2f €", total)
    return total, partidas


# ---------------------------------------------------------------------------
# Acometidas
# ---------------------------------------------------------------------------

def capitulo_acometidas(
    n: int, precio: float, label: str, factor: float = 1.0
) -> tuple[float, dict] | None:
    if n <= 0:
        logger.debug("[ACOM] n=%d → None", n)
        return None
    importe = _importe(n, precio * factor)
    logger.debug("[ACOM] %s: n=%d × precio=%.2f × factor=%.2f = %.2f €",
                 label, n, precio, factor, importe)
    return importe, {label: importe}


# ---------------------------------------------------------------------------
# Sub-base
# ---------------------------------------------------------------------------

def capitulo_subbase(
    superficie_m2: float, espesor_m: float, item: dict[str, Any] | None
) -> tuple[float, dict] | None:
    if superficie_m2 <= 0 or espesor_m <= 0 or item is None:
        logger.debug("[SUBBASE] Guard: sup=%.2f esp=%.3f item=%s → None",
                     superficie_m2, espesor_m, item["label"] if item else None)
        return None
    vol = superficie_m2 * espesor_m
    importe = _importe(vol, item["precio_m3"])
    logger.debug("[SUBBASE] %s: sup=%.2f × esp=%.3f = vol=%.3f m³ × precio=%.4f = %.2f €",
                 item["label"], superficie_m2, espesor_m, vol, item["precio_m3"], importe)
    return importe, {item["label"]: importe}
