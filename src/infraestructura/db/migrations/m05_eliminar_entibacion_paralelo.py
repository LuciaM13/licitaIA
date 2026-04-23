"""M5: eliminar 'Entibación tipo paralelo' (código muerto).

H1: 'Entibación tipo paralelo' (red=SAN, umbral=2.5) es código muerto.
    La regla CLIPS usa >= desde esta misma sesión (antes usaba >), por lo
    que para P>=2.5 SAN ahora compiten:
      - "Entibación tipo paralelo"      umbral=2.5  precio=16.961476
      - "Entibación blindada SAN profunda" umbral=2.5  precio=16.167024

    El desempate elige el de MAYOR umbral y en empate el MENOR índice. "Tipo
    paralelo" siempre ganaba por tener id=37 vs id=39, dejando el item de
    Migración 3 inaccesible. Además, "tipo paralelo" tenía el precio un
    ~4.9 % más alto que el item correcto (sobrevaloración equivalente a un
    doble CI).

    Fix: eliminar 'Entibación tipo paralelo' para que 'Entibación blindada
    SAN profunda' sea el único candidato en P>=2.5 SAN.

H2 (relacionado con H1): el cambio de > a >= en la regla CLIPS también
    corrige la frontera P=2.5 SAN: antes seleccionaba el precio superficial
    (~3.19 €/m²) cuando el Excel usa el profundo (~16.98 €/m²).
"""

from __future__ import annotations

import sqlite3

VERSION = 5
DESCRIPCION = (
    "Eliminar 'Entibación tipo paralelo' (dead code): profunda SAN ya "
    "cubierta por 'Entibación blindada SAN profunda'"
)


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "DELETE FROM entibacion WHERE label = 'Entibación tipo paralelo'"
    )
