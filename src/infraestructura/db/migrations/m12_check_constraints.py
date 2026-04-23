"""M12: CHECK constraints de integridad en todas las tablas de precios.

SQLite no admite ALTER TABLE ADD CHECK; la única forma de añadir checks a
tablas existentes es recrearlas. Patrón canónico:
  CREATE TABLE X_new (...) con CHECK añadidos
  INSERT INTO X_new SELECT ... FROM X
  DROP TABLE X
  ALTER TABLE X_new RENAME TO X

Los índices UNIQUE de M7 se recrean al final.

CHECKs añadidos (mínimos, centrados en invariantes de datos de precios):
  - precio > 0 en todas las tablas de catálogo de precios.
  - diametro_mm > 0 en tuberias; dn_min <= dn_max en valvuleria.
  - factor_piezas ∈ [0.5, 2.0] en tablas que lo tienen.
  - unidad ∈ {'m','m2','m3','ud'} donde aplica.

Esta migración es uno de los dos "mini-proyectos" dentro del runner (el otro
es M13). Pese a su tamaño, es puramente mecánica: cada ``executescript``
recrea UNA tabla preservando datos.
"""

from __future__ import annotations

import sqlite3

VERSION = 12
DESCRIPCION = "CHECK constraints completos en tablas de precios (defensa en profundidad)"


