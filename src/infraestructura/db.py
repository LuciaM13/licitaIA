"""Módulo de base de datos SQLite para precios EMASESA.

Gestiona el schema relacional, conexiones y operaciones CRUD.
Reemplaza la persistencia en JSON plano con integridad referencial.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "precios.db"

_TABLAS_PERMITIDAS = frozenset({
    "tuberias", "acerados",
    "espesores_calzada", "acometida_defecto", "acometidas",
    "defaults_ui", "excavacion", "bordillos", "calzadas",
    "pozos", "entibacion", "valvuleria", "config", "demolicion",
    "subbases", "desmontaje", "imbornales", "pozos_existentes_precios",
    # Historial de presupuestos
    "presupuestos", "presupuesto_capitulos", "presupuesto_partidas",
    "presupuesto_parametros", "presupuesto_trazabilidad",
})

# ---------------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------------

@contextmanager
def conectar(path: str | Path | None = None):
    """Context manager que abre conexión con FK activadas y cierra al salir."""
    db = path or DB_PATH
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA = """
-- Configuración global (escalares)
CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);

-- Tuberías (ABA y SAN unificadas)
CREATE TABLE IF NOT EXISTS tuberias (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    label TEXT NOT NULL,
    tipo  TEXT NOT NULL,
    diametro_mm  INTEGER NOT NULL,
    precio_m     REAL NOT NULL,
    factor_piezas     REAL NOT NULL DEFAULT 1.0,
    precio_material_m REAL NOT NULL DEFAULT 0.0,
    UNIQUE(red, label)
);

-- Valvulería ABA (instalacion nullable: NULL = sin distinción, 'enterrada'/'pozo')
CREATE TABLE IF NOT EXISTS valvuleria (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    tipo  TEXT NOT NULL,
    dn_min        INTEGER NOT NULL,
    dn_max        INTEGER NOT NULL,
    precio        REAL NOT NULL,
    intervalo_m   REAL NOT NULL,
    instalacion   TEXT CHECK(instalacion IS NULL OR instalacion IN ('enterrada', 'pozo')),
    factor_piezas  REAL NOT NULL DEFAULT 1.2,
    precio_material REAL NOT NULL DEFAULT 0.0
);

-- Entibación (red nullable: NULL = ambas redes)
CREATE TABLE IF NOT EXISTS entibacion (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label     TEXT NOT NULL UNIQUE,
    precio_m2 REAL NOT NULL,
    umbral_m  REAL NOT NULL,
    red       TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN'))
);

-- Pozos de registro (con soporte para precios graduados SAN por profundidad/DN)
CREATE TABLE IF NOT EXISTS pozos (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label            TEXT NOT NULL,
    precio           REAL NOT NULL,
    intervalo        REAL NOT NULL,
    red              TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN')),
    profundidad_max  REAL,
    dn_max           INTEGER,
    precio_tapa      REAL NOT NULL DEFAULT 0.0,
    precio_tapa_material REAL NOT NULL DEFAULT 0.0,
    precio_pate_material REAL NOT NULL DEFAULT 0.0
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
    unidad TEXT NOT NULL,
    precio REAL NOT NULL,
    UNIQUE(red, label)
);

-- Bordillos
CREATE TABLE IF NOT EXISTS bordillos (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label  TEXT NOT NULL UNIQUE,
    unidad TEXT NOT NULL,
    precio REAL NOT NULL
);

-- Calzadas
CREATE TABLE IF NOT EXISTS calzadas (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label  TEXT NOT NULL UNIQUE,
    unidad TEXT NOT NULL,
    precio REAL NOT NULL
);

-- Espesores de calzada (vinculado a calzadas por ID)
CREATE TABLE IF NOT EXISTS espesores_calzada (
    calzada_id INTEGER PRIMARY KEY REFERENCES calzadas(id)
               ON DELETE CASCADE,
    espesor_m  REAL NOT NULL
);

-- Demolición de pavimento (precios por red)
CREATE TABLE IF NOT EXISTS demolicion (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    label TEXT NOT NULL,
    unidad TEXT NOT NULL,
    precio REAL NOT NULL,
    UNIQUE(red, label)
);

-- Precios de excavación
CREATE TABLE IF NOT EXISTS excavacion (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);

-- Tipos de acometida (ABA y SAN unificados)
CREATE TABLE IF NOT EXISTS acometidas (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    tipo  TEXT NOT NULL,
    precio REAL NOT NULL,
    factor_piezas REAL NOT NULL DEFAULT 1.0,
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
    precio_m3 REAL NOT NULL
);

