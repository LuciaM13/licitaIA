"""M1: columnas nuevas (factor_piezas, precio_material, precio_tapa, ...) + datos iniciales.

Añade columnas que no existían en el schema original y siembra valores
por defecto para tipos de tubería y materiales de pozos SAN.

Nota histórica: aquí se hacía UPDATE factor_piezas=1.2 para ABA; retirado
en audit A2C (2026-04-19) porque el Excel EMASESA ya incluye piezas en el
precio unitario de acometida (duplicaba el encarecimiento).

Tras M13 (INTEGER céntimos), los valores se insertan en cents directamente
(15273 y 185) para que la migración sea idempotente sobre una BD fresca.
"""

from __future__ import annotations

import sqlite3

VERSION = 1
DESCRIPCION = "Columnas nuevas + datos iniciales por defecto"


def aplicar(conn: sqlite3.Connection) -> None:
    def _columnas_existentes(tabla: str) -> set[str]:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({tabla})")}

    migraciones_col = [
        ("tuberias",   "factor_piezas",      "REAL NOT NULL DEFAULT 1.0"),
        ("tuberias",   "precio_material_m",  "REAL NOT NULL DEFAULT 0.0"),
        ("valvuleria", "factor_piezas",       "REAL NOT NULL DEFAULT 1.2"),
        ("valvuleria", "precio_material",     "REAL NOT NULL DEFAULT 0.0"),
        ("pozos",      "precio_tapa",         "REAL NOT NULL DEFAULT 0.0"),
        ("pozos",      "precio_tapa_material","REAL NOT NULL DEFAULT 0.0"),
        ("pozos",      "precio_pate_material","REAL NOT NULL DEFAULT 0.0"),
        ("acometidas", "factor_piezas",       "REAL NOT NULL DEFAULT 1.0"),
    ]
    for tabla, columna, definicion in migraciones_col:
        cols = _columnas_existentes(tabla)
        if columna not in cols:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")

    # Valores iniciales en cents (post-M13). En BDs viejas M13 ya convirtió los
    # REAL a INTEGER; en fresh clones, M1 corre sobre columnas INTEGER y debe
    # insertar cents directamente. 152.7333 € → 15273 cents; 1.8476 € → 185 cents.
    conn.execute(
        "UPDATE pozos SET precio_tapa_material = 15273 "
        "WHERE red = 'SAN' AND precio_tapa_material = 0"
    )
    conn.execute(
        "UPDATE pozos SET precio_pate_material = 185 "
        "WHERE red = 'SAN' AND precio_pate_material = 0"
    )
    _factores_defecto = {
        "FD": 1.2, "PE-100": 1.2, "PE-80": 1.2,
        "Gres": 1.35, "PVC": 1.2,
        "Hormigón": 1.0, "HA": 1.0,
        "HA+PE80": 1.4,
    }
    for tipo, factor in _factores_defecto.items():
        conn.execute(
            "UPDATE tuberias SET factor_piezas = ? WHERE tipo = ? AND factor_piezas = 1.0",
            (factor, tipo),
        )
