"""Re-export para retrocompatibilidad.

La lógica de persistencia del historial vive en `src.almacenamiento.historial`.
Este módulo solo re-exporta los nombres públicos para no romper importadores
existentes (`pages/historial.py`, tests, etc.).

La frontera correcta es presupuesto → almacenamiento; mantener este shim
permite migrar consumidores progresivamente.
"""

from __future__ import annotations

from src.almacenamiento.historial import (  # noqa: F401
    contar_presupuestos,
    eliminar_presupuesto,
    guardar_presupuesto,
    listar_presupuestos,
    obtener_presupuesto,
)

__all__ = [
    "contar_presupuestos",
    "eliminar_presupuesto",
    "guardar_presupuesto",
    "listar_presupuestos",
    "obtener_presupuesto",
]
