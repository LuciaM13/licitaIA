"""Use case: editar el catálogo de precios desde la UI admin.

Dos funciones públicas:
  - ``preparar_guardado(editados, originales)`` — valida, calcula diff y
    drifts sin escribir. La UI usa el resultado para mostrar el diálogo de
    confirmación y bloquear el guardado si hay errores.
  - ``ejecutar_guardado(editados)`` — persiste tras confirmación. Propaga
    ``ValueError`` si la validación final falla o la BD rechaza los datos.

No importa Streamlit. Los widgets de ``pages/admin_precios.py`` invocan
este use case y consumen el shape ``ResultadoPreparacion`` declarado en
``src.aplicacion.contratos``.
"""

from __future__ import annotations

import logging

from src.aplicacion.contratos import (
    CambioPrecio,
    DriftOficial,
    ErrorValidacion,
    ResultadoPreparacion,
)
from src.domain.tipos import Precios
from src.infraestructura.diff_precios import calcular_diff
from src.infraestructura.precios import _validar_precios, guardar_precios
from src.infraestructura.validacion_oficial import detectar_drifts

logger = logging.getLogger(__name__)


def preparar_guardado(
    precios_editados: Precios,
    precios_originales: Precios,
) -> ResultadoPreparacion:
    """Valida + diff + drifts sin escribir nada.

    Args:
        precios_editados: dict de precios tras las ediciones del admin.
        precios_originales: snapshot del dict antes de las ediciones.

    Returns:
        ``ResultadoPreparacion`` con errores de validación (bloquean
        guardado), diff de cambios (para el diálogo de confirmación) y
        drifts contra el catálogo oficial (alertas no bloqueantes).
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

    drifts_raw = detectar_drifts(precios_editados)
    drifts: list[DriftOficial] = [
        {
            "categoria": str(d.get("categoria", "")),
            "clave": str(d.get("concepto", "")),
            "precio_bd": float(d.get("bd_precio", 0.0)),
            "precio_oficial": float(d.get("precio_oficial", 0.0)),
            "ratio": float(d.get("precio_con_ci", 0.0)) / float(d["precio_oficial"])
                     if d.get("precio_oficial") else 0.0,
        }
        for d in drifts_raw
    ]

    puede_guardar = not errores
    logger.info(
        "preparar_guardado → errores=%d, diff=%d, drifts=%d, puede_guardar=%s",
        len(errores), len(diff), len(drifts), puede_guardar,
    )
    return {
        "errores": errores,
        "diff": diff,
        "drifts": drifts,
        "puede_guardar": puede_guardar,
    }


def ejecutar_guardado(precios_editados: Precios) -> None:
    """Persiste los precios editados. Propaga ``ValueError`` si falla.

    La UI debe invalidar su caché (``cargar_precios.clear()``) tras un
    guardado exitoso.
    """
    logger.info("ejecutar_guardado → persistiendo precios editados")
    guardar_precios(precios_editados)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _a_float_o_none(v) -> float | None:
    """Intenta convertir a float; devuelve None si no es numérico."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
