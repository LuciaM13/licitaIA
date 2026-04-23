"""Helpers de lectura SQLite compartidos por los módulos CRUD.

Solo se exponen utilidades pequeñas y deterministas; las funciones de
carga/guardado completas viven en ``src.infraestructura.db_precios`` y
``src.infraestructura.db_historial``.
"""

from __future__ import annotations

import sqlite3

from src.infraestructura.db.connection import _TABLAS_PERMITIDAS


def _rows_to_dicts(cursor: sqlite3.Cursor, exclude: set[str] | None = None) -> list[dict]:
    """Convierte filas sqlite3.Row a lista de dicts, excluyendo columnas indicadas."""
    exclude = exclude or set()
    return [
        {k: row[k] for k in row.keys() if k not in exclude}
        for row in cursor.fetchall()
    ]


def _cargar_por_red(conn, tabla: str, columnas: str, clave_base: str,
                    order_by: str | None = None) -> dict:
    """Carga filas de una tabla con columna 'red' y devuelve dos listas keyed por ABA/SAN.

    SEGURIDAD: ``columnas`` y ``order_by`` se interpolan en SQL con f-string.
    Solo pasar literales definidos en este módulo, nunca input de usuario.
    La whitelist ``_TABLAS_PERMITIDAS`` impide tablas fuera del set conocido.
    """
    if tabla not in _TABLAS_PERMITIDAS:
        raise ValueError(f"Tabla no permitida: {tabla!r}")
    orden = order_by or columnas.split(",")[0].strip()
    resultado = {}
    for red in ("ABA", "SAN"):
        cursor = conn.execute(
            f"SELECT {columnas} FROM {tabla} WHERE red=? ORDER BY {orden}",
            (red,),
        )
        resultado[f"{clave_base}_{red.lower()}"] = _rows_to_dicts(cursor)
    return resultado