-- Desmontaje de tubería existente (ABA)
CREATE TABLE IF NOT EXISTS desmontaje (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label    TEXT NOT NULL UNIQUE,
    dn_max   INTEGER NOT NULL,   -- DN máximo para aplicar este precio
    precio_m REAL NOT NULL,      -- €/m lineal (precio base, sin CI)
    es_fibrocemento INTEGER NOT NULL DEFAULT 0  -- 1 = fibrocemento, 0 = normal
);

-- Imbornales (SAN)
CREATE TABLE IF NOT EXISTS imbornales (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    precio REAL NOT NULL,        -- €/ud (precio base, sin CI)
    tipo  TEXT NOT NULL CHECK(tipo IN ('adaptacion', 'nuevo'))
);

-- Precios de demolición/anulación de pozos existentes
CREATE TABLE IF NOT EXISTS pozos_existentes_precios (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red  TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    accion TEXT NOT NULL CHECK(accion IN ('demolicion', 'anulacion')),
    precio REAL NOT NULL,    -- €/ud (precio base, sin CI)
    intervalo_m REAL NOT NULL DEFAULT 100.0
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


def init_db(path: str | Path | None = None) -> None:
    """Crea todas las tablas si no existen y ejecuta migraciones pendientes. Idempotente."""
    logger.info("init_db() - path=%s", path or DB_PATH)
    with conectar(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        # Tabla de tracking de migraciones (se crea aquí para no mezclarla con _SCHEMA)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "  version INTEGER PRIMARY KEY,"
            "  descripcion TEXT NOT NULL,"
            "  aplicada_en TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        _ejecutar_migraciones(conn)
        conn.commit()
    logger.info("init_db() OK")


def _version_actual(conn: sqlite3.Connection) -> int:
    """Devuelve la versión de schema más alta aplicada, o 0 si no hay ninguna."""
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def _registrar_version(conn: sqlite3.Connection, version: int, descripcion: str) -> None:
    """Marca una migración como aplicada."""
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, descripcion) VALUES (?, ?)",
        (version, descripcion),
    )


