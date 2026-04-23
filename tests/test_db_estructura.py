"""Tests del paquete ``src.infraestructura.db`` tras el Paso 4 del refactor.

Verifica que:
  - El paquete ``db`` expone la misma API pública que el antiguo fichero
    monolítico (``conectar``, ``init_db``, ``DB_PATH``, ``_TABLAS_PERMITIDAS``).
  - Existen los 16 ficheros de migración y cada uno expone ``VERSION``,
    ``DESCRIPCION`` y ``aplicar``.
  - La lista ``MIGRACIONES`` del runner está completa y ordenada como en el
    runner histórico (con M7 antes que M6).
  - Tras ``init_db()``, la tabla ``schema_version`` contiene las 16 versiones.

Excepción a la regla "solo AppTest": valida invariantes estructurales de
la capa de infraestructura sin superficie Streamlit.
"""
from __future__ import annotations

import importlib
from pathlib import Path

from src.infraestructura.db import (
    DB_PATH,
    _TABLAS_PERMITIDAS,
    conectar,
    init_db,
    _rows_to_dicts,
    _cargar_por_red,
)
from src.infraestructura.db.migrations import MIGRACIONES


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
# Migraciones
# ---------------------------------------------------------------------------

def test_16_migraciones_registradas():
    assert len(MIGRACIONES) == 16


def test_cada_migracion_expone_contrato():
    """Cada módulo de migración expone VERSION, DESCRIPCION y aplicar()."""
    for mig in MIGRACIONES:
        assert hasattr(mig, "VERSION"), f"{mig.__name__} sin VERSION"
        assert hasattr(mig, "DESCRIPCION"), f"{mig.__name__} sin DESCRIPCION"
        assert hasattr(mig, "aplicar"), f"{mig.__name__} sin aplicar()"
        assert callable(mig.aplicar)
        assert isinstance(mig.VERSION, int)
        assert mig.VERSION >= 1


def test_orden_declarativo_preserva_m7_antes_m6():
    """El orden del runner histórico aplicaba M7 antes que M6. Preservarlo."""
    versiones = [m.VERSION for m in MIGRACIONES]
    idx_m6 = versiones.index(6)
    idx_m7 = versiones.index(7)
    assert idx_m7 < idx_m6, (
        f"M7 debe ir antes que M6 en MIGRACIONES (orden histórico del runner). "
        f"Obtenido: {versiones}"
    )


def test_todas_las_versiones_del_1_al_16_presentes():
    versiones = {m.VERSION for m in MIGRACIONES}
    assert versiones == set(range(1, 17))


# ---------------------------------------------------------------------------
# Ficheros físicos existen
# ---------------------------------------------------------------------------

def test_ficheros_de_migracion_existen():
    ruta_migraciones = (
        Path(__file__).resolve().parent.parent
        / "src" / "infraestructura" / "db" / "migrations"
    )
    esperados = {
        "m01_factor_piezas.py",
        "m02_entibacion_san.py",
        "m03_entibacion_san_profunda.py",
        "m04_demolicion_acerado_y_pozos_san.py",
        "m05_eliminar_entibacion_paralelo.py",
        "m06_fix_precios_entibacion.py",
        "m07_dedup_demolicion.py",
        "m08_patron_a_ci2.py",
        "m09_residual_mec_hasta_25.py",
        "m10_patron_b_imbornales.py",
        "m11_residuales_patron_a_excavacion.py",
        "m12_check_constraints.py",
        "m13_integer_centimos.py",
        "m14_audit_log.py",
        "m15_demolicion_material.py",
        "m16_san_bordillo_generico.py",
    }
    presentes = {f.name for f in ruta_migraciones.glob("m*.py")}
    assert esperados.issubset(presentes), f"Faltan: {esperados - presentes}"


# ---------------------------------------------------------------------------
# init_db() produce schema_version = 16
# ---------------------------------------------------------------------------

def test_schema_version_final_es_16_tras_init_db():
    # conftest.py ya ejecuta init_db() al arrancar la suite; aquí solo verificamos.
    with conectar() as conn:
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert max_version == 16, f"schema_version esperado 16, obtenido {max_version}"


def test_tabla_schema_version_tiene_16_filas():
    with conectar() as conn:
        count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    assert count == 16


# ---------------------------------------------------------------------------
# Import del paquete vs módulo antiguo
# ---------------------------------------------------------------------------

def test_infraestructura_db_es_paquete_no_modulo():
    """Confirmación defensiva: ``src.infraestructura.db`` debe ser paquete."""
    mod = importlib.import_module("src.infraestructura.db")
    assert hasattr(mod, "__path__"), (
        "src.infraestructura.db debe ser un paquete (directorio con __init__.py), "
        "no un módulo .py monolítico."
    )
