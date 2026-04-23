"""M4: correcciones auditadas 2026-04-12.

H1: precio base demolición acerado (ABA y SAN) era ~7.44; debería ser 14.0
    Excel S/A-BASE PRECIOS D9 = 14.70 €/m² → base sin CI = 14.70 / 1.05 = 14.0
    El precio anterior (7.438095) era ~la mitad del correcto, causando una
    infravaloración del ~50 % en demolición de acerado.

H2: los pozos SAN con dn_max=2500 no cubren la tubería HA+PE80 Ø3000 mm.
    Se extiende dn_max a 9999 para los tres tramos de profundidad (P<2.5,
    P<3.5, P<5) que actualmente llegan a dn_max=2500, usando el precio del
    tramo más próximo (DN≤2500) al no existir referencia Excel para DN=3000.
"""

from __future__ import annotations

import sqlite3

VERSION = 4
DESCRIPCION = "Fix dem acerado base 7.44→14.0; pozos SAN dn_max 2500→9999 para DN>=3000"


def aplicar(conn: sqlite3.Connection) -> None:
    # H1: corregir precio base demolición acerado
    conn.execute(
        "UPDATE demolicion SET precio = 14.0 "
        "WHERE label = 'Demolición acerado' AND ABS(precio - 7.438095) < 0.01"
    )
    # H2: extender cobertura pozos SAN de dn_max=2500 a dn_max=9999
    conn.execute(
        "UPDATE pozos SET dn_max = 9999 "
        "WHERE red = 'SAN' AND dn_max = 2500"
    )
