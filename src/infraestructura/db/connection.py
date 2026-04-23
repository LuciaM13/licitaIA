"""Context manager de conexión SQLite con PRAGMAs activados.

Abre conexiones con:
  - ``foreign_keys = ON`` para que los FK declarados en el schema sean reales.
  - ``journal_mode = WAL`` para permitir lectura concurrente mientras otra
    conexión escribe (evita ``database is locked`` en Streamlit con varias
    pestañas abiertas).

``DB_PATH`` apunta a ``<repo>/data/precios.db`` calculado desde la posición
del paquete, robusto ante cambios de working directory.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "precios.db"


_TABLAS_PERMITIDAS = frozenset({
    "tuberias", "acerados",
    "espesores_calzada", "acometida_defecto", "acometidas",
    "defaults_ui", "excavacion", "bordillos", "calzadas",
    "pozos", "entibacion", "valvuleria", "config", "demolicion",
    "subbases", "desmontaje", "imbornales", "pozos_existentes_precios",
    # Historial de presupuestos
    "presupuestos", "presupuesto_capitulos", "presupuesto_partidas",
    "presupuesto_parametros", "presupuesto_trazabilidad",
})


@contextmanager
def conectar(path: str | Path | None = None):
    """Context manager que abre conexión con FK activadas y cierra al salir.

    Activa WAL (Write-Ahead Logging) para permitir que múltiples lectores
    convivan con un único escritor sin bloquear. Necesario en Streamlit
    Cloud, donde los reruns del script pueden solapar lectura y escritura
    cuando hay varias pestañas abiertas. La primera conexión crea los
    ficheros auxiliares ``precios.db-wal`` y ``precios.db-shm``; ambos son
    temporales y se consolidan en ``precios.db`` al cerrar limpiamente.
    """
    db = path or DB_PATH
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
