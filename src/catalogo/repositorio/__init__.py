"""CRUD de catálogos de precios.

Subpaquete con las 4 APIs públicas que consume la aplicación:
  - ``cargar_todo`` — lee toda la BD y construye el dict de precios.
  - ``guardar_todo`` — DELETE+INSERT atómico de catálogos completos (admin).
  - ``insertar_fila_catalogo`` — INSERT quirúrgico de UNA variante (Phase 3).
  - ``escribir_audit_evento`` — wrapper público para registrar 1 fila en
    ``audit_log`` (lo usan los use cases inline en
    ``src.catalogo.editor``).

Convención storage: la BD almacena los precios de catálogo como INTEGER
céntimos; las conversiones céntimos↔EUR viven en
``src.almacenamiento.conversion_centimos``.
"""

from __future__ import annotations

from src.catalogo.repositorio.audit import escribir_audit_evento
from src.catalogo.repositorio.carga_bd import cargar_todo
from src.catalogo.repositorio.guardado_bd import guardar_todo
from src.catalogo.repositorio.insercion_inline import insertar_fila_catalogo

__all__ = [
    "cargar_todo",
    "escribir_audit_evento",
    "guardar_todo",
    "insertar_fila_catalogo",
]
