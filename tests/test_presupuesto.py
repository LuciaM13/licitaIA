"""Tests de regresion del presupuesto contra verify_baseline.json.

Replica exactamente la funcion regresion_baseline() de verify_clips.py
(lineas 204-271) como tests pytest parametrizados.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import ParametrosProyecto
from src.presupuesto import calcular_presupuesto

TOLERANCIA = 0.01
BASELINE_PATH = Path(__file__).resolve().parent.parent / "verify_baseline.json"


@pytest.fixture(scope="session")
def baseline():
    if not BASELINE_PATH.exists():
        pytest.skip("verify_baseline.json no encontrado")
    with open(BASELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _params_baseline_1(precios):
    """baseline_1_aba_fd150: FD DN150 ABA, 200m, prof=1.2."""
    aba_items = [t for t in precios.get("catalogo_aba", [])
                 if int(t["diametro_mm"]) == 150]
    if not aba_items:
        pytest.skip("No hay item ABA DN150 en catalogo")
    return ParametrosProyecto(
        aba_item=aba_items[0],
        aba_longitud_m=200.0, aba_profundidad_m=1.2, pct_manual=0.30,
        instalacion_valvuleria="enterrada", desmontaje_tipo="normal",
        pct_seguridad=0.03, pct_gestion=0.01,
    )


def _params_baseline_2(precios):
    """baseline_2_san_gres300: Gres DN300 SAN, 150m, prof=2.0."""
    san_items = [t for t in precios.get("catalogo_san", [])
                 if int(t["diametro_mm"]) == 300]
    if not san_items:
        pytest.skip("No hay item SAN DN300 en catalogo")
    return ParametrosProyecto(
        san_item=san_items[0],
        san_longitud_m=150.0, san_profundidad_m=2.0, pct_manual=0.30,
        pct_seguridad=0.03, pct_gestion=0.01, imbornales_tipo="adaptacion",
    )


def _params_baseline_3(precios):
    """baseline_3_aba_patologico: ABA DN>=300 o DN150, 100m, prof=3.5."""
    aba_items_large = [t for t in precios.get("catalogo_aba", [])
                       if int(t["diametro_mm"]) >= 300]
    aba_items = [t for t in precios.get("catalogo_aba", [])
                 if int(t["diametro_mm"]) == 150]
    item = aba_items_large[0] if aba_items_large else (
        aba_items[0] if aba_items else None)
    if item is None:
        pytest.skip("No hay items ABA en catalogo")
    return ParametrosProyecto(
        aba_item=item,
        aba_longitud_m=100.0, aba_profundidad_m=3.5, pct_manual=0.50,
        instalacion_valvuleria="enterrada", desmontaje_tipo="fibrocemento",
        pct_seguridad=0.05, pct_gestion=0.02, espesor_pavimento_m=0.15,
    )


_BASELINE_BUILDERS = {
    "baseline_1_aba_fd150": _params_baseline_1,
    "baseline_2_san_gres300": _params_baseline_2,
    "baseline_3_aba_patologico": _params_baseline_3,
}


@pytest.mark.parametrize("nombre", list(_BASELINE_BUILDERS.keys()))
def test_baseline_total(nombre, precios, baseline):
    if nombre not in baseline:
        pytest.skip(f"{nombre} no encontrado en baseline")
    p = _BASELINE_BUILDERS[nombre](precios)
    r = calcular_presupuesto(p, precios)
    b = baseline[nombre]
    diff = abs(r["total"] - b["total"])
    assert diff <= TOLERANCIA, (
        f"{nombre}: total={r['total']:.2f} baseline={b['total']:.2f} diff={diff:.4f}"
    )


@pytest.mark.parametrize("nombre", list(_BASELINE_BUILDERS.keys()))
def test_baseline_capitulos(nombre, precios, baseline):
    if nombre not in baseline:
        pytest.skip(f"{nombre} no encontrado en baseline")
    p = _BASELINE_BUILDERS[nombre](precios)
    r = calcular_presupuesto(p, precios)
    b = baseline[nombre]
    for cap_key, b_cap in b.get("capitulos", {}).items():
        cap_nombre = cap_key.split(" ", 1)[1] if " " in cap_key else cap_key
        r_cap = next((v for k, v in r["capitulos"].items() if cap_nombre in k), None)
        if r_cap is None:
            continue
        diff = abs(r_cap["subtotal"] - b_cap["subtotal"])
        assert diff <= TOLERANCIA, (
            f"{nombre}/{cap_nombre}: subtotal={r_cap['subtotal']:.2f} "
            f"baseline={b_cap['subtotal']:.2f} diff={diff:.4f}"
        )
