"""M7: deduplicar ``demolicion`` por (red, unidad) + unique index.

El campo UNIQUE(red, label) no impedía dos filas con la misma (red, unidad)
si tenían labels distintos. ``demo_items()`` asume como máximo una fila por
unidad ('m2', 'm') y lanzaba ValueError en caso de duplicado.

Fix: conservar la fila con MAX(id) por (red, unidad) y añadir unique index.

Orden de ejecución: M7 corre ANTES que M6 por un artefacto histórico del
fichero original. El runner preserva ese orden declarativo para no alterar
el comportamiento sobre BDs intermedias.
"""

from __future__ import annotations

import sqlite3

VERSION = 7
DESCRIPCION = "Deduplicar demolicion (red, unidad) y añadir unique index"


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "DELETE FROM demolicion WHERE id NOT IN "
        "(SELECT MAX(id) FROM demolicion GROUP BY red, unidad)"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_demolicion_red_unidad "
        "ON demolicion(red, unidad)"
    )
