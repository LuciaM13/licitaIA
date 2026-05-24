"""Helper compartido por los bloques: ``_acumular``.

Cada bloque acumula sus partidas sobre un dict ``caps`` con la forma
``{"NOMBRE CAPITULO": {"subtotal": float, "partidas": dict}}``. Los
capítulos pueden recibir resultados en varias llamadas (p.ej. obra
civil base + cánones + pozos + valvulería) y el helper se encarga de
fusionar partidas y acumular subtotales.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _acumular(caps: dict, nombre: str, resultado: tuple[float, dict] | None) -> None:
    if resultado is None:
        logger.debug("[ACUM] '%s' → resultado=None, nada que acumular", nombre)
        return
    subtotal, partidas = resultado
    if subtotal == 0.0:
        logger.warning("[ACUM] '%s' tiene subtotal=0.0 con %d partidas: %s",
                       nombre, len(partidas), list(partidas.keys()))
    if nombre in caps:
        caps[nombre]["partidas"].update(partidas)
        caps[nombre]["subtotal"] += subtotal
        logger.debug("[ACUM] '%s' +%.2f € → acumulado=%.2f €",
                     nombre, subtotal, caps[nombre]["subtotal"])
    else:
        caps[nombre] = {"subtotal": subtotal, "partidas": dict(partidas)}
        logger.debug("[ACUM] '%s' nuevo → %.2f € (%d partidas)",
                     nombre, subtotal, len(partidas))
