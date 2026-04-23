"""M13: precios a INTEGER céntimos (2 decimales exactos, sin error de float).

Motivación: REAL (float64) acumula error de redondeo (M9 tuvo que corregir
un residual de 0.13 % por esto). INTEGER céntimos elimina el problema: 2
decimales exactos, sin error de punto flotante.

Convención post-M13:
  - BD almacena precios como INTEGER céntimos (12.96 € → 1296).
  - ``cargar_todo()`` divide por 100 al leer → dict Python en floats €.
  - ``guardar_todo()`` multiplica por 100 con round() al guardar.
  - ``_aplicar_ci`` opera sobre floats €, sin cambios.

Tablas REAL afectadas (todas sus columnas de precio → INTEGER):
  tuberias, valvuleria, pozos, acerados, bordillos, calzadas, demolicion,
  entibacion, acometidas, subbases, desmontaje, imbornales,
  pozos_existentes_precios.

Excluidas (contienen factores/dimensiones, no solo precios):
  excavacion.valor, config.valor, defaults_ui.valor → siguen REAL.

Esta migración es el segundo "mini-proyecto" dentro del runner (junto a
M12). Cada ``executescript`` recrea UNA tabla convirtiendo REAL→INTEGER con
``CAST(ROUND(precio * 100) AS INTEGER)``.
"""

from __future__ import annotations

import sqlite3

VERSION = 13
DESCRIPCION = "Precios a INTEGER céntimos (2 decimales exactos, sin error de float)"


