"""Bootstrap idempotente del schema de la BD.

``init_db()`` es el punto de entrada. Ejecuta ``_SCHEMA`` (DDL con
``CREATE TABLE IF NOT EXISTS`` para todas las tablas), de modo que
sobre una BD vacía construye el schema completo y sobre una BD ya
poblada no hace nada. No hay migraciones versionadas: cualquier
cambio estructural se aplica editando ``_SCHEMA`` directamente.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.almacenamiento.conexion import DB_PATH, conectar
from src.almacenamiento.schema import _SCHEMA

logger = logging.getLogger(__name__)


def init_db(path: str | Path | None = None) -> None:
    """Crea todas las tablas si no existen. Idempotente."""
    logger.info("init_db() - path=%s", path or DB_PATH)
    with conectar(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        conn.commit()
    logger.info("init_db() OK")
