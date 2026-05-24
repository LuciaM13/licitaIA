"""Wrapper trivial sobre src.presupuesto.orquestador.calcular_presupuesto.

Anade contexto al ValueError si el calculo falla por algun item no resuelto.
"""

from __future__ import annotations

import logging
from typing import Any

from src.modelo.parametros import ParametrosProyecto
from src.presupuesto.orquestador import calcular_presupuesto

logger = logging.getLogger(__name__)


def ejecutar(p: ParametrosProyecto, precios_base: dict[str, Any], *, expediente: str = "") -> dict:
    logger.info("ejecutor.ejecutar INICIO expediente=%s", expediente or "<sin nombre>")
    try:
        resultado = calcular_presupuesto(p, precios_base)
    except ValueError as e:
        msg = f"[{expediente}] fallo calcular_presupuesto: {e}" if expediente else str(e)
        raise ValueError(msg) from e
    logger.info("ejecutor.ejecutar FIN pem=%.2f total=%.2f",
                float(resultado.get("pem", 0.0)), float(resultado.get("total", 0.0)))
    return resultado
