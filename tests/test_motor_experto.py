"""Tests del motor experto CLIPSpy.

Portados de verify_clips.py — mismos 10 casos (A-J) como tests pytest.
"""

from __future__ import annotations

import pytest

from src.reglas.motor import resolver_decisiones

TOLERANCIA = 0.01


def _resolver(precios, tipo, dn, red, prof,
              instalacion="enterrada", desmontaje="none"):
    return resolver_decisiones(
        tipo_tuberia=tipo,
        diametro_mm=dn,
        red=red,
        profundidad=prof,
        precios=precios,
        instalacion=instalacion,
        desmontaje_tipo=desmontaje,
    )


# ── Caso A: FD DN150 ABA prof=1.0 ──────────────────────────────────────────

def test_a_factor_piezas_fd150(precios):
    d = _resolver(precios, "FD", 150, "ABA", 1.0)
    assert abs(d["factor_piezas"] - 1.2) < TOLERANCIA

def test_a_entibacion_false(precios):
    d = _resolver(precios, "FD", 150, "ABA", 1.0)
    assert not d["entibacion"]["necesaria"]
    assert d["entibacion"]["item"] is None


# ── Caso B: Gres DN300 SAN prof=2.0 ────────────────────────────────────────

def test_b_factor_piezas_gres300(precios):
    d = _resolver(precios, "Gres", 300, "SAN", 2.0)
    assert abs(d["factor_piezas"] - 1.35) < TOLERANCIA

def test_b_entibacion_true(precios):
    d = _resolver(precios, "Gres", 300, "SAN", 2.0)
    assert d["entibacion"]["necesaria"]
    assert d["entibacion"]["item"] is not None


# ── Caso C: PE-100 DN200 ABA prof=3.0 ──────────────────────────────────────

def test_c_factor_pe100(precios):
    d = _resolver(precios, "PE-100", 200, "ABA", 3.0)
    assert abs(d["factor_piezas"] - 1.2) < TOLERANCIA

def test_c_entibacion_true(precios):
    d = _resolver(precios, "PE-100", 200, "ABA", 3.0)
    assert d["entibacion"]["necesaria"]


# ── Caso D: HA DN600 SAN prof=1.0 ──────────────────────────────────────────

def test_d_factor_ha600(precios):
    d = _resolver(precios, "HA", 600, "SAN", 1.0)
    assert abs(d["factor_piezas"] - 1.0) < TOLERANCIA

def test_d_entibacion_false(precios):
    d = _resolver(precios, "HA", 600, "SAN", 1.0)
    assert not d["entibacion"]["necesaria"]


# ── Caso E: Umbral estricto (prof == umbral -> False) ──────────────────────

def test_e_umbral_estricto(precios):
    cat = precios.get("catalogo_entibacion", [])
    if not cat:
        pytest.skip("catalogo_entibacion vacio")
    umbral = float(cat[0].get("umbral_m", 1.5))
    red = cat[0].get("red") or "ABA"
    d = _resolver(precios, "FD", 150, red, umbral)
    assert not d["entibacion"]["necesaria"], (
        f"prof={umbral} == umbral -> entibacion debe ser False"
    )


# ── Caso F: Catalogo pozos vacio ───────────────────────────────────────────

def test_f_pozos_catalogo_vacio(precios):
    precios_sin_pozos = dict(precios, catalogo_pozos=[])
    d = resolver_decisiones(
        tipo_tuberia="FD", diametro_mm=150, red="ABA", profundidad=1.0,
        precios=precios_sin_pozos, instalacion="enterrada",
        desmontaje_tipo="none",
    )
    assert d["pozo_registro"]["item"] is None


# ── Caso G: Valvuleria orden de catalogo ───────────────────────────────────

def test_g_valvuleria_orden_catalogo(precios):
    d = _resolver(precios, "FD", 150, "ABA", 1.0, instalacion="enterrada")
    items = d["valvuleria"]["items"]
    cat = precios.get("catalogo_valvuleria", [])
    indices = []
    for vi in items:
        for idx, ci in enumerate(cat):
            if ci.get("label") == vi.get("label"):
                indices.append(idx)
                break
    assert indices == sorted(indices), (
        f"valvuleria items no en orden de catalogo: {[v.get('label') for v in items]}"
    )


# ── Caso H: Desmontaje mas especifico ─────────────────────────────────────

def test_h_desmontaje_especifico(precios):
    d = _resolver(precios, "FD", 80, "ABA", 1.0, desmontaje="normal")
    item_desm = d["desmontaje"]["item"]
    cat_desm = [
        x for x in precios.get("catalogo_desmontaje", [])
        if not x.get("es_fibrocemento", 0) and 80 <= int(x["dn_max"])
    ]
    if not cat_desm:
        pytest.skip("sin items de desmontaje normal aplicables a DN80")
    mejor_esperado = min(cat_desm, key=lambda x: int(x["dn_max"]))
    assert item_desm is not None
    assert item_desm.get("label") == mejor_esperado.get("label")


# ── Caso I: Determinismo ──────────────────────────────────────────────────

def test_i_determinismo(precios):
    args = ("FD", 150, "ABA", 1.5)
    kwargs = dict(instalacion="enterrada", desmontaje="normal")
    d1 = _resolver(precios, *args, **kwargs)
    d2 = _resolver(precios, *args, **kwargs)
    assert d1["factor_piezas"] == d2["factor_piezas"]
    assert d1["entibacion"]["necesaria"] == d2["entibacion"]["necesaria"]
    assert (d1["pozo_registro"]["item"] is None) == (d2["pozo_registro"]["item"] is None)
    assert len(d1["valvuleria"]["items"]) == len(d2["valvuleria"]["items"])


# ── Caso J: Catalogo entibacion vacio ─────────────────────────────────────

def test_j_entibacion_catalogo_vacio(precios):
    precios_vacio = dict(precios, catalogo_entibacion=[])
    d = resolver_decisiones(
        tipo_tuberia="FD", diametro_mm=150, red="ABA", profundidad=5.0,
        precios=precios_vacio, instalacion="enterrada",
        desmontaje_tipo="none",
    )
    assert not d["entibacion"]["necesaria"]
