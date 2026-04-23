"""Contratos (DTOs) de los use cases de aplicación.

Estos TypedDict son el lenguaje que hablan los use cases con la UI. No son
conceptos del dominio nuclear (presupuestación) sino shapes que describen
interacciones de casos de uso concretos (editar catálogo, etc.).

Mantenerlos aquí en vez de en ``src/domain/tipos.py`` evita que el dominio
se contamine con vocabulario de flujos administrativos (drifts contra
catálogo oficial, audit log, validación de edición).

Política de crecimiento
-----------------------
Este fichero se limita a contratos del flujo de edición de catálogo. Si
crecen contratos de otros use cases (exportación Word, simulación
masiva…), partir por contexto (``contratos_admin.py``,
``contratos_historial.py``, etc.) en lugar de acumular estructuras
heterogéneas.
"""

from __future__ import annotations

from typing import Literal, TypedDict


class ErrorValidacion(TypedDict):
    """Un fallo de validación encontrado al preparar un guardado."""
    campo: str                    # p.ej. "pct_gg", "catalogo_aba[12].precio_m"
    mensaje: str                  # texto legible en castellano
    severidad: Literal["error", "warning"]


class CambioPrecio(TypedDict):
    """Un cambio detectado en el diff antes ↔ después."""
    categoria: str                # p.ej. "catalogo_aba"
    clave: str                    # identificador del ítem
    antes: float | None           # None en INSERT
    despues: float | None         # None en DELETE


class DriftOficial(TypedDict):
    """Un ítem editado cuyo precio BD × pct_ci difiere del Excel oficial."""
    categoria: str
    clave: str
    precio_bd: float
    precio_oficial: float
    ratio: float                  # precio_bd × pct_ci / precio_oficial


class ResultadoPreparacion(TypedDict):
    """Output de ``editar_catalogo.preparar_guardado``.

    La UI usa este shape para decidir si permitir el guardado (bloqueado
    si ``errores`` no está vacío), qué cambios mostrar en el diálogo de
    confirmación, y qué drifts resaltar como alertas no bloqueantes.
    """
    errores: list[ErrorValidacion]
    diff: list[CambioPrecio]
    drifts: list[DriftOficial]
    puede_guardar: bool