def aplicar(conn: sqlite3.Connection) -> None:
    # tuberias
    conn.executescript("""
        CREATE TABLE tuberias_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            label TEXT NOT NULL,
            tipo  TEXT NOT NULL,
            diametro_mm  INTEGER NOT NULL CHECK(diametro_mm > 0),
            precio_m     REAL NOT NULL CHECK(precio_m > 0),
            factor_piezas     REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
            precio_material_m REAL NOT NULL DEFAULT 0.0 CHECK(precio_material_m >= 0),
            UNIQUE(red, label)
        );
        INSERT INTO tuberias_new (id, red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m)
            SELECT id, red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m FROM tuberias;
        DROP TABLE tuberias;
        ALTER TABLE tuberias_new RENAME TO tuberias;
    """)
    # valvuleria
    conn.executescript("""
        CREATE TABLE valvuleria_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            tipo  TEXT NOT NULL,
            dn_min        INTEGER NOT NULL CHECK(dn_min > 0),
            dn_max        INTEGER NOT NULL CHECK(dn_max >= dn_min),
            precio        REAL NOT NULL CHECK(precio > 0),
            intervalo_m   REAL NOT NULL CHECK(intervalo_m > 0),
            instalacion   TEXT CHECK(instalacion IS NULL OR instalacion IN ('enterrada', 'pozo')),
            factor_piezas  REAL NOT NULL DEFAULT 1.2 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
            precio_material REAL NOT NULL DEFAULT 0.0 CHECK(precio_material >= 0)
        );
        INSERT INTO valvuleria_new SELECT * FROM valvuleria;
        DROP TABLE valvuleria;
        ALTER TABLE valvuleria_new RENAME TO valvuleria;
    """)
    # entibacion
    conn.executescript("""
        CREATE TABLE entibacion_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label     TEXT NOT NULL UNIQUE,
            precio_m2 REAL NOT NULL CHECK(precio_m2 > 0),
            umbral_m  REAL NOT NULL CHECK(umbral_m > 0),
            red       TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN'))
        );
        INSERT INTO entibacion_new SELECT * FROM entibacion;
        DROP TABLE entibacion;
        ALTER TABLE entibacion_new RENAME TO entibacion;
    """)
    # pozos
    conn.executescript("""
        CREATE TABLE pozos_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label            TEXT NOT NULL,
            precio           REAL NOT NULL CHECK(precio > 0),
            intervalo        REAL NOT NULL CHECK(intervalo > 0),
            red              TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN')),
            profundidad_max  REAL CHECK(profundidad_max IS NULL OR profundidad_max > 0),
            dn_max           INTEGER CHECK(dn_max IS NULL OR dn_max > 0),
            precio_tapa      REAL NOT NULL DEFAULT 0.0 CHECK(precio_tapa >= 0),
            precio_tapa_material REAL NOT NULL DEFAULT 0.0 CHECK(precio_tapa_material >= 0),
            precio_pate_material REAL NOT NULL DEFAULT 0.0 CHECK(precio_pate_material >= 0)
        );
        INSERT INTO pozos_new SELECT * FROM pozos;
        DROP TABLE pozos;
        ALTER TABLE pozos_new RENAME TO pozos;
    """)
    # acerados
    conn.executescript("""
        CREATE TABLE acerados_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red    TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            label  TEXT NOT NULL,
            unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
            precio REAL NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
            UNIQUE(red, label)
        );
        INSERT INTO acerados_new (id, red, label, unidad, precio, factor_ci)
            SELECT id, red, label, unidad, precio, factor_ci FROM acerados;
        DROP TABLE acerados;
        ALTER TABLE acerados_new RENAME TO acerados;
    """)
    # bordillos
    conn.executescript("""
        CREATE TABLE bordillos_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label  TEXT NOT NULL UNIQUE,
            unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'ud')),
            precio REAL NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
        );
        INSERT INTO bordillos_new (id, label, unidad, precio, factor_ci)
            SELECT id, label, unidad, precio, factor_ci FROM bordillos;
        DROP TABLE bordillos;
        ALTER TABLE bordillos_new RENAME TO bordillos;
    """)
    # calzadas (preservar espesores_calzada con FK CASCADE)
    conn.executescript("""
        CREATE TEMP TABLE _espesores_backup AS SELECT * FROM espesores_calzada;

        PRAGMA foreign_keys = OFF;

        CREATE TABLE calzadas_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label  TEXT NOT NULL UNIQUE,
            unidad TEXT NOT NULL CHECK(unidad IN ('m2', 'm3')),
            precio REAL NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
        );
        INSERT INTO calzadas_new (id, label, unidad, precio, factor_ci)
            SELECT id, label, unidad, precio, factor_ci FROM calzadas;
        DROP TABLE calzadas;
        ALTER TABLE calzadas_new RENAME TO calzadas;

        DELETE FROM espesores_calzada;
        INSERT INTO espesores_calzada (calzada_id, espesor_m)
            SELECT calzada_id, espesor_m FROM _espesores_backup;

        DROP TABLE _espesores_backup;

        PRAGMA foreign_keys = ON;
    """)
    # demolicion (recrear también el UNIQUE INDEX de M7)
    conn.executescript("""
        CREATE TABLE demolicion_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            label TEXT NOT NULL,
            unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
            precio REAL NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
            UNIQUE(red, label)
        );
        INSERT INTO demolicion_new (id, red, label, unidad, precio, factor_ci)
            SELECT id, red, label, unidad, precio, factor_ci FROM demolicion;
        DROP TABLE demolicion;
        ALTER TABLE demolicion_new RENAME TO demolicion;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_demolicion_red_unidad
            ON demolicion(red, unidad);
    """)
    # acometidas
    conn.executescript("""
        CREATE TABLE acometidas_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            tipo  TEXT NOT NULL,
            precio REAL NOT NULL CHECK(precio > 0),
            factor_piezas REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
            UNIQUE(red, tipo)
        );
        INSERT INTO acometidas_new SELECT * FROM acometidas;
        DROP TABLE acometidas;
        ALTER TABLE acometidas_new RENAME TO acometidas;
    """)
    # subbases
    conn.executescript("""
        CREATE TABLE subbases_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            precio_m3 REAL NOT NULL CHECK(precio_m3 > 0)
        );
        INSERT INTO subbases_new SELECT * FROM subbases;
        DROP TABLE subbases;
        ALTER TABLE subbases_new RENAME TO subbases;
    """)
    # desmontaje
    conn.executescript("""
        CREATE TABLE desmontaje_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label    TEXT NOT NULL UNIQUE,
            dn_max   INTEGER NOT NULL CHECK(dn_max > 0),
            precio_m REAL NOT NULL CHECK(precio_m > 0),
            es_fibrocemento INTEGER NOT NULL DEFAULT 0 CHECK(es_fibrocemento IN (0, 1))
        );
        INSERT INTO desmontaje_new SELECT * FROM desmontaje;
        DROP TABLE desmontaje;
        ALTER TABLE desmontaje_new RENAME TO desmontaje;
    """)
    # imbornales
    conn.executescript("""
        CREATE TABLE imbornales_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            precio REAL NOT NULL CHECK(precio > 0),
            tipo  TEXT NOT NULL CHECK(tipo IN ('adaptacion', 'nuevo'))
        );
        INSERT INTO imbornales_new SELECT * FROM imbornales;
        DROP TABLE imbornales;
        ALTER TABLE imbornales_new RENAME TO imbornales;
    """)
    # pozos_existentes_precios
    conn.executescript("""
        CREATE TABLE pozos_existentes_precios_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            accion TEXT NOT NULL CHECK(accion IN ('demolicion', 'anulacion')),
            precio REAL NOT NULL CHECK(precio > 0),
            intervalo_m REAL NOT NULL CHECK(intervalo_m > 0),
            UNIQUE(red, accion)
        );
        INSERT INTO pozos_existentes_precios_new SELECT * FROM pozos_existentes_precios;
        DROP TABLE pozos_existentes_precios;
        ALTER TABLE pozos_existentes_precios_new RENAME TO pozos_existentes_precios;
    """)
