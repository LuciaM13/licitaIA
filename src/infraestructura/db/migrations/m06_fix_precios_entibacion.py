"""M6: corregir precios base de entibación (auditoría 2026-04-13).

Los precios de entibación se almacenaron con un factor de división erróneo
(~1.406 en lugar de 1.05 CI). Verificación contra el Excel EMASESA:

  A-BASE PRECIOS D45 = 4.27 €/m² (ref 2.5.001) → sin CI = 4.27/1.05 = 4.066667
  S-BASE PRECIOS D49 = 4.27 €/m² (ref 2.5.001) → sin CI = 4.27/1.05 = 4.066667
  S-BASE PRECIOS D50 = 22.73 €/m² (ref 2.5.065) → sin CI = 22.73/1.05 = 21.647619

Contraste: demolición (D9=14.70/1.05=14.0) y pates (D188=1.94/1.05=1.8476)
estaban correctos, confirmando que el CI correcto es 1.05.

Impacto: las tres entradas de entibación estaban infravaloradas un ~25 %.
"""

from __future__ import annotations

import sqlite3

VERSION = 6
DESCRIPCION = (
    "Fix precios entibación: base 3.037→4.067 (superf) y 16.167→21.648 "
    "(profunda). Los anteriores usaban factor ~1.406 en vez de CI=1.05"
)


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE entibacion SET precio_m2 = 4.066667 "
        "WHERE label = 'Entibación blindada ABA'"
    )
    conn.execute(
        "UPDATE entibacion SET precio_m2 = 4.066667 "
        "WHERE label = 'Entibación blindada SAN'"
    )
    conn.execute(
        "UPDATE entibacion SET precio_m2 = 21.647619 "
        "WHERE label = 'Entibación blindada SAN profunda'"
    )
