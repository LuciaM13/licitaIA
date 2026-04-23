"""Paquete de base de datos SQLite para precios EMASESA.

Estructura interna:
  - ``connection`` — context manager ``conectar()`` + ``DB_PATH`` + whitelist.
  - ``schema`` — DDL de las tablas (``_SCHEMA``).
  - ``runner`` — ``init_db()`` y dispatcher de migraciones.
  - ``migrations/`` — una migración por fichero (M1 … M16).
  - ``helpers`` — utilidades de lectura (_rows_to_dicts, _cargar_por_red).

Los módulos de CRUD completo (``cargar_todo``/``guardar_todo``) viven en
``src.infraestructura.db_precios``; el historial en
``src.infraestructura.db_historial``.

Este ``__init__`` re-exporta los nombres que el resto del proyecto venía
importando desde el antiguo fichero ``src/infraestructura/db.py``, para
que el troceo sea transparente.
"""

from __future__ import annotations

from src.infraestructura.db.connection import (
    DB_PATH,
    _TABLAS_PERMITIDAS,
    conectar,
)
from src.infraestructura.db.runner import init_db
from src.infraestructura.db.helpers import (
    _rows_to_dicts,
    _cargar_por_red,
)

__all__ = [
    "DB_PATH",
    "_TABLAS_PERMITIDAS",
    "conectar",
    "init_db",
    "_rows_to_dicts",
    "_cargar_por_red",
]
