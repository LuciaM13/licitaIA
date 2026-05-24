"""Catálogo de precios EMASESA: carga, persistencia, diff y comparación.

API pública re-exportada (para mantener imports cortos):
  - ``cargar_precios``, ``aplicar_ci``  → ``src.catalogo.carga``
  - ``guardar_precios``                  → ``src.catalogo.guardado``
  - ``calcular_diff``                    → ``src.catalogo.diff``

Subpaquetes:
  - ``src.catalogo.repositorio`` — CRUD bajo nivel sobre SQLite (`cargar_todo`,
    `guardar_todo`, `insertar_fila_catalogo`, `escribir_audit_evento`).
  - ``src.catalogo.editor`` — use case de edición admin (preparar/ejecutar
    guardado, insertar variante inline).
"""

from __future__ import annotations

from src.catalogo.carga import aplicar_ci, cargar_precios
from src.catalogo.diff import calcular_diff
from src.catalogo.guardado import guardar_precios

__all__ = [
    "aplicar_ci",
    "calcular_diff",
    "cargar_precios",
    "guardar_precios",
]
