"""M14: tabla ``audit_log`` para trazabilidad de cambios de precios.

La tabla se crea vía ``_SCHEMA`` (``CREATE TABLE IF NOT EXISTS``). Esta
migración solo registra la versión. La lógica de escritura está en
``guardar_todo()`` de ``db_precios.py``: diff snapshot antes/después y se
registra cada cambio lógico.

Se optó por diff a nivel Python (no triggers row-level SQLite) porque
``guardar_todo()`` hace DELETE + INSERT wholesale de todas las tablas, lo
que produciría cientos de eventos espurios con triggers.
"""

from __future__ import annotations

import sqlite3

VERSION = 14
DESCRIPCION = "Tabla audit_log para trazabilidad (escritura desde guardar_todo)"


def aplicar(conn: sqlite3.Connection) -> None:
    # No-op: la tabla ya existe desde el schema. Esta migración solo registra
    # la versión para que los callers sepan que el audit_log está disponible.
    pass
