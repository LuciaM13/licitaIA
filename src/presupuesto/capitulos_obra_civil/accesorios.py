"""Accesorios escalados por intervalo: valvulería, imbornales, desmontaje.

Cada función comparte la misma estructura: cuenta unidades por intervalo,
multiplica por precio (y factor de piezas, cuando aplica) y devuelve
``(subtotal, partidas)`` o ``None`` si la entrada no aplica.
"""

from __future__ import annotations

import logging

from src.modelo.tipos import ItemCatalogo, Precios
from src.presupuesto.capitulos_obra_civil._helpers import _importe

logger = logging.getLogger(__name__)


def capitulo_valvuleria(
    longitud: float,
    diametro_mm: int,
    precios: Precios,
    *,
    instalacion: str = "enterrada",
    valvuleria_items: list[ItemCatalogo] | None = None,
) -> tuple[float, dict] | None:
    logger.debug("[VALV] Entrada: L=%.2f DN=%d inst=%s items=%d",
                 longitud, diametro_mm, instalacion,
                 len(valvuleria_items) if valvuleria_items else 0)
    if not precios.get("catalogo_valvuleria") or longitud <= 0:
        logger.debug("[VALV] Guard: catálogo vacío o L<=0 → None")
        return None

    items = valvuleria_items or []
    partidas: dict[str, float] = {}
    for item in items:
        intervalo = float(item.get("intervalo_m", 0))
        if intervalo <= 0:
            continue
        n = longitud / intervalo
        factor = float(item.get("factor_piezas", 1.0))
        imp = _importe(n, item["precio"] * factor)
        partidas[item["label"]] = imp
        logger.debug("[VALV]   '%s': n=%.2f × precio=%.4f × fp=%.2f = %.2f €",
                     item["label"], n, item["precio"], factor, imp)

    if not partidas:
        if precios["catalogo_valvuleria"]:
            raise ValueError(
                f"Hay {len(precios['catalogo_valvuleria'])} items de valvulería pero ninguno "
                f"aplica para DN={diametro_mm} mm, instalación='{instalacion}'. "
                "Revisa los rangos DN e instalación en Administración de precios."
            )
        return None

    return sum(partidas.values()), partidas


def capitulo_desmontaje(
    longitud: float, precios: Precios, *, desmontaje_item: ItemCatalogo | None = None
) -> tuple[float, dict] | None:
    if longitud <= 0 or desmontaje_item is None:
        logger.debug("[DESM] Guard: L=%.2f item=%s → None",
                     longitud, desmontaje_item["label"] if desmontaje_item else None)
        return None
    importe = _importe(longitud, desmontaje_item["precio_m"])
    logger.debug("[DESM] %s: L=%.2f × precio=%.4f = %.2f €",
                 desmontaje_item["label"], longitud, desmontaje_item["precio_m"], importe)
    return importe, {desmontaje_item["label"]: importe}


def capitulo_imbornales(
    longitud: float, tipo: str, label_nuevo: str, precios: Precios
) -> tuple[float, dict] | None:
    """Fórmula: n_imbornales = 2/32 × L."""
    logger.debug("[IMBORN] Entrada: L=%.2f tipo=%s label_nuevo=%s", longitud, tipo, label_nuevo)
    if tipo == "none" or longitud <= 0:
        logger.debug("[IMBORN] Guard: tipo=none o L<=0 → None")
        return None
    catalogo = precios.get("catalogo_imbornales", [])
    if not catalogo:
        logger.warning("[IMBORN] Catálogo imbornales vacío → None")
        return None
    n = 2.0 / 32.0 * longitud
    if tipo == "adaptacion":
        item = next((x for x in catalogo if x["tipo"] == "adaptacion"), None)
    else:
        item = next((x for x in catalogo if x["label"] == label_nuevo), None)
        if item is None:
            item = next((x for x in catalogo if x["tipo"] == "nuevo"), None)
    if item is None:
        logger.warning("[IMBORN] No se encontró item para tipo=%s label=%s → None", tipo, label_nuevo)
        return None
    importe = _importe(n, item["precio"])
    logger.debug("[IMBORN] %s: n=%.4f × precio=%.4f = %.2f €", item["label"], n, item["precio"], importe)
    return importe, {item["label"]: importe}
