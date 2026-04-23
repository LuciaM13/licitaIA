"""Tests baseline contra Excel EMASESA oficial.

Dos tests anclados a valores concretos del Excel:

1. ``test_snapshot_valores_financieros`` — totales financieros de un proyecto
   de referencia mixto ABA+SAN con materiales seleccionados explícitamente.
   Contrastado con el Excel `240415_VALORACIÓN ACTUACIONES.xlsx`.

2. ``test_material_demolicion_afecta_total`` — verifica que cambiar el
   material de demolición de calzada (aglomerado / adoquín / hormigón)
   produce totales distintos y en el orden correcto. Es el único test
   que varía la dimensión "material seleccionado" actualmente; se amplía
   en el Pilar A3 con el resto de variantes.

Historia: este archivo se llamaba ``test_refactor_snapshot.py`` y contenía
además un ``test_snapshot_presupuesto`` que comparaba el resultado consigo
mismo en la misma ejecución (determinismo, no corrección). Eliminado en
la auditoría A1 porque nunca podía fallar salvo non-determinismo del
runtime y por tanto no aportaba evidencia de calidad.

Ejecutar:  conda activate licitaia && pytest tests/test_snapshot_excel.py -v
"""

from __future__ import annotations

import copy

import pytest

from src.domain.parametros import ParametrosProyecto
from src.infraestructura.precios import cargar_precios, aplicar_ci
from src.aplicacion.calcular_presupuesto import calcular_presupuesto


def _hacer_params_referencia(precios: dict) -> ParametrosProyecto:
    """Crea ParametrosProyecto con valores deterministas de referencia."""
    pr = copy.deepcopy(precios)
    aplicar_ci(pr)

    aba_item = next(i for i in precios["catalogo_aba"] if i["diametro_mm"] == 150)
    san_item = next(
        i for i in precios["catalogo_san"]
        if i["diametro_mm"] == 300 and "Gres" in i["tipo"]
    )
    acerado_aba = precios["acerados_aba"][0] if precios["acerados_aba"] else {}
    bordillo = precios["bordillos_reposicion"][0] if precios["bordillos_reposicion"] else {}
    calzada = precios["calzadas_reposicion"][0] if precios["calzadas_reposicion"] else {}

    return ParametrosProyecto(
        aba_item=aba_item,
        aba_longitud_m=100.0,
        aba_profundidad_m=2.0,
        san_item=san_item,
        san_longitud_m=80.0,
        san_profundidad_m=1.5,
        pav_aba_acerado_m2=50.0,
        pav_aba_acerado_item=acerado_aba,
        pav_aba_bordillo_m=25.0,
        pav_aba_bordillo_item=bordillo,
        pav_aba_calzada_m2=0.0,
        pav_aba_calzada_item={},
        pav_san_calzada_m2=60.0,
        pav_san_calzada_item=calzada,
        pav_san_acera_m2=0.0,
        pav_san_acera_item={},
        acometidas_aba_n=3,
        acometidas_san_n=2,
        pct_manual=0.30,
        espesor_pavimento_m=0.20,
        pct_seguridad=0.025,
        pct_gestion=0.015,
        instalacion_valvuleria="enterrada",
        desmontaje_tipo="none",
        pozos_existentes_aba="none",
        pozos_existentes_san="none",
        imbornales_tipo="none",
    )


def test_snapshot_valores_financieros():
    """Verifica que los totales financieros coinciden con el baseline Excel.

    Baseline actualizado 2026-04-19 tras audit A2C:
    - Acometidas ABA: renombrados tipos y reajustado precio al Excel oficial
      (Adaptación 32.26, Reposición <6m 261.92, Reposición >6m 326.36 €).
      factor_piezas retirado de 1.2 → 1.0 (el Excel ya incluye piezas).
      Impacto: 3 acometidas × (478.21 - 261.92) = -648.87 € directos.
    - Desmontaje ABA DN<150 y DN<600 corregidos (~22 % sobreprecio).
    - 15 subcoberturas insertadas (desmontaje DN=160, pozos SAN ladrillo,
      tuberías ABA HACCH) — no afectan este proyecto (usa FD DN150 y gres).
    - Impacto neto PEM: -749.42 € vs snapshot previo (59594.68 → 58845.26).
    """
    precios = cargar_precios()
    p = _hacer_params_referencia(precios)
    r = calcular_presupuesto(p, precios)

    assert r["pem"] == pytest.approx(58845.26, abs=0.01)
    assert r["gg"] == pytest.approx(6985.40, abs=0.01)
    assert r["bi"] == pytest.approx(3224.03, abs=0.01)
    assert r["pbl_sin_iva"] == pytest.approx(69060.0, abs=0.01)
    assert r["iva"] == pytest.approx(14502.60, abs=0.01)
    assert r["total"] == pytest.approx(83562.60, abs=0.01)


def test_material_demolicion_afecta_total():
    """Cambiar material a demoler produce totales distintos y coherentes.

    Para una calzada ABA con 100 m² a demoler:
      - adoquín (Excel 15.80 €/m²) → coste más bajo dentro de su rango
      - hormigón (Excel 17.43 €/m²) → más caro (+10.3 % vs adoquín)
      - aglomerado (Excel 14.29 €/m²) → más barato (-9.6 %)
    Verificamos ordenación y delta aproximado.
    """
    precios = cargar_precios()

    def _total_con_material(mat: str) -> float:
        p = _hacer_params_referencia(precios)
        p.pav_aba_calzada_m2 = 100.0
        p.pav_aba_calzada_item = precios["calzadas_reposicion"][0]
        p.material_demo_calzada_aba = mat
        return calcular_presupuesto(p, precios)["pem"]

    pem_aglomerado = _total_con_material("aglomerado")
    pem_adoquin = _total_con_material("adoquin")
    pem_hormigon = _total_con_material("hormigon")

    # Ordenación esperada: aglomerado < adoquín < hormigón
    assert pem_aglomerado < pem_adoquin < pem_hormigon

    # Delta entre hormigón y aglomerado en la partida de demolición:
    # 100 m² × (17.43 - 14.29) = 314 €. En PEM sube un poco más por
    # amplificación de pct_seguridad + pct_gestion + servicios_afectados.
    delta = pem_hormigon - pem_aglomerado
    assert 310 <= delta <= 340, f"Delta hormigón-aglomerado = {delta:.2f} (esperado 310-340)"
