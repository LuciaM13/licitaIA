"""Runner idempotente de migraciones de schema.

``init_db()`` es el punto de entrada. Ejecuta, en orden:
  1. ``_SCHEMA`` DDL para crear tablas que aún no existen.
  2. Crea la tabla ``schema_version`` si no está.
  3. Despacha cada migración declarada en ``MIGRACIONES`` cuyo ``VERSION``
     sea mayor que el máximo registrado.

La variable ``version`` se captura UNA VEZ al inicio del dispatch, antes
de aplicar ninguna migración. Esto preserva el comportamiento original
del fichero monolítico, donde una migración con número N2 puede
declararse después que otra con N1 > N2 sin quedar bloqueada (el MAX en
``schema_version`` cambia durante el dispatch, pero la comparación usa
la versión inicial).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from src.infraestructura.db.connection import DB_PATH, conectar
from src.infraestructura.db.schema import _SCHEMA
from src.infraestructura.db.migrations import MIGRACIONES

logger = logging.getLogger(__name__)


def init_db(path: str | Path | None = None) -> None:
    """Crea todas las tablas si no existen y ejecuta migraciones pendientes. Idempotente."""
    logger.info("init_db() - path=%s", path or DB_PATH)
    with conectar(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        # Tabla de tracking de migraciones (se crea aquí para no mezclarla con _SCHEMA)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "  version INTEGER PRIMARY KEY,"
            "  descripcion TEXT NOT NULL,"
            "  aplicada_en TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        _ejecutar_migraciones(conn)
        conn.commit()
    logger.info("init_db() OK")


def _version_actual(conn: sqlite3.Connection) -> int:
    """Devuelve la versión de schema más alta aplicada, o 0 si no hay ninguna."""
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def _registrar_version(conn: sqlite3.Connection, version: int, descripcion: str) -> None:
    """Marca una migración como aplicada."""
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, descripcion) VALUES (?, ?)",
        (version, descripcion),
    )


def _ejecutar_migraciones(conn: sqlite3.Connection) -> None:
    """Ejecuta solo las migraciones que aún no se han aplicado.

    Cada migración tiene un número de versión. Solo se ejecuta si ese número
    es mayor que la versión capturada al inicio del dispatch (no el MAX
    actualizado por migraciones previas en la misma llamada).
    """
    version = _version_actual(conn)
    logger.debug("Versión actual del schema: %d", version)

    for mig in MIGRACIONES:
        if version < mig.VERSION:
            logger.debug("Aplicando M%02d: %s", mig.VERSION, mig.DESCRIPCION)
            mig.aplicar(conn)
            _registrar_version(conn, mig.VERSION, mig.DESCRIPCION)
