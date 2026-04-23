"""M2: separar entibación ABA/SAN + frontera desmontaje DN=150.

H1: El Excel SAN usa D19>1.4 en la fórmula de precio (J17), no 1.5 m. Se
renombra la entrada wildcard a 'Entibación blindada ABA' y se inserta una
nueva para SAN con umbral 1.4 m.

H2: El desmontaje DN<150 mm tenía dn_max=149; el Excel usa >150 como frontera
(DN=150 pertenece al rango <150 mm), así que el dn_max correcto es 150.
"""

from __future__ import annotations

import sqlite3

VERSION = 2
DESCRIPCION = "Fix entibación SAN umbral 1.4m y desmontaje DN=150 frontera"


def aplicar(conn: sqlite3.Connection) -> None:
    # H1 - Paso 1: renombrar la entrada wildcard a ABA y asignarle red='ABA'
    conn.execute(
        "UPDATE entibacion SET label = 'Entibación blindada ABA', red = 'ABA' "
        "WHERE label = 'Entibación blindada' AND red IS NULL"
    )
    # H1 - Paso 2: insertar nueva entrada para SAN con umbral 1.4m
    # El precio base es el mismo (2.5.001 del Excel: 4.27 €/m², sin CI = 3.037096)
    conn.execute(
        "INSERT OR IGNORE INTO entibacion (label, precio_m2, umbral_m, red) "
        "VALUES ('Entibación blindada SAN', 3.037096, 1.4, 'SAN')"
    )
    # H2 - Corregir frontera desmontaje: dn_max 149 → 150
    conn.execute(
        "UPDATE desmontaje SET dn_max = 150 "
        "WHERE label = 'Desmontaje tubería DN<150mm' AND dn_max = 149"
    )
