"""M11: residuales Patrón A en excavación (carga_mec + arrinonado).

Al elevar la cobertura del test al 100 % contra el catálogo oficial, emergieron
dos claves adicionales de ``excavacion`` con el mismo patrón CI² que M8 no cubrió:

  - carga_mec: BD 0.304762 → BD×1.05 = 0.32 vs Excel 0.34. Ratio 0.34/0.304762 = 1.1155 ≈ 1.05².
  - arrinonado: BD 20.114286 → BD×1.05 = 21.12 vs Excel 22.18. Ratio 1.1025 = 1.05² exacto.

Corrige estableciendo el valor base canónico = Excel / 1.05 (idempotente,
con guarda en valor drifted).
"""

from __future__ import annotations

import sqlite3

VERSION = 11
DESCRIPCION = "Fix residuales Patrón A en excavación (carga_mec, arrinonado)"


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE excavacion SET valor = 0.323810 "
        "WHERE clave = 'carga_mec' AND ABS(valor - 0.304762) < 0.005"
    )
    conn.execute(
        "UPDATE excavacion SET valor = 21.123810 "
        "WHERE clave = 'arrinonado' AND ABS(valor - 20.114286) < 0.005"
    )
