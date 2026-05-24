"""Pozos (registro y existentes) y cánones de vertido.

  - ``capitulo_pozos_registro`` — pozos NUEVOS de registro (ABA o SAN).
  - ``capitulo_pozos_existentes`` — demolición o anulación de pozos
    EXISTENTES por tramo.
  - ``capitulo_canones`` — recoge los cánones que ``capitulo_obra_civil``
    dejó en ``auxiliares`` y los devuelve como capítulo separado (OTROS).
"""

from __future__ import annotations

import logging

from src.modelo.tipos import ItemCatalogo, Precios
from src.presupuesto.capitulos_obra_civil._helpers import _importe

logger = logging.getLogger(__name__)


def capitulo_pozos_registro(
    longitud: float,
    profundidad: float,
    diametro_mm: int,
    precios: Precios,
    *,
    es_san: bool = False,
    pozo_item: ItemCatalogo | None = None,
) -> tuple[float, dict] | None:
    red_label = "SAN" if es_san else "ABA"
    logger.debug("[POZOS-%s] Entrada: L=%.2f P=%.2f DN=%d pozo_item=%s",
                 red_label, longitud, profundidad, diametro_mm,
                 pozo_item["label"] if pozo_item else None)
    if not precios.get("catalogo_pozos") or longitud <= 0:
        logger.debug("[POZOS-%s] Guard: catálogo vacío o L<=0 → None", red_label)
        return None

    if pozo_item is None:
        if precios["catalogo_pozos"]:
            red_label = "SAN" if es_san else "ABA"
            raise ValueError(
                f"Hay {len(precios['catalogo_pozos'])} pozos en el catálogo pero ninguno aplica "
                f"para red={red_label}, profundidad={profundidad:.1f} m, DN={diametro_mm} mm. "
                "Revisa los rangos en Administración de precios."
            )
        return None

    # Guardia SAN: rechazar el pozo genérico ABA (red=None) cuando estamos
    # en saneamiento. Ocurre cuando P supera el máximo del catálogo SAN (5 m).
    # El Excel EMASESA no define pozos SAN para esas profundidades → None.
    if es_san and pozo_item.get("red") is None:
        logger.warning(
            "[POZOS-SAN] P=%.2fm supera el máximo cubierto por el catálogo SAN "
            "(profundidad_max=5.0m). No existe pozo de registro SAN para esta "
            "profundidad en la Base de Precios EMASESA → partida nula.",
            profundidad,
        )
        return None

    intervalo = float(pozo_item.get("intervalo", 0))
    if intervalo <= 0:
        return None

    n_pozos = longitud / intervalo
    partidas: dict[str, float] = {
        pozo_item["label"]: _importe(n_pozos, pozo_item["precio"])
    }

    precio_tapa = float(pozo_item.get("precio_tapa", 0.0) or 0.0)
    if precio_tapa > 0:
        partidas[pozo_item["label"] + " (tapa)"] = _importe(n_pozos, precio_tapa)

    total = sum(partidas.values())
    logger.debug("[POZOS-%s] n=%.2f intervalo=%.1f → %.2f € (%d partidas)",
                 red_label, n_pozos, intervalo, total, len(partidas))
    return total, partidas


def capitulo_pozos_existentes(
    longitud: float, accion: str, red: str, precios: Precios
) -> tuple[float, dict] | None:
    logger.debug("[POZOS-EX] Entrada: L=%.2f accion=%s red=%s", longitud, accion, red)
    if accion == "none" or longitud <= 0:
        logger.debug("[POZOS-EX] Guard → None")
        return None
    catalogo = precios.get("catalogo_pozos_existentes", [])
    item = next(
        (x for x in catalogo if x["red"] == red and x["accion"] == accion), None
    )
    if item is None:
        logger.warning("[POZOS-EX] No se encontró item red=%s accion=%s en catálogo (%d items) → None",
                       red, accion, len(catalogo))
        return None
    intervalo = float(item.get("intervalo_m", 100.0))
    n = longitud / intervalo
    importe = _importe(n, item["precio"])
    label = f"{accion.capitalize()} pozos existentes {red}"
    logger.debug("[POZOS-EX] %s: n=%.2f × precio=%.4f = %.2f €", label, n, item["precio"], importe)
    return importe, {label: importe}


def capitulo_canones(
    canon_tierras: float, canon_mixto: float
) -> tuple[float, dict] | None:
    partidas: dict[str, float] = {}
    if canon_tierras > 0:
        partidas["Canon vertido tierras"] = canon_tierras
    if canon_mixto > 0:
        partidas["Canon vertido mixto"] = canon_mixto
    if not partidas:
        return None
    return sum(partidas.values()), partidas