def _ejecutar_migraciones(conn: sqlite3.Connection) -> None:
    """Ejecuta solo las migraciones que aún no se han aplicado.

    Cada migración tiene un número de versión. Solo se ejecuta si ese número
    no está en schema_version. Esto evita que los UPDATEs de datos iniciales
    sobreescriban valores que el usuario haya editado manualmente.
    """

    version = _version_actual(conn)
    logger.debug("Versión actual del schema: %d", version)

    def _columnas_existentes(tabla: str) -> set[str]:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({tabla})")}

    # --- Migración 1: columnas nuevas + datos iniciales por defecto -----------
    if version < 1:
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

        # Datos iniciales (solo se ejecutan UNA VEZ en la vida de la BD)
        conn.execute(
            "UPDATE acometidas SET factor_piezas = 1.2 WHERE red = 'ABA' AND factor_piezas = 1.0"
        )
        conn.execute(
            "UPDATE pozos SET precio_tapa_material = 152.7333 "
            "WHERE red = 'SAN' AND precio_tapa_material = 0.0"
        )
        conn.execute(
            "UPDATE pozos SET precio_pate_material = 1.8476 "
            "WHERE red = 'SAN' AND precio_pate_material = 0.0"
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
        _registrar_version(conn, 1, "Columnas nuevas + datos iniciales por defecto")

    # --- Migración 2: correcciones de reglas CLIPS ----------------------------
    # H1: separar entibación blindada en ABA (umbral 1.5m) y SAN (umbral 1.4m)
    #     El Excel SAN usa D19>1.4 en la fórmula de precio (J17), no 1.5m.
    # H2: desmontaje DN<150mm tenía dn_max=149; el Excel usa >150 como frontera
    #     (DN=150 pertenece al rango <150mm), así que dn_max correcto es 150.
    if version < 2:
        # H1 - Paso 1: renombrar la entrada wildcard a ABA y asignarle red='ABA'
        conn.execute(
            "UPDATE entibacion SET label = 'Entibación blindada ABA', red = 'ABA' "
            "WHERE label = 'Entibación blindada' AND red IS NULL"
        )
        # H1 - Paso 2: insertar nueva entrada para SAN con umbral 1.4m
        # El precio base es el mismo (2.5.001 del Excel: 4.27 €/m², sin CI = 3.037096)
        conn.execute(
            "INSERT OR IGNORE INTO entibacion (label, precio_m2, umbral_m, red) "
            "VALUES ('Entibación blindada SAN', 3.037096, 1.4, 'SAN')"
        )
        # H2 - Corregir frontera desmontaje: dn_max 149 → 150
        conn.execute(
            "UPDATE desmontaje SET dn_max = 150 "
            "WHERE label = 'Desmontaje tubería DN<150mm' AND dn_max = 149"
        )
        _registrar_version(conn, 2, "Fix entibación SAN umbral 1.4m y desmontaje DN=150 frontera")

    # --- Migración 3: entibación SAN profunda (P ≥ 2.5 m) --------------------
    # El Excel SAN usa dos precios de entibación en J17:
    #   IF(D19>1.4, IF(D19<2.5, D49, D50), 0)
    #   D49 = 4.27 €/m² (ref 2.5.001, superficial) → base 3.037096 (ya existe)
    #   D50 = 22.73 €/m² (ref 2.5.065, profunda)   → base 16.167024
    # Faltaba el segundo registro. desempatar_entibacion() ya elige el
    # candidato con mayor umbral_m, así que basta con insertar el dato.
    if version < 3:
        conn.execute(
            "INSERT OR IGNORE INTO entibacion (label, precio_m2, umbral_m, red) "
            "VALUES ('Entibación blindada SAN profunda', 16.167024, 2.5, 'SAN')"
        )
        _registrar_version(conn, 3, "Añadir entibación SAN profunda P>=2.5m (22.73 €/m²)")

    # --- Migración 4: correcciones auditadas 2026-04-12 -----------------------
    # H1: precio base demolición acerado (ABA y SAN) era ~7.44, debería ser 14.0
    #     Excel S/A-BASE PRECIOS D9 = 14.70 €/m² → base sin CI = 14.70 / 1.05 = 14.0
    #     El precio anterior (7.438095) era ~la mitad del correcto, causando una
    #     infravaloración del ~50% en demolición de acerado.
    # H2: los pozos SAN con dn_max=2500 no cubren la tubería HA+PE80 Ø3000mm.
    #     Se extiende dn_max a 9999 para los tres tramos de profundidad (P<2.5,
    #     P<3.5, P<5) que actualmente llegan a dn_max=2500, usando el precio del
    #     tramo más próximo (DN≤2500) al no existir referencia Excel para DN=3000.
    if version < 4:
        # H1: corregir precio base demolición acerado
        conn.execute(
            "UPDATE demolicion SET precio = 14.0 "
            "WHERE label = 'Demolición acerado' AND ABS(precio - 7.438095) < 0.01"
        )
        # H2: extender cobertura pozos SAN de dn_max=2500 a dn_max=9999
        conn.execute(
            "UPDATE pozos SET dn_max = 9999 "
            "WHERE red = 'SAN' AND dn_max = 2500"
        )
        _registrar_version(
            conn, 4,
            "Fix dem acerado base 7.44→14.0; pozos SAN dn_max 2500→9999 para DN>=3000"
        )

    # --- Migración 5: correcciones auditadas 2026-04-12 (tercera pasada) ------
    # H1: "Entibación tipo paralelo" (red=SAN, umbral=2.5) es código muerto.
    #     La regla CLIPS usa >= desde esta misma sesión (antes usaba >), por lo
    #     que para P>=2.5 SAN ahora compiten:
    #       - "Entibación tipo paralelo"      umbral=2.5  precio=16.961476
    #       - "Entibación blindada SAN profunda" umbral=2.5  precio=16.167024
    #     El desempate elige el de MAYOR umbral, y en caso de empate el MENOR
    #     índice en el catálogo. "Tipo paralelo" siempre ganaba por tener id=37
    #     vs id=39, dejando el item de Migración 3 inaccesible.
    #     Adicionalmente, "tipo paralelo" tenía el precio un ~4.9% más alto que
    #     el item correcto (sobrevaloración equivalente a un doble CI).
    #     Fix: eliminar "Entibación tipo paralelo" para que "Entibación blindada
    #     SAN profunda" sea el único candidato en P>=2.5 SAN.
    # H2 (relacionado con H1): el cambio de > a >= en la regla CLIPS también
    #     corrige la frontera P=2.5 SAN: antes seleccionaba el precio superficial
    #     (~3.19 €/m²) cuando el Excel usa el profundo (~16.98 €/m²).
    if version < 5:
        conn.execute(
            "DELETE FROM entibacion WHERE label = 'Entibación tipo paralelo'"
        )
        _registrar_version(
            conn, 5,
            "Eliminar 'Entibación tipo paralelo' (dead code): profunda SAN ya "
            "cubierta por 'Entibación blindada SAN profunda'"
        )

    # --- Migración 7: deduplicar demolicion por (red, unidad) + unique index -----
    # El campo UNIQUE(red, label) no impedía dos filas con la misma (red, unidad)
    # si tenían labels distintos. demo_items() asume como máximo una fila por
    # unidad ('m2', 'm') y lanzaba ValueError en caso de duplicado.
    # Fix: conservar la fila con MAX(id) por (red, unidad) y añadir unique index.
    if version < 7:
        conn.execute(
            "DELETE FROM demolicion WHERE id NOT IN "
            "(SELECT MAX(id) FROM demolicion GROUP BY red, unidad)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_demolicion_red_unidad "
            "ON demolicion(red, unidad)"
        )
        _registrar_version(
            conn, 7,
            "Deduplicar demolicion (red, unidad) y añadir unique index"
        )

    # --- Migración 6: corregir precios base de entibación (auditoría 2026-04-13) --
    # Los precios de entibación se almacenaron con un factor de división erróneo
    # (~1.406 en lugar de 1.05 CI). Verificación contra el Excel EMASESA:
    #   A-BASE PRECIOS D45 = 4.27 €/m² (ref 2.5.001) → sin CI = 4.27/1.05 = 4.066667
    #   S-BASE PRECIOS D49 = 4.27 €/m² (ref 2.5.001) → sin CI = 4.27/1.05 = 4.066667
    #   S-BASE PRECIOS D50 = 22.73 €/m² (ref 2.5.065) → sin CI = 22.73/1.05 = 21.647619
    # Contraste: demolición (D9=14.70/1.05=14.0) y pates (D188=1.94/1.05=1.8476)
    # estaban correctos, confirmando que el CI correcto es 1.05.
    # Impacto: las tres entradas de entibación estaban infravaloradas un ~25%.
    if version < 6:
        conn.execute(
            "UPDATE entibacion SET precio_m2 = 4.066667 "
            "WHERE label = 'Entibación blindada ABA'"
        )
        conn.execute(
            "UPDATE entibacion SET precio_m2 = 4.066667 "
            "WHERE label = 'Entibación blindada SAN'"
        )
        conn.execute(
            "UPDATE entibacion SET precio_m2 = 21.647619 "
            "WHERE label = 'Entibación blindada SAN profunda'"
        )
        _registrar_version(
            conn, 6,
            "Fix precios entibación: base 3.037→4.067 (superf) y 16.167→21.648 "
            "(profunda). Los anteriores usaban factor ~1.406 en vez de CI=1.05"
        )


# ---------------------------------------------------------------------------
# Helpers de lectura
# ---------------------------------------------------------------------------

def _rows_to_dicts(cursor: sqlite3.Cursor, exclude: set[str] | None = None) -> list[dict]:
    """Convierte filas sqlite3.Row a lista de dicts, excluyendo columnas indicadas."""
    exclude = exclude or set()
    return [
        {k: row[k] for k in row.keys() if k not in exclude}
        for row in cursor.fetchall()
    ]


def _cargar_por_red(conn, tabla: str, columnas: str, clave_base: str,
                    order_by: str | None = None) -> dict:
    """Carga filas de una tabla con columna 'red' y devuelve dos listas keyed por ABA/SAN.

    SEGURIDAD: ``columnas`` y ``order_by`` se interpolan en SQL con f-string.
    Solo pasar literales definidos en este módulo, nunca input de usuario.
    """
    if tabla not in _TABLAS_PERMITIDAS:
        raise ValueError(f"Tabla no permitida: {tabla!r}")
    orden = order_by or columnas.split(",")[0].strip()
    resultado = {}
    for red in ("ABA", "SAN"):
        cursor = conn.execute(
            f"SELECT {columnas} FROM {tabla} WHERE red=? ORDER BY {orden}",
            (red,),
        )
        resultado[f"{clave_base}_{red.lower()}"] = _rows_to_dicts(cursor)
    return resultado


# ---------------------------------------------------------------------------
# Re-exports de submódulos (compatibilidad con imports existentes)
# ---------------------------------------------------------------------------

from src.infraestructura.db_precios import cargar_todo, guardar_todo  # noqa: F401,E402
from src.infraestructura.db_historial import (  # noqa: F401,E402
    guardar_presupuesto, listar_presupuestos, obtener_presupuesto,
    eliminar_presupuesto, contar_presupuestos,
)
