"""Tests de auditoría numérica - verificaciones puntuales de fórmulas puras.

Estos tests comparan valores calculados por el código contra valores de
referencia obtenidos del Excel EMASESA (240415_VALORACIÓN ACTUACIONES.xlsx).
No usan AppTest: llaman directamente a las funciones del dominio.

Ejecutar:  conda activate licitaia && pytest tests/test_audit.py -v
"""

from __future__ import annotations

import math

import pytest

from src.domain.geometria import calcular_geometria
from src.domain.financiero import calcular_resumen
from src.presupuesto.materiales import materiales_san


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - Geometría ABA (A-Fundición 150)
# ═══════════════════════════════════════════════════════════════════════════════


def test_geometria_aba_fd150():
    """Geometría ABA FD150 P=1.2 sin entibación - valores manuales contra Excel."""
    geo = calcular_geometria(dn_mm=150, profundidad_m=1.2, es_san=False,
                             hay_entibacion=False, espesor_pavimento_m=0.0)

    # DN=150 < 250 → ancho_fondo = 0.6  (Excel H69)
    assert geo.ancho_fondo_m == pytest.approx(0.6, abs=1e-4)

    # Sin entibación → ancho_cima = P_exc*0.4 + fondo
    # clearance = 0.15 + 0.1*150/1000 = 0.165
    # P_exc = 1.2 + 0.165 = 1.365
    assert geo.P_exc_m == pytest.approx(1.365, abs=1e-4)
    assert geo.ancho_cima_m == pytest.approx(1.365 * 0.4 + 0.6, abs=1e-4)

    # Altura arena = 1.2*150/1000 + 0.2 = 0.38  (Excel H75)
    assert geo.altura_arena_m == pytest.approx(0.38, abs=1e-4)

    # Volumen tubo = pi/4 * (1.2*150/1000)^2 = pi/4 * 0.18^2
    d_ext = 1.2 * 150 / 1000
    vol_tubo_esperado = math.pi / 4 * d_ext ** 2
    assert geo.vol_tubo_pm == pytest.approx(vol_tubo_esperado, abs=1e-5)

    # Volúmenes > 0 y coherentes
    assert geo.vol_zanja_m3 > 0
    assert geo.vol_arena_pm > 0
    assert geo.vol_relleno_pm > 0
    assert geo.vol_zanja_m3 > geo.vol_arena_pm + geo.vol_tubo_pm

    # Sin entibación
    assert geo.sup_entibacion_pm == 0.0


def test_geometria_san_gres300():
    """Geometría SAN Gres300 P=1.5 con entibación - valores contra Excel S-Gres 300."""
    geo = calcular_geometria(dn_mm=300, profundidad_m=1.5, es_san=True,
                             hay_entibacion=True, espesor_pavimento_m=0.0)

    # SAN ancho_fondo = 1.2*300/1000 + 1.5 = 1.86  (Excel H62)
    assert geo.ancho_fondo_m == pytest.approx(1.86, abs=1e-4)

    # Con entibación → ancho_cima = ancho_fondo (paredes verticales)
    assert geo.ancho_cima_m == pytest.approx(1.86, abs=1e-4)

    # Altura arena SAN = 1.2*300/1000 + 0.3 = 0.66  (Excel H68)
    assert geo.altura_arena_m == pytest.approx(0.66, abs=1e-4)

    # Recubrimiento con entibación = fondo
    assert geo.ancho_recub_m == pytest.approx(1.86, abs=1e-4)

    # Entibación SAN: (P+1)*2*1.1 = (1.5+1)*2*1.1 = 5.5
    assert geo.sup_entibacion_pm == pytest.approx(5.5, abs=1e-4)


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - Superficie de entibación
# ═══════════════════════════════════════════════════════════════════════════════


def test_entibacion_superficie_aba():
    """Entibación ABA P=2.0 DN=150: (P+0.1*DN/1000+0.20)*2."""
    geo = calcular_geometria(dn_mm=150, profundidad_m=2.0, es_san=False,
                             hay_entibacion=True)
    # (2.0 + 0.1*150/1000 + 0.20) * 2 = (2.0 + 0.015 + 0.20) * 2 = 4.43
    esperado = (2.0 + 0.1 * 150 / 1000 + 0.20) * 2
    assert geo.sup_entibacion_pm == pytest.approx(esperado, abs=1e-4)


