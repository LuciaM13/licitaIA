"""Validación de los parámetros de entrada del licitador.

Se invoca desde ``pages/calculadora.py`` antes de llamar al orquestador
de cálculo. Reglas mínimas: al menos una red activa, longitudes y
profundidades > 0 cuando la red corresponde está activa.
"""

from __future__ import annotations

import logging

from src.modelo.parametros import ParametrosProyecto

logger = logging.getLogger(__name__)


def validar_parametros(p: ParametrosProyecto) -> list[str]:
    """Valida parámetros de entrada. Retorna lista de errores (vacía si OK)."""
    errores = []
    if p.aba_item is None and p.san_item is None:
        errores.append("Debe incluir al menos abastecimiento o saneamiento.")
    if p.aba_item is not None and p.aba_longitud_m <= 0:
        errores.append("Longitud de abastecimiento debe ser > 0.")
    if p.san_item is not None and p.san_longitud_m <= 0:
        errores.append("Longitud de saneamiento debe ser > 0.")
    if p.aba_item is not None and p.aba_profundidad_m <= 0:
        errores.append("Profundidad de abastecimiento debe ser > 0.")
    if p.san_item is not None and p.san_profundidad_m <= 0:
        errores.append("Profundidad de saneamiento debe ser > 0.")
    if errores:
        logger.warning("validar_parametros: %d error(es) de validación: %s", len(errores), errores)
    else:
        logger.debug("validar_parametros: OK")
    return errores
