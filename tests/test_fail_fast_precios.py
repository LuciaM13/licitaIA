"""Tests de fail-fast en el cálculo de precios (Paso 1 del refactor Fase 2).

Verifica que:
  - ``_importe`` lanza ``ValueError`` ante None, negativos o NaN en vez de
    devolver 0 € silenciosamente.
  - ``_resolver_item_ci`` (vía la clausura ``_ci`` dentro de
    ``_reresolver_items_ci``) lanza ``ValueError`` cuando un item seleccionado
    por el usuario no se encuentra en el catálogo con CI aplicado, en lugar
    de caer al precio base (infravaloración ~5 %).

Excepción a la regla "solo AppTest": este test valida invariantes puros
del módulo de cálculo (sin superficie Streamlit). Ver AGENTS.md.
"""
from __future__ import annotations

import math

import pytest

from src.presupuesto.capitulos_obra_civil import _importe
from src.aplicacion.calcular_presupuesto import _reresolver_items_ci
from src.domain.parametros import ParametrosProyecto


# ---------------------------------------------------------------------------
# _importe: valores válidos siguen funcionando
# ---------------------------------------------------------------------------

def test_importe_valores_validos_devuelve_producto():
    assert _importe(2.5, 10.0) == 25.0
    assert _importe(0.0, 100.0) == 0.0
    assert _importe(100.0, 0.0) == 0.0


# ---------------------------------------------------------------------------
# _importe: fail-fast ante None
# ---------------------------------------------------------------------------

def test_importe_lanza_valueerror_ante_cantidad_none():
    with pytest.raises(ValueError, match="None"):
        _importe(None, 10.0)  # type: ignore[arg-type]


def test_importe_lanza_valueerror_ante_precio_none():
    with pytest.raises(ValueError, match="None"):
        _importe(10.0, None)  # type: ignore[arg-type]


def test_importe_lanza_valueerror_ante_ambos_none():
    with pytest.raises(ValueError, match="None"):
        _importe(None, None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _importe: fail-fast ante negativos
# ---------------------------------------------------------------------------

def test_importe_lanza_valueerror_ante_cantidad_negativa():
    with pytest.raises(ValueError, match="negativo"):
        _importe(-1.0, 10.0)


def test_importe_lanza_valueerror_ante_precio_negativo():
    with pytest.raises(ValueError, match="negativo"):
        _importe(10.0, -5.0)


# ---------------------------------------------------------------------------
# _importe: fail-fast ante NaN / infinito
# ---------------------------------------------------------------------------

def test_importe_lanza_valueerror_ante_nan():
    with pytest.raises(ValueError, match="no finito"):
        _importe(math.nan, 10.0)


def test_importe_lanza_valueerror_ante_infinito():
    with pytest.raises(ValueError, match="no finito"):
        _importe(math.inf, 10.0)


# ---------------------------------------------------------------------------
# _reresolver_items_ci: fail-fast cuando un item no está en el catálogo CI
# ---------------------------------------------------------------------------

def test_reresolver_items_ci_lanza_si_item_no_esta_en_catalogo():
    """Si el usuario seleccionó un item y éste no está en el catálogo con CI
    aplicado, el cálculo debe abortar con ValueError claro en vez de caer
    silenciosamente al precio base (infravaloración ~5 %)."""
    item_fantasma = {"label": "Tubería inexistente DN999", "precio_m": 100.0,
                     "tipo": "A", "diametro_mm": 999}
    p = ParametrosProyecto(
        aba_item=item_fantasma,
        aba_longitud_m=10.0,
        aba_profundidad_m=1.5,
    )
    precios_mock = {
        "catalogo_aba": [],  # vacío a propósito: el item no se encontrará
        "catalogo_san": [],
        "acerados_aba": [],
        "acerados_san": [],
        "bordillos_reposicion": [],
        "calzadas_reposicion": [],
        "catalogo_subbases": [],
    }
    with pytest.raises(ValueError, match="no se resolvió tras"):
        _reresolver_items_ci(p, precios_mock)


def test_reresolver_items_ci_no_lanza_si_item_es_none():
    """Un item=None es legítimo (p.ej. pav_aba_acerado_item cuando la
    superficie es 0). No debe lanzar ValueError."""
    p = ParametrosProyecto(
        aba_item=None,
        san_item=None,
    )
    precios_mock = {
        "catalogo_aba": [],
        "catalogo_san": [],
        "acerados_aba": [],
        "acerados_san": [],
        "bordillos_reposicion": [],
        "calzadas_reposicion": [],
        "catalogo_subbases": [],
    }
    # No debe lanzar; todos los items son None y eso es estado válido.
    result = _reresolver_items_ci(p, precios_mock)
    assert result["aba_item"] is None
    assert result["san_item"] is None