def test_entibacion_superficie_san():
    """Entibación SAN P=2.0: (P+1)*2*1.1 (fórmula simplificada obra civil)."""
    geo = calcular_geometria(dn_mm=300, profundidad_m=2.0, es_san=True,
                             hay_entibacion=True)
    esperado = (2.0 + 1.0) * 2.0 * 1.1  # = 6.6
    assert geo.sup_entibacion_pm == pytest.approx(esperado, abs=1e-4)


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - Resumen financiero
# ═══════════════════════════════════════════════════════════════════════════════


def test_financiero_roundup_boundary():
    """ROUNDUP a decena: valor exacto no sube, valor+0.01 sí sube."""
    # Caso exacto: PEM+GG+BI = 1190.00 → PBL = 1190
    r1 = calcular_resumen(pem=1000.0, materiales=0.0,
                          pct_gg=0.13, pct_bi=0.06, pct_iva=0.21)
    # PEM=1000, GG=130, BI=60, sum=1190 → ceil(119)*10 = 1190
    assert r1.pbl_sin_iva == 1190.0

    # Caso no exacto: forzar que PEM+GG+BI > 1190
    r2 = calcular_resumen(pem=1000.10, materiales=0.0,
                          pct_gg=0.13, pct_bi=0.06, pct_iva=0.21)
    # 1000.10 + 130.013 + 60.006 = 1190.119 → ceil(119.0119)*10 = 1200
    assert r2.pbl_sin_iva == 1200.0


def test_financiero_materiales_excluidos():
    """Materiales se excluyen de la base GG/BI."""
    r = calcular_resumen(pem=1000.0, materiales=200.0,
                         pct_gg=0.13, pct_bi=0.06, pct_iva=0.21)
    # base = 1000 - 200 = 800
    assert r.base_gg_bi == pytest.approx(800.0, abs=0.01)
    assert r.gg == pytest.approx(800 * 0.13, abs=0.01)  # 104
    assert r.bi == pytest.approx(800 * 0.06, abs=0.01)   # 48
    # PEM + GG + BI = 1000 + 104 + 48 = 1152 → ceil(115.2)*10 = 1160
    assert r.pbl_sin_iva == 1160.0


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - Aplicación de CI
# ═══════════════════════════════════════════════════════════════════════════════


def test_ci_no_escala_campos_no_precio():
    """CI no modifica campos no-precio (umbral, factor_piezas, diámetro)."""
    import copy
    from src.infraestructura.precios import cargar_precios, aplicar_ci

    precios = cargar_precios()
    copia = copy.deepcopy(precios)
    aplicar_ci(copia)

    # umbral_profundidad_m no debe cambiar
    assert copia["excavacion"]["umbral_profundidad_m"] == precios["excavacion"]["umbral_profundidad_m"]

    # factor_piezas en tuberías no debe cambiar
    for orig, ci in zip(precios["catalogo_aba"], copia["catalogo_aba"]):
        assert ci.get("factor_piezas") == orig.get("factor_piezas"), \
            f"factor_piezas cambió de {orig.get('factor_piezas')} a {ci.get('factor_piezas')}"
        assert ci.get("diametro_mm") == orig.get("diametro_mm")

    # Pero precio_m SÍ debe cambiar (multiplicado por CI)
    pct_ci = precios["pct_ci"]
    if pct_ci > 1.0:
        for orig, ci in zip(precios["catalogo_aba"], copia["catalogo_aba"]):
            if orig.get("precio_m", 0) > 0:
                assert ci["precio_m"] == pytest.approx(orig["precio_m"] * pct_ci, rel=1e-4)


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - Pates SAN boundaries
# ═══════════════════════════════════════════════════════════════════════════════


