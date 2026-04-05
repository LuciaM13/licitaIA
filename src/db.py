"""Módulo de base de datos SQLite para precios EMASESA.

Gestiona el schema relacional, conexiones y operaciones CRUD.
Reemplaza la persistencia en JSON plano con integridad referencial.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "precios.db"

_TABLAS_PERMITIDAS = frozenset({
    "tuberias", "anchos_zanja", "espesores_arrinonado", "acerados",
    "espesores_calzada", "acometida_defecto", "acometidas",
    "defaults_ui", "excavacion", "bordillos", "calzadas",
    "pozos", "entibacion", "valvuleria", "config", "demolicion",
    "subbases", "desmontaje", "imbornales", "pozos_existentes_precios",
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

-- Anchos de zanja por diámetro
CREATE TABLE IF NOT EXISTS anchos_zanja (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    diametro_mm INTEGER NOT NULL,
    ancho_m     REAL NOT NULL,
    UNIQUE(red, diametro_mm)
);

-- Espesores de arriñonado por diámetro
CREATE TABLE IF NOT EXISTS espesores_arrinonado (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
    diametro_mm INTEGER NOT NULL,
    espesor_m   REAL NOT NULL,
    UNIQUE(red, diametro_mm)
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
    precio_tapa_material REAL NOT NULL DEFAULT 0.0
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
"""


