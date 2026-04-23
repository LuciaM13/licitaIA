"""
Shim de compatibilidad del antiguo ``src.reglas.trazabilidad``.

El módulo se renombró a ``src.reglas.explicaciones`` porque su cometido es
*explicar el ganador de cada desempate determinista*, no trazar razonamiento
CLIPS (CLIPS en este proyecto solo emite alertas).

La función pública ``generar_trazabilidad`` se mantiene como alias del
nuevo ``generar_explicaciones`` por compatibilidad con imports legacy.
La clave de persistencia ``presupuesto_trazabilidad`` en BD y la clave del
dict ``resultado["trazabilidad"]`` conservan su nombre.
"""

from __future__ import annotations

from src.reglas.explicaciones import (  # noqa: F401 (re-exportado)
    explicar_entibacion,
    explicar_pozo,
    explicar_valvuleria,
    explicar_desmontaje,
    generar_explicaciones,
    generar_explicaciones as generar_trazabilidad,
)

__all__ = [
    "explicar_entibacion",
    "explicar_pozo",
    "explicar_valvuleria",
    "explicar_desmontaje",
    "generar_explicaciones",
    "generar_trazabilidad",
]
