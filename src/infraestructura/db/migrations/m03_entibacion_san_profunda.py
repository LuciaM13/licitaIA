"""M3: añadir entibación SAN profunda (P ≥ 2.5 m).

El Excel SAN usa dos precios de entibación en J17:
  IF(D19>1.4, IF(D19<2.5, D49, D50), 0)
  D49 = 4.27 €/m² (ref 2.5.001, superficial) → base 3.037096 (ya existe)
  D50 = 22.73 €/m² (ref 2.5.065, profunda)   → base 16.167024

Faltaba el segundo registro. ``desempatar_entibacion()`` ya elige el
candidato con mayor umbral_m, así que basta con insertar el dato.
"""

from __future__ import annotations

import sqlite3

VERSION = 3
DESCRIPCION = "Añadir entibación SAN profunda P>=2.5m (22.73 €/m²)"


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO entibacion (label, precio_m2, umbral_m, red) "
        "VALUES ('Entibación blindada SAN profunda', 16.167024, 2.5, 'SAN')"
    )
