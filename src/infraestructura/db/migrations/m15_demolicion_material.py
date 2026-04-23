"""M15: demolición con variantes por material.

El Excel oficial EMASESA lista varios precios de demolición según material:
  Bordillo: Granítico 5.59, Hidráulico 4.44 €/m.
  Calzada: adoquín 15.80, aglomerado 14.29, hormigón 17.43 €/m².
  Acerado: Losa Hidráulica / Losa Terrazo / Hormigón 14.70 €/m².

La BD tenía 1 fila flat por (red, unidad). Se añade columna ``material`` como
identificador semántico. El unique index ``(red, unidad)`` se reemplaza por
``(red, unidad, material)`` para permitir múltiples variantes.
"""

from __future__ import annotations

import sqlite3

from src.domain.constantes import PCT_CI_DEFAULT

VERSION = 15
DESCRIPCION = (
    "Demolición con variantes por material (granitico/hidraulico/adoquin/etc.)"
)


def aplicar(conn: sqlite3.Connection) -> None:
    # 1) Añadir columna `material` vía recreación de tabla (SQLite no
    #    permite ALTER para modificar unique index).
    conn.executescript("""
        DROP INDEX IF EXISTS idx_demolicion_red_unidad;

        CREATE TABLE demolicion_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            label TEXT NOT NULL,
            unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
            material TEXT NOT NULL DEFAULT 'generico',
            precio INTEGER NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
            UNIQUE(red, unidad, material)
        );
        INSERT INTO demolicion_new (id, red, label, unidad, material, precio, factor_ci)
            SELECT id, red, label, unidad, 'generico', precio, factor_ci FROM demolicion;
        DROP TABLE demolicion;
        ALTER TABLE demolicion_new RENAME TO demolicion;
    """)

    # 2) Poblar variantes desde el Excel (precios base = Excel / 1.05, en céntimos).
    #    Las filas 'generico' quedan para que presupuestos existentes no rompan,
    #    pero la UI empujará al usuario a elegir material específico.
    variantes = [
        # (red, label, unidad, material, precio_excel)
        ("ABA", "Demolición bordillo granítico",  "m",  "granitico",   5.59),
        ("ABA", "Demolición bordillo hidráulico", "m",  "hidraulico",  4.44),
        ("ABA", "Demolición calzada adoquín",     "m2", "adoquin",    15.80),
        ("ABA", "Demolición calzada aglomerado",  "m2", "aglomerado", 14.29),
        ("ABA", "Demolición calzada hormigón",    "m2", "hormigon",   17.43),
        ("ABA", "Demolición acerado losa hidráulica", "m2", "losa_hidraulica", 14.70),
        ("ABA", "Demolición acerado losa terrazo",    "m2", "losa_terrazo",    14.70),
        ("ABA", "Demolición acerado hormigón",        "m2", "hormigon_acerado", 14.70),
        ("SAN", "Demolición bordillo granítico",  "m",  "granitico",   5.59),
        ("SAN", "Demolición bordillo hidráulico", "m",  "hidraulico",  4.44),
        ("SAN", "Demolición calzada adoquín",     "m2", "adoquin",    15.80),
        ("SAN", "Demolición calzada aglomerado",  "m2", "aglomerado", 14.29),
        ("SAN", "Demolición calzada hormigón",    "m2", "hormigon",   17.43),
        ("SAN", "Demolición acerado losa hidráulica", "m2", "losa_hidraulica", 14.70),
        ("SAN", "Demolición acerado losa terrazo",    "m2", "losa_terrazo",    14.70),
        ("SAN", "Demolición acerado hormigón",        "m2", "hormigon_acerado", 14.70),
    ]
    for red, label, unidad, material, precio_excel in variantes:
        precio_base_cents = round((precio_excel / PCT_CI_DEFAULT) * 100)
        conn.execute(
            "INSERT OR IGNORE INTO demolicion (red, label, unidad, material, precio, factor_ci) "
            "VALUES (?, ?, ?, ?, ?, 1.0)",
            (red, label, unidad, material, precio_base_cents),
        )
