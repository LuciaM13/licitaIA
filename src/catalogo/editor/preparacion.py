"""``preparar_guardado``: valida + diff, sin escribir nada.

La UI llama primero a ``preparar_guardado`` para mostrar al admin el
diálogo de confirmación con los cambios. Si confirma, se invoca
``persistencia.ejecutar_guardado``.
"""

from __future__ import annotations

import logging

from src.catalogo.diff import calcular_diff
from src.catalogo.editor.contratos import (
    CambioPrecio,
    ErrorValidacion,
    ResultadoPreparacion,
)
from src.catalogo.guardado import _validar_precios
from src.modelo.tipos import Precios

logger = logging.getLogger(__name__)


def preparar_guardado(
    precios_editados: Precios,
    precios_originales: Precios,
) -> ResultadoPreparacion:
    """Valida + diff sin escribir nada.

    Args:
        precios_editados: dict de precios tras las ediciones del admin.
        precios_originales: snapshot del dict antes de las ediciones.

    Returns:
        ``ResultadoPreparacion`` con errores de validación (bloquean
        guardado) y diff de cambios (para el diálogo de confirmación).
    """
    mensajes_validacion = _validar_precios(precios_editados)
    errores: list[ErrorValidacion] = [
        {"campo": "precios", "mensaje": m, "severidad": "error"}
        for m in mensajes_validacion
    ]

    diff_raw = calcular_diff(precios_originales, precios_editados)
    diff: list[CambioPrecio] = [
        {
            "categoria": str(d.get("seccion", "")),
            "clave": str(d.get("campo", "")),
            "antes": _a_float_o_none(d.get("valor_anterior")),
            "despues": _a_float_o_none(d.get("valor_nuevo")),
        }
        for d in diff_raw
    ]

    puede_guardar = not errores
    logger.info(
        "preparar_guardado → errores=%d, diff=%d, puede_guardar=%s",
        len(errores), len(diff), puede_guardar,
    )
    return {
        "errores": errores,
        "diff": diff,
        "puede_guardar": puede_guardar,
    }


def _a_float_o_none(v) -> float | None:
    """Intenta convertir a float; devuelve None si no es numérico."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