def init_db(path: str | Path | None = None) -> None:
    """Crea todas las tablas si no existen y migra columnas nuevas. Idempotente."""
    with conectar(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        _migrar_columnas(conn)
        conn.commit()


def _migrar_columnas(conn: sqlite3.Connection) -> None:
    """Añade columnas nuevas a tablas existentes sin perder datos. Idempotente."""

    def _columnas_existentes(tabla: str) -> set[str]:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({tabla})")}

    migraciones = [
        # (tabla, columna, definición SQL)
        ("tuberias",   "factor_piezas",      "REAL NOT NULL DEFAULT 1.0"),
        ("tuberias",   "precio_material_m",  "REAL NOT NULL DEFAULT 0.0"),
        ("valvuleria", "factor_piezas",       "REAL NOT NULL DEFAULT 1.2"),
        ("valvuleria", "precio_material",     "REAL NOT NULL DEFAULT 0.0"),
        ("pozos",      "precio_tapa",         "REAL NOT NULL DEFAULT 0.0"),
        ("pozos",      "precio_tapa_material","REAL NOT NULL DEFAULT 0.0"),
        ("acometidas", "factor_piezas",       "REAL NOT NULL DEFAULT 1.0"),
    ]

    for tabla, columna, definicion in migraciones:
        cols = _columnas_existentes(tabla)
        if columna not in cols:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")

    # Poner factor_piezas = 1.2 en ABA acometidas existentes que tengan 1.0
    conn.execute(
        "UPDATE acometidas SET factor_piezas = 1.2 WHERE red = 'ABA' AND factor_piezas = 1.0"
    )

    # Poner factor_piezas según tipo en tuberías existentes
    _factores_defecto = {
        "FD": 1.2, "PE-100": 1.2, "PE-80": 1.2,
        "Gres": 1.35, "PVC": 1.2,
        "Hormigón": 1.0, "HA": 1.0,
        "HA+PE80": 1.4,
    }
    for tipo, factor in _factores_defecto.items():
        conn.execute(
            "UPDATE tuberias SET factor_piezas = ? WHERE tipo = ? AND factor_piezas = 1.0",
            (factor, tipo)
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


def cargar_todo(path: str | Path | None = None) -> dict:
    """Lee toda la BD y construye el dict compatible con la interfaz existente."""
    with conectar(path) as conn:
        precios = {}

        # Config escalares
        for row in conn.execute("SELECT clave, valor FROM config"):
            precios[row["clave"]] = row["valor"]

        # Tuberías (ABA/SAN) — incluye factor_piezas y precio_material_m
        precios.update(_cargar_por_red(
            conn, "tuberias",
            "label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m",
            "catalogo", order_by="diametro_mm"))
        # Anchos zanja y espesores arriñonado — se mantienen para backward compat
        # pero el cálculo ahora usa fórmulas del Excel (no estas tablas)
        precios.update(_cargar_por_red(conn, "anchos_zanja", "diametro_mm, ancho_m",
                                       "anchos_zanja"))
        precios.update(_cargar_por_red(conn, "espesores_arrinonado", "diametro_mm, espesor_m",
                                       "espesores_arrinonado"))

        # Valvulería (incluye factor_piezas, precio_material y instalacion nullable)
        precios["catalogo_valvuleria"] = _rows_to_dicts(
            conn.execute("SELECT label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material FROM valvuleria ORDER BY dn_min"))

        # Entibación (incluye columna red, nullable)
        precios["catalogo_entibacion"] = _rows_to_dicts(
            conn.execute("SELECT label, precio_m2, umbral_m, red FROM entibacion"))

        # Pozos (con columnas opcionales para precios graduados y tapa)
        precios["catalogo_pozos"] = _rows_to_dicts(
            conn.execute("SELECT label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material FROM pozos"))

        # Demolición (ABA/SAN)
        precios.update(_cargar_por_red(conn, "demolicion", "label, unidad, precio",
                                       "demolicion"))

        # Acerados
        precios.update(_cargar_por_red(conn, "acerados", "label, unidad, precio",
                                       "acerados"))

        # Bordillos
        precios["bordillos_reposicion"] = _rows_to_dicts(
            conn.execute("SELECT label, unidad, precio FROM bordillos ORDER BY label"))

        # Calzadas
        precios["calzadas_reposicion"] = _rows_to_dicts(
            conn.execute("SELECT label, unidad, precio FROM calzadas ORDER BY label"))

        # Espesores calzada (dict, no lista) — JOIN para obtener label
        precios["espesores_calzada"] = {
            row["label"]: row["espesor_m"]
            for row in conn.execute(
                "SELECT c.label, e.espesor_m "
                "FROM espesores_calzada e "
                "JOIN calzadas c ON e.calzada_id = c.id")
        }

        # Sub-bases pavimentacion
        precios["catalogo_subbases"] = _rows_to_dicts(
            conn.execute("SELECT label, precio_m3 FROM subbases ORDER BY label"))

        # Excavación (dict)
        precios["excavacion"] = {
            row["clave"]: row["valor"]
            for row in conn.execute("SELECT clave, valor FROM excavacion")
        }

        # Acometidas (tipos→precio y tipos→factor_piezas separados)
        precios["acometidas_aba_tipos"] = {
            row["tipo"]: row["precio"]
            for row in conn.execute("SELECT tipo, precio FROM acometidas WHERE red='ABA' ORDER BY tipo")
        }
        precios["acometidas_san_tipos"] = {
            row["tipo"]: row["precio"]
            for row in conn.execute("SELECT tipo, precio FROM acometidas WHERE red='SAN' ORDER BY tipo")
        }
        precios["acometidas_aba_factores"] = {
            row["tipo"]: row["factor_piezas"]
            for row in conn.execute("SELECT tipo, factor_piezas FROM acometidas WHERE red='ABA' ORDER BY tipo")
        }
        precios["acometidas_san_factores"] = {
            row["tipo"]: row["factor_piezas"]
            for row in conn.execute("SELECT tipo, factor_piezas FROM acometidas WHERE red='SAN' ORDER BY tipo")
        }

        # Acometida por defecto
        for row in conn.execute("SELECT red, tipo FROM acometida_defecto"):
            if row["red"] == "ABA":
                precios["acometida_aba_defecto"] = row["tipo"]
            else:
                precios["acometida_san_defecto"] = row["tipo"]

        # Defaults UI
        precios["defaults_ui"] = {
            row["clave"]: row["valor"]
            for row in conn.execute("SELECT clave, valor FROM defaults_ui")
        }

        # Desmontaje tubería ABA
        precios["catalogo_desmontaje"] = _rows_to_dicts(
            conn.execute("SELECT label, dn_max, precio_m, es_fibrocemento FROM desmontaje ORDER BY dn_max"))

        # Imbornales SAN
        precios["catalogo_imbornales"] = _rows_to_dicts(
            conn.execute("SELECT label, precio, tipo FROM imbornales ORDER BY tipo, label"))

        # Pozos existentes precios
        precios["catalogo_pozos_existentes"] = _rows_to_dicts(
            conn.execute("SELECT red, accion, precio, intervalo_m FROM pozos_existentes_precios ORDER BY red, accion"))

        return precios


# ---------------------------------------------------------------------------
# Escritura completa (reemplaza todo el contenido)
# ---------------------------------------------------------------------------

def guardar_todo(precios: dict, path: str | Path | None = None) -> None:
    """Escribe el dict completo a la BD dentro de una transacción atómica.

    Con autocommit=False (PEP 249), commit() y rollback() funcionan
    correctamente. El orden de DELETE (dependientes primero) e INSERT
    (padres primero) respeta la única FK: espesores_calzada → calzadas.
    """
    with conectar(path) as conn:
        try:
            # Limpiar todas las tablas (orden respeta FK: dependientes primero)
            for tabla in [
                "espesores_calzada", "acometida_defecto", "acometidas",
                "defaults_ui", "excavacion", "demolicion", "bordillos", "calzadas",
                "acerados", "pozos", "entibacion", "valvuleria",
                "espesores_arrinonado", "anchos_zanja", "tuberias", "config",
                "subbases", "desmontaje", "imbornales", "pozos_existentes_precios",
            ]:
                if tabla not in _TABLAS_PERMITIDAS:
                    raise ValueError(f"Tabla no permitida: {tabla!r}")
                conn.execute(f"DELETE FROM {tabla}")

            # Config escalares
            for clave in ("pct_gg", "pct_bi", "pct_iva", "factor_esponjamiento",
                          "pct_manual_defecto", "conduccion_provisional_precio_m",
                          "pct_ci"):
                val = precios.get(clave)
                if val is None:
                    raise ValueError(
                        f"Falta el valor de configuración '{clave}'. "
                        "Revisa la sección Financiero y generales en Administración de precios."
                    )
                conn.execute("INSERT INTO config (clave, valor) VALUES (?, ?)",
                             (clave, float(val)))

            # Tuberías (con factor_piezas y precio_material_m)
            for red, clave in [("ABA", "catalogo_aba"), ("SAN", "catalogo_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO tuberias (red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m) VALUES (?,?,?,?,?,?,?)",
                        (red, item["label"], item["tipo"], int(item["diametro_mm"]), float(item["precio_m"]),
                         float(item.get("factor_piezas", 1.0)),
                         float(item.get("precio_material_m", 0.0))))

            # Anchos zanja
            for red, clave in [("ABA", "anchos_zanja_aba"), ("SAN", "anchos_zanja_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO anchos_zanja (red, diametro_mm, ancho_m) VALUES (?,?,?)",
                        (red, int(item["diametro_mm"]), float(item["ancho_m"])))

            # Espesores arriñonado
            for red, clave in [("ABA", "espesores_arrinonado_aba"), ("SAN", "espesores_arrinonado_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO espesores_arrinonado (red, diametro_mm, espesor_m) VALUES (?,?,?)",
                        (red, int(item["diametro_mm"]), float(item["espesor_m"])))

            # Valvulería (con factor_piezas, precio_material e instalacion nullable)
            for item in precios["catalogo_valvuleria"]:
                inst = item.get("instalacion")
                conn.execute(
                    "INSERT INTO valvuleria (label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material) VALUES (?,?,?,?,?,?,?,?,?)",
                    (item["label"], item["tipo"], int(item["dn_min"]), int(item["dn_max"]),
                     float(item["precio"]), float(item["intervalo_m"]), inst,
                     float(item.get("factor_piezas", 1.2)),
                     float(item.get("precio_material", 0.0))))

            # Entibación (con columna red nullable)
            for item in precios["catalogo_entibacion"]:
                red = item.get("red")
                conn.execute(
                    "INSERT INTO entibacion (label, precio_m2, umbral_m, red) VALUES (?,?,?,?)",
                    (item["label"], float(item["precio_m2"]), float(item["umbral_m"]), red))

            # Pozos (con columnas opcionales + precio_tapa)
            for item in precios["catalogo_pozos"]:
                prof_max = item.get("profundidad_max")
                dn_max = item.get("dn_max")
                conn.execute(
                    "INSERT INTO pozos (label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material) VALUES (?,?,?,?,?,?,?,?)",
                    (item["label"], float(item["precio"]),
                     float(item["intervalo"]),
                     item.get("red"),
                     float(prof_max) if prof_max is not None else None,
                     int(dn_max) if dn_max is not None else None,
                     float(item.get("precio_tapa", 0.0) or 0.0),
                     float(item.get("precio_tapa_material", 0.0) or 0.0)))

            # Demolición
            for red, clave in [("ABA", "demolicion_aba"), ("SAN", "demolicion_san")]:
                for item in precios.get(clave, []):
                    conn.execute(
                        "INSERT INTO demolicion (red, label, unidad, precio) VALUES (?,?,?,?)",
                        (red, item["label"], item["unidad"], float(item["precio"])))

            # Acerados
            for red, clave in [("ABA", "acerados_aba"), ("SAN", "acerados_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO acerados (red, label, unidad, precio) VALUES (?,?,?,?)",
                        (red, item["label"], item["unidad"], float(item["precio"])))

            # Bordillos
            for item in precios["bordillos_reposicion"]:
                conn.execute(
                    "INSERT INTO bordillos (label, unidad, precio) VALUES (?,?,?)",
                    (item["label"], item["unidad"], float(item["precio"])))

            # Calzadas
            for item in precios["calzadas_reposicion"]:
                conn.execute(
                    "INSERT INTO calzadas (label, unidad, precio) VALUES (?,?,?)",
                    (item["label"], item["unidad"], float(item["precio"])))

            # Espesores calzada — lookup calzada ID por label
            calzada_ids = {
                row["label"]: row["id"]
                for row in conn.execute("SELECT id, label FROM calzadas")
            }
            for label, espesor in precios["espesores_calzada"].items():
                calzada_id = calzada_ids.get(label)
                if calzada_id is None:
                    raise ValueError(
                        f"Espesor definido para calzada '{label}' pero esa calzada "
                        "no existe en 'calzadas_reposicion'.")
                conn.execute(
                    "INSERT INTO espesores_calzada (calzada_id, espesor_m) VALUES (?,?)",
                    (calzada_id, float(espesor)))

            # Excavación
            for clave, valor in precios["excavacion"].items():
                conn.execute(
                    "INSERT INTO excavacion (clave, valor) VALUES (?,?)",
                    (clave, float(valor)))

            # Acometidas (con factor_piezas)
            for red, clave_tipo, clave_factor in [
                ("ABA", "acometidas_aba_tipos", "acometidas_aba_factores"),
                ("SAN", "acometidas_san_tipos", "acometidas_san_factores"),
            ]:
                factores = precios.get(clave_factor, {})
                for tipo, precio in precios[clave_tipo].items():
                    factor = float(factores.get(tipo, 1.2 if red == "ABA" else 1.0))
                    conn.execute(
                        "INSERT INTO acometidas (red, tipo, precio, factor_piezas) VALUES (?,?,?,?)",
                        (red, tipo, float(precio), factor))

            # Acometida por defecto
            for red, clave in [("ABA", "acometida_aba_defecto"), ("SAN", "acometida_san_defecto")]:
                conn.execute(
                    "INSERT INTO acometida_defecto (red, tipo) VALUES (?,?)",
                    (red, precios[clave]))

            # Defaults UI
            for clave, valor in precios["defaults_ui"].items():
                conn.execute(
                    "INSERT INTO defaults_ui (clave, valor) VALUES (?,?)",
                    (clave, float(valor)))

            # Sub-bases
            for item in precios.get("catalogo_subbases", []):
                conn.execute(
                    "INSERT INTO subbases (label, precio_m3) VALUES (?,?)",
                    (item["label"], float(item["precio_m3"])))

            # Desmontaje
            for item in precios.get("catalogo_desmontaje", []):
                conn.execute(
                    "INSERT INTO desmontaje (label, dn_max, precio_m, es_fibrocemento) VALUES (?,?,?,?)",
                    (item["label"], int(item["dn_max"]), float(item["precio_m"]),
                     int(item.get("es_fibrocemento", 0) or 0)))

            # Imbornales
            for item in precios.get("catalogo_imbornales", []):
                conn.execute(
                    "INSERT INTO imbornales (label, precio, tipo) VALUES (?,?,?)",
                    (item["label"], float(item["precio"]), item["tipo"]))

            # Pozos existentes
            for item in precios.get("catalogo_pozos_existentes", []):
                conn.execute(
                    "INSERT INTO pozos_existentes_precios (red, accion, precio, intervalo_m) VALUES (?,?,?,?)",
                    (item["red"], item["accion"], float(item["precio"]),
                     float(item.get("intervalo_m", 100))))

            conn.commit()

        except Exception:
            conn.rollback()
            raise