def test_pates_san_boundaries():
    """Fórmula pates: IF(P<2.5,6,IF(P<3.5,9,12)) - verificar fronteras."""
    # Pozo SAN de prueba con precios material
    pozo = {
        "intervalo": 32.0,
        "precio_tapa_material": 0.0,
        "precio_pate_material": 10.0,  # Precio ficticio para facilitar cálculo
    }

    # P=2.49 → 6 pates
    r1 = materiales_san(100.0, 2.49, pozo)
    assert r1 is not None
    n_pozos = 100.0 / 32.0
    assert r1[0] == pytest.approx(n_pozos * 6 * 10.0, abs=0.01)

    # P=2.5 → 9 pates (frontera: 2.5 no es < 2.5)
    r2 = materiales_san(100.0, 2.5, pozo)
    assert r2 is not None
    assert r2[0] == pytest.approx(n_pozos * 9 * 10.0, abs=0.01)

    # P=3.49 → 9 pates
    r3 = materiales_san(100.0, 3.49, pozo)
    assert r3 is not None
    assert r3[0] == pytest.approx(n_pozos * 9 * 10.0, abs=0.01)

    # P=3.5 → 12 pates (frontera: 3.5 no es < 3.5)
    r4 = materiales_san(100.0, 3.5, pozo)
    assert r4 is not None
    assert r4[0] == pytest.approx(n_pozos * 12 * 10.0, abs=0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - Canon mixto ABA vs SAN
# ═══════════════════════════════════════════════════════════════════════════════


def test_canon_mixto_aba_vs_san():
    """Canon mixto ABA usa L*h_pav, SAN usa L*h_pav*(W_cima+0.75).

    Verificado contra Excel:
      ABA H42 = H79 (solo altura pavimento)
      SAN H37 = H72*(H63+0.75)
    """
    from src.presupuesto.capitulos_obra_civil import capitulo_obra_civil
    from src.infraestructura.precios import cargar_precios, aplicar_ci
    import copy

    precios = cargar_precios()
    pr = copy.deepcopy(precios)
    aplicar_ci(pr)

    aba_item = next(i for i in pr["catalogo_aba"] if i["diametro_mm"] == 150)
    san_item = next(i for i in pr["catalogo_san"] if i["diametro_mm"] == 300 and "Gres" in i["tipo"])

    # ABA con h_pav=0.20
    _, _, aux_aba = capitulo_obra_civil(
        100.0, 2.0, aba_item, pr, pct_manual=0.3,
        espesor_pavimento_m=0.20, entibacion_item=None)

    # SAN con h_pav=0.20
    _, _, aux_san = capitulo_obra_civil(
        100.0, 2.0, san_item, pr, es_san=True, pct_manual=0.3,
        espesor_pavimento_m=0.20, entibacion_item=None)

    # ABA canon mixto: L × h_pav × precio
    assert aux_aba["canon_mixto"] > 0, "Canon mixto ABA debe existir con h_pav>0"

    # SAN canon mixto debe ser mayor (incluye factor de ancho)
    assert aux_san["canon_mixto"] > aux_aba["canon_mixto"], (
        f"Canon SAN ({aux_san['canon_mixto']:.2f}) debería ser mayor que ABA "
        f"({aux_aba['canon_mixto']:.2f}) por el factor (W_cima+0.75)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# D.1 - DN=250 ABA boundary
# ═══════════════════════════════════════════════════════════════════════════════


def test_dn_boundary_250_aba():
    """ABA DN=250 usa fórmula 1.2*DN/1000+0.4, no el flat 0.6 (condición <250)."""
    geo = calcular_geometria(dn_mm=250, profundidad_m=1.5, es_san=False,
                             hay_entibacion=False)
    # DN=250 NO es < 250, así que va al else: 1.2*250/1000+0.4 = 0.7
    assert geo.ancho_fondo_m == pytest.approx(0.7, abs=1e-4)

    # DN=249 SÍ es < 250 → flat 0.6
    geo2 = calcular_geometria(dn_mm=249, profundidad_m=1.5, es_san=False,
                              hay_entibacion=False)
    assert geo2.ancho_fondo_m == pytest.approx(0.6, abs=1e-4)