def aplicar(conn: sqlite3.Connection) -> None:
    # tuberias
    conn.executescript("""
        CREATE TABLE tuberias_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            label TEXT NOT NULL,
            tipo  TEXT NOT NULL,
            diametro_mm  INTEGER NOT NULL CHECK(diametro_mm > 0),
            precio_m     INTEGER NOT NULL CHECK(precio_m > 0),
            factor_piezas     REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
            precio_material_m INTEGER NOT NULL DEFAULT 0 CHECK(precio_material_m >= 0),
            UNIQUE(red, label)
        );
        INSERT INTO tuberias_new (id, red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m)
            SELECT id, red, label, tipo, diametro_mm,
                   CAST(ROUND(precio_m * 100) AS INTEGER),
                   factor_piezas,
                   CAST(ROUND(precio_material_m * 100) AS INTEGER)
            FROM tuberias;
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
            precio        INTEGER NOT NULL CHECK(precio > 0),
            intervalo_m   REAL NOT NULL CHECK(intervalo_m > 0),
            instalacion   TEXT CHECK(instalacion IS NULL OR instalacion IN ('enterrada', 'pozo')),
            factor_piezas  REAL NOT NULL DEFAULT 1.2 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
            precio_material INTEGER NOT NULL DEFAULT 0 CHECK(precio_material >= 0)
        );
        INSERT INTO valvuleria_new (id, label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material)
            SELECT id, label, tipo, dn_min, dn_max,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   intervalo_m, instalacion, factor_piezas,
                   CAST(ROUND(precio_material * 100) AS INTEGER)
            FROM valvuleria;
        DROP TABLE valvuleria;
        ALTER TABLE valvuleria_new RENAME TO valvuleria;
    """)
    # pozos (4 columnas de precio)
    conn.executescript("""
        CREATE TABLE pozos_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label            TEXT NOT NULL,
            precio           INTEGER NOT NULL CHECK(precio > 0),
            intervalo        REAL NOT NULL CHECK(intervalo > 0),
            red              TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN')),
            profundidad_max  REAL CHECK(profundidad_max IS NULL OR profundidad_max > 0),
            dn_max           INTEGER CHECK(dn_max IS NULL OR dn_max > 0),
            precio_tapa      INTEGER NOT NULL DEFAULT 0 CHECK(precio_tapa >= 0),
            precio_tapa_material INTEGER NOT NULL DEFAULT 0 CHECK(precio_tapa_material >= 0),
            precio_pate_material INTEGER NOT NULL DEFAULT 0 CHECK(precio_pate_material >= 0)
        );
        INSERT INTO pozos_new (id, label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material, precio_pate_material)
            SELECT id, label,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   intervalo, red, profundidad_max, dn_max,
                   CAST(ROUND(precio_tapa * 100) AS INTEGER),
                   CAST(ROUND(precio_tapa_material * 100) AS INTEGER),
                   CAST(ROUND(precio_pate_material * 100) AS INTEGER)
            FROM pozos;
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
            precio INTEGER NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
            UNIQUE(red, label)
        );
        INSERT INTO acerados_new (id, red, label, unidad, precio, factor_ci)
            SELECT id, red, label, unidad,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   factor_ci
            FROM acerados;
        DROP TABLE acerados;
        ALTER TABLE acerados_new RENAME TO acerados;
    """)
    # bordillos
    conn.executescript("""
        CREATE TABLE bordillos_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label  TEXT NOT NULL UNIQUE,
            unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'ud')),
            precio INTEGER NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
        );
        INSERT INTO bordillos_new (id, label, unidad, precio, factor_ci)
            SELECT id, label, unidad,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   factor_ci
            FROM bordillos;
        DROP TABLE bordillos;
        ALTER TABLE bordillos_new RENAME TO bordillos;
    """)
    # calzadas (preservar espesores_calzada)
    conn.executescript("""
        CREATE TEMP TABLE _espesores_backup_m13 AS SELECT * FROM espesores_calzada;

        PRAGMA foreign_keys = OFF;

        CREATE TABLE calzadas_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label  TEXT NOT NULL UNIQUE,
            unidad TEXT NOT NULL CHECK(unidad IN ('m2', 'm3')),
            precio INTEGER NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
        );
        INSERT INTO calzadas_new (id, label, unidad, precio, factor_ci)
            SELECT id, label, unidad,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   factor_ci
            FROM calzadas;
        DROP TABLE calzadas;
        ALTER TABLE calzadas_new RENAME TO calzadas;

        DELETE FROM espesores_calzada;
        INSERT INTO espesores_calzada (calzada_id, espesor_m)
            SELECT calzada_id, espesor_m FROM _espesores_backup_m13;

        DROP TABLE _espesores_backup_m13;

        PRAGMA foreign_keys = ON;
    """)
    # demolicion
    conn.executescript("""
        CREATE TABLE demolicion_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            label TEXT NOT NULL,
            unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
            precio INTEGER NOT NULL CHECK(precio > 0),
            factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
            UNIQUE(red, label)
        );
        INSERT INTO demolicion_new (id, red, label, unidad, precio, factor_ci)
            SELECT id, red, label, unidad,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   factor_ci
            FROM demolicion;
        DROP TABLE demolicion;
        ALTER TABLE demolicion_new RENAME TO demolicion;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_demolicion_red_unidad
            ON demolicion(red, unidad);
    """)
    # entibacion
    conn.executescript("""
        CREATE TABLE entibacion_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label     TEXT NOT NULL UNIQUE,
            precio_m2 INTEGER NOT NULL CHECK(precio_m2 > 0),
            umbral_m  REAL NOT NULL CHECK(umbral_m > 0),
            red       TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN'))
        );
        INSERT INTO entibacion_new (id, label, precio_m2, umbral_m, red)
            SELECT id, label,
                   CAST(ROUND(precio_m2 * 100) AS INTEGER),
                   umbral_m, red
            FROM entibacion;
        DROP TABLE entibacion;
        ALTER TABLE entibacion_new RENAME TO entibacion;
    """)
    # acometidas
    conn.executescript("""
        CREATE TABLE acometidas_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            tipo  TEXT NOT NULL,
            precio INTEGER NOT NULL CHECK(precio > 0),
            factor_piezas REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
            UNIQUE(red, tipo)
        );
        INSERT INTO acometidas_new (id, red, tipo, precio, factor_piezas)
            SELECT id, red, tipo,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   factor_piezas
            FROM acometidas;
        DROP TABLE acometidas;
        ALTER TABLE acometidas_new RENAME TO acometidas;
    """)
    # subbases
    conn.executescript("""
        CREATE TABLE subbases_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            precio_m3 INTEGER NOT NULL CHECK(precio_m3 > 0)
        );
        INSERT INTO subbases_new (id, label, precio_m3)
            SELECT id, label, CAST(ROUND(precio_m3 * 100) AS INTEGER)
            FROM subbases;
        DROP TABLE subbases;
        ALTER TABLE subbases_new RENAME TO subbases;
    """)
    # desmontaje
    conn.executescript("""
        CREATE TABLE desmontaje_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label    TEXT NOT NULL UNIQUE,
            dn_max   INTEGER NOT NULL CHECK(dn_max > 0),
            precio_m INTEGER NOT NULL CHECK(precio_m > 0),
            es_fibrocemento INTEGER NOT NULL DEFAULT 0 CHECK(es_fibrocemento IN (0, 1))
        );
        INSERT INTO desmontaje_new (id, label, dn_max, precio_m, es_fibrocemento)
            SELECT id, label, dn_max,
                   CAST(ROUND(precio_m * 100) AS INTEGER),
                   es_fibrocemento
            FROM desmontaje;
        DROP TABLE desmontaje;
        ALTER TABLE desmontaje_new RENAME TO desmontaje;
    """)
    # imbornales
    conn.executescript("""
        CREATE TABLE imbornales_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            precio INTEGER NOT NULL CHECK(precio > 0),
            tipo  TEXT NOT NULL CHECK(tipo IN ('adaptacion', 'nuevo'))
        );
        INSERT INTO imbornales_new (id, label, precio, tipo)
            SELECT id, label, CAST(ROUND(precio * 100) AS INTEGER), tipo
            FROM imbornales;
        DROP TABLE imbornales;
        ALTER TABLE imbornales_new RENAME TO imbornales;
    """)
    # pozos_existentes_precios
    conn.executescript("""
        CREATE TABLE pozos_existentes_precios_new (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
            accion TEXT NOT NULL CHECK(accion IN ('demolicion', 'anulacion')),
            precio INTEGER NOT NULL CHECK(precio > 0),
            intervalo_m REAL NOT NULL CHECK(intervalo_m > 0),
            UNIQUE(red, accion)
        );
        INSERT INTO pozos_existentes_precios_new (id, red, accion, precio, intervalo_m)
            SELECT id, red, accion,
                   CAST(ROUND(precio * 100) AS INTEGER),
                   intervalo_m
            FROM pozos_existentes_precios;
        DROP TABLE pozos_existentes_precios;
        ALTER TABLE pozos_existentes_precios_new RENAME TO pozos_existentes_precios;
    """)
