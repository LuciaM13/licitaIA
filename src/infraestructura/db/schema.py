"""Definición DDL del schema inicial de la BD.

``_SCHEMA`` contiene los ``CREATE TABLE IF NOT EXISTS`` que ejecuta
``init_db`` una vez antes de aplicar las migraciones versionadas.

Cualquier cambio de schema post-arranque debe modelarse como una migración
nueva en ``src.infraestructura.db.migrations``, no editando este fichero,
para preservar la idempotencia de las BDs existentes.
"""

from __future__ import annotations


_SCHEMA = """
-- Configuración global (escalares: pct_gg, pct_bi, pct_iva, pct_ci, etc.)
CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);

-- Tuberías (ABA y SAN unificadas)
-- Nota: precios en INTEGER céntimos desde Migración 13 (2 decimales exactos).
CREATE TABLE IF NOT EXISTS tuberias (
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

-- Valvulería ABA (instalacion nullable: NULL = sin distinción, 'enterrada'/'pozo')
CREATE TABLE IF NOT EXISTS valvuleria (
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

-- Entibación (red nullable: NULL = ambas redes)
CREATE TABLE IF NOT EXISTS entibacion (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label     TEXT NOT NULL UNIQUE,
    precio_m2 INTEGER NOT NULL CHECK(precio_m2 > 0),
    umbral_m  REAL NOT NULL CHECK(umbral_m > 0),
    red       TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN'))
);

-- Pozos de registro (con soporte para precios graduados SAN por profundidad/DN)
CREATE TABLE IF NOT EXISTS pozos (
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
    -- precio_pate_material: coste de suministro de un pate (escalón de pozo).
    -- Aplica solo a SAN. La cantidad de pates por pozo depende de la profundidad:
    --   P < 2.5 m → 6 pates/pozo
    --   2.5 ≤ P < 3.5 m → 9 pates/pozo
    --   P ≥ 3.5 m → 12 pates/pozo
    -- Fórmula del Excel: H45 = H29 * IF(D19<2.5,6,IF(D19<3.5,9,12))
    -- Precio base EMASESA (S-BASE PRECIOS D188): 1.94 €/ud
);

-- Acerados (ABA y SAN unificados)
CREATE TABLE IF NOT EXISTS acerados (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red    TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    label  TEXT NOT NULL,
    unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
    precio INTEGER NOT NULL CHECK(precio > 0),
    factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
    UNIQUE(red, label)
);

-- Bordillos
CREATE TABLE IF NOT EXISTS bordillos (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label  TEXT NOT NULL UNIQUE,
    unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'ud')),
    precio INTEGER NOT NULL CHECK(precio > 0),
    factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
);

-- Calzadas
CREATE TABLE IF NOT EXISTS calzadas (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label  TEXT NOT NULL UNIQUE,
    unidad TEXT NOT NULL CHECK(unidad IN ('m2', 'm3')),
    precio INTEGER NOT NULL CHECK(precio > 0),
    factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
);

-- Espesores de calzada (vinculado a calzadas por ID)
CREATE TABLE IF NOT EXISTS espesores_calzada (
    calzada_id INTEGER PRIMARY KEY REFERENCES calzadas(id)
               ON DELETE CASCADE,
    espesor_m  REAL NOT NULL
);

-- Demolición de pavimento (precios por red y material).
-- La clave semántica es (red, unidad, material): granítico/hidráulico para
-- bordillo; adoquín/aglomerado/hormigón para calzada; losa_hidraulica/
-- losa_terrazo/hormigon_acerado para acerado. Fila 'generico' legacy para
-- compatibilidad con presupuestos antiguos.
CREATE TABLE IF NOT EXISTS demolicion (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    label TEXT NOT NULL,
    unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
    material TEXT NOT NULL DEFAULT 'generico',
    precio INTEGER NOT NULL CHECK(precio > 0),
    factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
    UNIQUE(red, unidad, material)
);

-- Precios de excavación (escalares mezclados; REAL para preservar umbrales)
CREATE TABLE IF NOT EXISTS excavacion (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);

-- Tipos de acometida (ABA y SAN unificados)
CREATE TABLE IF NOT EXISTS acometidas (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    tipo  TEXT NOT NULL,
    precio INTEGER NOT NULL CHECK(precio > 0),
    factor_piezas REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
    UNIQUE(red, tipo)
);

-- Acometida por defecto (una fila por red)
CREATE TABLE IF NOT EXISTS acometida_defecto (
    red  TEXT PRIMARY KEY CHECK(red IN ('ABA', 'SAN')),
    tipo TEXT NOT NULL
);

-- Valores por defecto de la UI
CREATE TABLE IF NOT EXISTS defaults_ui (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);

-- Sub-bases de pavimentacion (capas bajo acerado/calzada)
CREATE TABLE IF NOT EXISTS subbases (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    precio_m3 INTEGER NOT NULL CHECK(precio_m3 > 0)
);

-- Desmontaje de tubería existente (ABA)
CREATE TABLE IF NOT EXISTS desmontaje (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label    TEXT NOT NULL UNIQUE,
    dn_max   INTEGER NOT NULL CHECK(dn_max > 0),   -- DN máximo para aplicar este precio
    precio_m INTEGER NOT NULL CHECK(precio_m > 0),  -- céntimos/m lineal (precio base, sin CI)
    es_fibrocemento INTEGER NOT NULL DEFAULT 0 CHECK(es_fibrocemento IN (0, 1))
);

-- Imbornales (SAN)
CREATE TABLE IF NOT EXISTS imbornales (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    precio INTEGER NOT NULL CHECK(precio > 0),   -- céntimos/ud (precio base, sin CI)
    tipo  TEXT NOT NULL CHECK(tipo IN ('adaptacion', 'nuevo'))
);

-- Audit log de cambios en tablas de precios (M14).
-- Se escribe desde guardar_todo() con diff snapshot antes↔después. Cada cambio
-- lógico genera una fila (no una por row afectada del DELETE+INSERT).
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    categoria   TEXT NOT NULL,      -- e.g. "catalogo_aba", "excavacion", "imbornales"
    clave       TEXT NOT NULL,      -- identificador del ítem dentro de la categoría
    operacion   TEXT NOT NULL CHECK(operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    antes_json  TEXT,                -- NULL en INSERT
    despues_json TEXT,               -- NULL en DELETE
    actor       TEXT NOT NULL DEFAULT 'desconocido'
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_categoria ON audit_log(categoria);

-- Precios de demolición/anulación de pozos existentes
CREATE TABLE IF NOT EXISTS pozos_existentes_precios (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red  TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    accion TEXT NOT NULL CHECK(accion IN ('demolicion', 'anulacion')),
    precio INTEGER NOT NULL CHECK(precio > 0),   -- céntimos/ud (precio base, sin CI)
    intervalo_m REAL NOT NULL DEFAULT 100.0 CHECK(intervalo_m > 0),
    UNIQUE(red, accion)
);

-- =========================================================================
-- HISTORIAL DE PRESUPUESTOS GENERADOS
-- =========================================================================

-- Tabla principal: un registro por presupuesto generado
CREATE TABLE IF NOT EXISTS presupuestos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    creado_en   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    descripcion TEXT NOT NULL DEFAULT '',
    -- Totales financieros
    pem         REAL NOT NULL,
    gg          REAL NOT NULL,
    bi          REAL NOT NULL,
    pbl_sin_iva REAL NOT NULL,
    iva         REAL NOT NULL,
    total       REAL NOT NULL,
    -- Porcentajes usados
    pct_gg      REAL NOT NULL,
    pct_bi      REAL NOT NULL,
    pct_iva     REAL NOT NULL,
    pct_ci      REAL NOT NULL DEFAULT 1.0
);

-- Desglose por capítulo
CREATE TABLE IF NOT EXISTS presupuesto_capitulos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    capitulo        TEXT NOT NULL,      -- ej: "01 OBRA CIVIL ABASTECIMIENTO"
    subtotal        REAL NOT NULL,
    orden           INTEGER NOT NULL    -- para mantener el orden de capítulos
);

-- Partidas (líneas detalladas dentro de cada capítulo)
CREATE TABLE IF NOT EXISTS presupuesto_partidas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    capitulo_id INTEGER NOT NULL REFERENCES presupuesto_capitulos(id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    importe     REAL NOT NULL
);

-- Parámetros de entrada del usuario
CREATE TABLE IF NOT EXISTS presupuesto_parametros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    clave           TEXT NOT NULL,      -- ej: "aba_longitud_m", "san_tuberia"
    valor           TEXT NOT NULL       -- siempre TEXT para flexibilidad (números se parsean)
);

-- Trazabilidad: decisiones del sistema experto en lenguaje natural
CREATE TABLE IF NOT EXISTS presupuesto_trazabilidad (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    red             TEXT NOT NULL,       -- "ABA" o "SAN"
    orden           INTEGER NOT NULL,    -- 0=Entibación, 1=Pozo, 2=Valvulería, 3=Desmontaje
    explicacion     TEXT NOT NULL        -- frase en castellano
);
"""
