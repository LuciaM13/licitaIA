"""M9: ajustar residual de precisión tras M8 en ``mec_hasta_25``.

M8 aplicó "valor = valor × 1.05" sobre valores BD originales guardados con
6 decimales truncados. Para la mayoría de ítems, el resultado coincide con
el valor canónico (Excel/1.05) dentro del 0.1 % de tolerancia. Excepción:
``mec_hasta_25`` estaba guardado como 2.780952 (≈ 3.07/1.05²=2.78458 truncado
con error residual), así que tras ×1.05 queda 2.9200 vs canónico 2.9238 →
drift residual -0.13 %. Se corrige con valor exacto 3.07/1.05 = 2.923810.
"""

from __future__ import annotations

import sqlite3

VERSION = 9
DESCRIPCION = "Fix residual mec_hasta_25 (2.92→2.9238) para invariante BD × 1.05 = 3.07"


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE excavacion SET valor = 2.923810 "
        "WHERE clave = 'mec_hasta_25' AND ABS(valor - 2.92) < 0.005"
    )
