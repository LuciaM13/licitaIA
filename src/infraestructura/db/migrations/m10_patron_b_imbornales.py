"""M10: Patrón B — 5 precios de imbornales con CI aplicado tres veces.

5 precios con ratio Excel/BD = 1.05³. Verificación manual contra el Excel
S-BASE r106-112 confirma que las unidades coinciden (ambas incluyen
acometida del imbornal). El fix alinea BD × 1.05 = Excel oficial para los
5 ítems. Si en el futuro aparece evidencia contraria, se reverte con una
migración correctiva siguiente.
"""

from __future__ import annotations

import sqlite3

VERSION = 10
DESCRIPCION = "Fix Patrón B imbornales (ratio 1.05³) alineado con Excel oficial"


def aplicar(conn: sqlite3.Connection) -> None:
    imbornales_fix = [
        ("Adaptación imbornal",                138.920209, 114.285714),
        ("Imbornal buzón c/clapeta",          1009.477941, 830.504762),
        ("Imbornal buzón s/clapeta",           928.452294, 763.838095),
        ("Imbornal nuevo rejilla c/clapeta",   634.360557, 521.885714),
        ("Imbornal nuevo rejilla s/clapeta",   634.360557, 521.885714),
    ]
    for label, drifted, correcto in imbornales_fix:
        conn.execute(
            "UPDATE imbornales SET precio = ? "
            "WHERE label = ? AND ABS(precio - ?) < 0.005",
            (correcto, label, drifted),
        )
