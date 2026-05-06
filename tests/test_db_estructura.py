"""Tests estructurales del paquete ``src.almacenamiento``.

Verifica que:
  - El paquete expone su API pública (``conectar``, ``init_db``,
    ``DB_PATH``, ``_TABLAS_PERMITIDAS``, ``_rows_to_dicts``,
    ``_cargar_por_red``).
  - La whitelist ``_TABLAS_PERMITIDAS`` cubre las tablas de historial.
  - Tras ``init_db()`` el schema incluye las tablas críticas
    (incluida ``presupuesto_cadena_inferencia``).

Excepción a la regla "solo AppTest": valida invariantes estructurales
de la capa de infraestructura sin superficie Streamlit.
"""
from __future__ import annotations

import importlib

from src.almacenamiento import (
    DB_PATH,
    _TABLAS_PERMITIDAS,
    conectar,
    init_db,
    _rows_to_dicts,
    _cargar_por_red,
)


# ---------------------------------------------------------------------------
# API pública preservada
# ---------------------------------------------------------------------------

def test_api_publica_preservada():
    """Los 6 nombres públicos siguen siendo accesibles desde el paquete."""
    assert callable(conectar)
    assert callable(init_db)
    assert callable(_rows_to_dicts)
    assert callable(_cargar_por_red)
    assert isinstance(_TABLAS_PERMITIDAS, frozenset)
    assert DB_PATH.name == "precios.db"


def test_tablas_permitidas_incluye_historial():
    """La whitelist debe incluir las tablas de historial (conservadas intactas)."""
    esperadas = {
        "tuberias", "acerados", "espesores_calzada",
        "presupuestos", "presupuesto_trazabilidad",
    }
    assert esperadas.issubset(_TABLAS_PERMITIDAS)


# ---------------------------------------------------------------------------
# Tablas críticas presentes tras init_db
# ---------------------------------------------------------------------------

def test_schema_incluye_cadena_inferencia():
    """La tabla presupuesto_cadena_inferencia (provenance del SE CLIPS)
    debe existir tras init_db(). Cubre regresión del gap reconciliado
    cuando se squashearon las 19 migraciones a _SCHEMA único."""
    with conectar() as conn:
        fila = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='presupuesto_cadena_inferencia'"
        ).fetchone()
    assert fila is not None, (
        "Tabla presupuesto_cadena_inferencia ausente — "
        "verificar que _SCHEMA en src/almacenamiento/schema.py la incluye."
    )


# ---------------------------------------------------------------------------
# Import del paquete vs módulo antiguo
# ---------------------------------------------------------------------------

def test_infraestructura_db_es_paquete_no_modulo():
    """Confirmación defensiva: ``src.almacenamiento`` debe ser paquete."""
    mod = importlib.import_module("src.almacenamiento")
    assert hasattr(mod, "__path__"), (
        "src.almacenamiento debe ser un paquete (directorio con __init__.py), "
        "no un módulo .py monolítico."
    )
