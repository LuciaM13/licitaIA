"""M16: añadir SAN bordillo 'generico' (fallback legacy).

M15 pobló variantes por material pero no creó fila generico para SAN 'm'
(SAN no tenía fila de bordillo pre-M15, así que no se duplicó). Sin esa
fila, cualquier caller de ``demo_items('SAN', ..., material_m='generico')``
recibe None silenciosamente. El peer review (C1) lo identificó como gap.

Fix: añadir (SAN, 'm', 'generico', 'Demolición bordillo', 403 cents) con
el mismo precio que ABA generico. El licitador puede sobrescribirlo
desde admin UI si la práctica real de SAN difiere.
"""

from __future__ import annotations

import sqlite3

VERSION = 16
DESCRIPCION = "Añadir SAN bordillo generico (fallback legacy, mismo precio que ABA)"


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO demolicion "
        "(red, label, unidad, material, precio, factor_ci) "
        "VALUES ('SAN', 'Demolición bordillo', 'm', 'generico', 403, 1.0)"
    )
