"""M8: drift sistémico Patrón A + Gres SAN DN300 (auditoría 2026-04-19).

H1: 18 precios con ratio Excel/BD = 1.05² (CI aplicado dos veces al guardar).
    Invariante del sistema: BD.precio × pct_ci(1.05) = precio Excel oficial.
    La BD almacena precio base sin margen; ``_aplicar_ci`` en precios.py lo
    multiplica por pct_ci en runtime. Los 18 precios están pre-divididos por
    CI dos veces, produciendo subestimación ~5 % en el presupuesto.
    Grupos afectados:
      - excavacion: 7 claves (mec, manual, transporte, relleno, canon)
      - tuberias ABA: FD DN80/100/150 y PE-100 DN90
      - valvuleria conexion: 6 rangos DN (1-400)
    Los demás precios del catálogo ya cumplen la invariante BD × 1.05 = Excel.

    UPDATEs condicionales (ABS(valor - drifted) < 0.005): si el admin UI ya
    había corregido el valor manualmente, el WHERE no matchea y es no-op.

H2: Gres SAN DN300 — drift aislado. Excel S-BASE r86 = 126.10 €/m, base correcta
    120.095238. La BD tenía 84.72381 (~29 % por debajo). Los demás DN de Gres
    SAN (400/500/600/800/1000) ya cumplen la invariante.
"""

from __future__ import annotations

import sqlite3

VERSION = 8
DESCRIPCION = "Fix drift Patrón A (18 precios ratio 1.05²) + Gres SAN DN300 aislado"


def aplicar(conn: sqlite3.Connection) -> None:
    # H1 — Patrón A
    excavacion_fix = [
        ("mec_hasta_25", 2.780952), ("mec_mas_25", 4.535148),
        ("manual_hasta_25", 10.133333), ("manual_mas_25", 12.689343),
        ("transporte", 4.8), ("relleno", 17.590476),
        ("canon_tierras", 1.451238),
    ]
    for clave, drifted in excavacion_fix:
        conn.execute(
            "UPDATE excavacion SET valor = valor * 1.05 "
            "WHERE clave = ? AND ABS(valor - ?) < 0.005",
            (clave, drifted),
        )
    tuberias_fix = [
        ("ABA", "FD", 80, 41.190476), ("ABA", "FD", 100, 43.361905),
        ("ABA", "FD", 150, 59.8),     ("ABA", "PE-100", 90, 9.990476),
    ]
    for red, tipo, dn, drifted in tuberias_fix:
        conn.execute(
            "UPDATE tuberias SET precio_m = precio_m * 1.05 "
            "WHERE red=? AND tipo=? AND diametro_mm=? "
            "  AND ABS(precio_m - ?) < 0.005",
            (red, tipo, dn, drifted),
        )
    valvuleria_fix = [
        (1, 100, 686.009524), (101, 150, 1765.514286),
        (151, 200, 1067.171429), (201, 250, 1320.790476),
        (251, 300, 1941.390476), (301, 400, 2373.819048),
    ]
    for dn_min, dn_max, drifted in valvuleria_fix:
        conn.execute(
            "UPDATE valvuleria SET precio = precio * 1.05 "
            "WHERE tipo='conexion' AND dn_min=? AND dn_max=? "
            "  AND ABS(precio - ?) < 0.005",
            (dn_min, dn_max, drifted),
        )
    # H2 — Gres SAN DN300
    conn.execute(
        "UPDATE tuberias SET precio_m = 120.095238 "
        "WHERE red='SAN' AND tipo='Gres' AND diametro_mm=300 "
        "  AND ABS(precio_m - 84.72381) < 0.005"
    )
