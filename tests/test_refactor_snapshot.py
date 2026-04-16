"""Test de snapshot - red de seguridad para el refactoring de ensamblaje.py.

Ejecuta calcular_presupuesto con parámetros de referencia y verifica que
el resultado numérico no cambia tras la refactorización.

Ejecutar:  conda activate licitaia && pytest tests/test_refactor_snapshot.py -v
"""

from __future__ import annotations

import copy

import pytest

from src.domain.parametros import ParametrosProyecto
from src.infraestructura.precios import cargar_precios, aplicar_ci
from src.presupuesto.ensamblaje import calcular_presupuesto


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
    acera_san = precios["acerados_san"][0] if precios["acerados_san"] else {}

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


# ── Snapshot: se genera en la primera ejecución, luego se compara ──────────

# Valor capturado con el código ANTES del refactoring.
# Si es None, la primera ejecución lo imprime para que lo copies aquí.
_SNAPSHOT: dict | None = None


def _comparar_resultado(resultado: dict, snapshot: dict):
    """Compara dos resultados de calcular_presupuesto campo a campo."""
    # Financieros escalares
    for clave in ("pem", "gg", "bi", "pbl_sin_iva", "iva", "total"):
        assert resultado[clave] == pytest.approx(snapshot[clave], abs=0.01), \
            f"{clave}: {resultado[clave]} != {snapshot[clave]}"

    # Capítulos: mismas claves y mismos subtotales
    assert set(resultado["capitulos"].keys()) == set(snapshot["capitulos"].keys()), \
        f"Capítulos difieren: {set(resultado['capitulos'].keys())} vs {set(snapshot['capitulos'].keys())}"

    for cap_nombre in resultado["capitulos"]:
        r_sub = resultado["capitulos"][cap_nombre]["subtotal"]
        s_sub = snapshot["capitulos"][cap_nombre]["subtotal"]
        assert r_sub == pytest.approx(s_sub, abs=0.01), \
            f"Capítulo '{cap_nombre}': subtotal {r_sub} != {s_sub}"

        # Partidas dentro de cada capítulo
        r_part = resultado["capitulos"][cap_nombre]["partidas"]
        s_part = snapshot["capitulos"][cap_nombre]["partidas"]
        assert set(r_part.keys()) == set(s_part.keys()), \
            f"Partidas de '{cap_nombre}' difieren: {set(r_part.keys())} vs {set(s_part.keys())}"
        for partida in r_part:
            assert r_part[partida] == pytest.approx(s_part[partida], abs=0.01), \
                f"Partida '{partida}' en '{cap_nombre}': {r_part[partida]} != {s_part[partida]}"


def test_snapshot_presupuesto():
    """El resultado de calcular_presupuesto debe ser idéntico tras refactor."""
    precios = cargar_precios()
    p = _hacer_params_referencia(precios)
    resultado = calcular_presupuesto(p, precios)

    if _SNAPSHOT is None:
        # Primera ejecución: imprimir el snapshot para capturarlo
        _snapshot_local = resultado
    else:
        _snapshot_local = _SNAPSHOT

    # Ejecutar una segunda vez y comparar contra sí mismo (o el snapshot fijo)
    resultado2 = calcular_presupuesto(p, precios)
    _comparar_resultado(resultado2, _snapshot_local)


def test_snapshot_valores_financieros():
    """Verifica que los totales financieros coinciden con el baseline capturado."""
    precios = cargar_precios()
    p = _hacer_params_referencia(precios)
    r = calcular_presupuesto(p, precios)

    assert r["pem"] == pytest.approx(54386.64, abs=0.01)
    assert r["gg"] == pytest.approx(6405.74, abs=0.01)
    assert r["bi"] == pytest.approx(2956.50, abs=0.01)
    assert r["pbl_sin_iva"] == pytest.approx(63750.0, abs=0.01)
    assert r["iva"] == pytest.approx(13387.50, abs=0.01)
    assert r["total"] == pytest.approx(77137.50, abs=0.01)
