"""
Tests del sistema experto: inferencia en cascada de etiquetas + alertas.

Excepción justificada a la estrategia "solo AppTest" del proyecto: el motor
CLIPS es lógica pura (no UI) y el encadenamiento 1er→2º nivel no tiene
representación en AppTest. La demostración de inferencia real es uno de los
argumentos centrales de la defensa del TFG, por lo que merece test pytest
directo sobre la función pura.
"""

from __future__ import annotations

import pytest

from src.reglas.alertas_clips import generar_alertas_tecnicas


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _defaults() -> dict:
    """Caso base totalmente neutro: no dispara ninguna regla."""
    return dict(
        aba_activa=True, san_activa=False,
        aba_longitud_m=50.0, aba_profundidad_m=1.5, san_profundidad_m=0.0,
        aba_diametro_mm=200, san_diametro_mm=0, aba_tipo_tuberia="PE-100",
        acometidas_aba_n=2, acometidas_san_n=0,
        desmontaje_tipo="none",
        pct_seguridad=0.04, pct_gestion=0.02,
        pct_servicios_afectados=0.01,
        conduccion_provisional_m=0.0,
        pozos_existentes_aba="none", pozos_existentes_san="none",
        instalacion_valvuleria="enterrada",
    )


def _ids_etiquetas(resultado: dict) -> set[str]:
    return {e["id"] for e in resultado["etiquetas"]}


def _rule_ids_alertas(resultado: dict) -> set[str]:
    return {a["rule_id"] for a in resultado["alertas"]}


# ---------------------------------------------------------------------------
# Caso neutro: sin disparos
# ---------------------------------------------------------------------------

def test_proyecto_neutro_sin_etiquetas_ni_alertas():
    r = generar_alertas_tecnicas(**_defaults())
    assert r["etiquetas"] == []
    assert r["alertas"] == []


# ---------------------------------------------------------------------------
# Reglas de clasificación de 1er nivel (cada una aislada)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "overrides,etiqueta_esperada",
    [
        # Profundidad ABA por encima del umbral (3.5m).
        ({"aba_profundidad_m": 4.0}, "zanja-compleja"),
        # Profundidad SAN por encima del umbral.
        ({"san_activa": True, "san_profundidad_m": 4.0}, "zanja-compleja"),
        # Longitud + acometidas → tramo urbano denso.
        ({"aba_longitud_m": 150.0, "acometidas_aba_n": 10}, "tramo-urbano-denso"),
        # Fibrocemento → régimen amianto.
        ({"desmontaje_tipo": "fibrocemento"}, "obra-regulada-amianto"),
        # Pozos existentes en ABA.
        ({"pozos_existentes_aba": "demolicion"}, "intervencion-infraestructura"),
        # Pozos existentes en SAN.
        ({"pozos_existentes_san": "anulacion"}, "intervencion-infraestructura"),
    ],
)
def test_etiquetas_primer_nivel(overrides, etiqueta_esperada):
    params = _defaults()
    params.update(overrides)
    r = generar_alertas_tecnicas(**params)
    assert etiqueta_esperada in _ids_etiquetas(r), (
        f"Esperaba etiqueta '{etiqueta_esperada}' con overrides={overrides}. "
        f"Obtenidas: {_ids_etiquetas(r)}"
    )


def test_zanja_compartida_probable():
    # ABA y SAN activas con profundidades casi iguales → zanja compartida.
    params = _defaults()
    params.update(
        san_activa=True,
        aba_profundidad_m=2.0, san_profundidad_m=2.15,   # diff = 0.15 < 0.3
    )
    r = generar_alertas_tecnicas(**params)
    assert "zanja-compartida-probable" in _ids_etiquetas(r)


# ---------------------------------------------------------------------------
# Encadenamiento 1er → 2º nivel
# ---------------------------------------------------------------------------
# La etiqueta `proyecto-alto-riesgo` es el hecho derivado de 2º nivel que
# justifica que este sistema es un SE con inferencia real y no una cadena
# de if/else. Estos tests son la evidencia de defensa en el TFG.

def test_encadenamiento_zanja_compleja_sola_no_dispara_alto_riesgo():
    """Solo zanja-compleja por sí sola NO debe elevar a alto riesgo."""
    params = _defaults()
    params.update(aba_profundidad_m=4.0)   # solo zanja compleja
    r = generar_alertas_tecnicas(**params)
    etiquetas = _ids_etiquetas(r)
    assert "zanja-compleja" in etiquetas
    assert "proyecto-alto-riesgo" not in etiquetas


def test_encadenamiento_compleja_mas_urbano_dispara_alto_riesgo():
    """zanja-compleja + tramo-urbano-denso → proyecto-alto-riesgo (2º nivel)."""
    params = _defaults()
    params.update(
        aba_profundidad_m=4.0,           # zanja compleja
        aba_longitud_m=150.0, acometidas_aba_n=10,   # tramo urbano denso
    )
    r = generar_alertas_tecnicas(**params)
    etiquetas = _ids_etiquetas(r)
    assert "zanja-compleja" in etiquetas
    assert "tramo-urbano-denso" in etiquetas
    assert "proyecto-alto-riesgo" in etiquetas


def test_encadenamiento_compleja_mas_amianto_dispara_alto_riesgo():
    """zanja-compleja + obra-regulada-amianto → proyecto-alto-riesgo."""
    params = _defaults()
    params.update(
        aba_profundidad_m=4.0,
        desmontaje_tipo="fibrocemento",
    )
    r = generar_alertas_tecnicas(**params)
    etiquetas = _ids_etiquetas(r)
    assert "zanja-compleja" in etiquetas
    assert "obra-regulada-amianto" in etiquetas
    assert "proyecto-alto-riesgo" in etiquetas


def test_encadenamiento_negativo_urbano_solo_no_dispara_alto_riesgo():
    """tramo-urbano-denso por sí solo (sin zanja-compleja) NO eleva a alto riesgo."""
    params = _defaults()
    params.update(aba_longitud_m=150.0, acometidas_aba_n=10)
    r = generar_alertas_tecnicas(**params)
    etiquetas = _ids_etiquetas(r)
    assert "tramo-urbano-denso" in etiquetas
    assert "zanja-compleja" not in etiquetas
    assert "proyecto-alto-riesgo" not in etiquetas


# ---------------------------------------------------------------------------
# Alertas dependientes de etiquetas (encadenamiento 1er→2º → alerta)
# ---------------------------------------------------------------------------

def test_alerta_fibrocemento_requiere_etiqueta_y_gestion_cero():
    """La alerta solo dispara si hay etiqueta obra-regulada-amianto + pct_gestion=0."""
    # Caso 1: fibrocemento + gestion 0 → dispara
    params = _defaults()
    params.update(desmontaje_tipo="fibrocemento", pct_gestion=0.0)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-fibrocemento-sin-gestion" in _rule_ids_alertas(r)

    # Caso 2: fibrocemento + gestion 2% → etiqueta sí, alerta no
    params["pct_gestion"] = 0.02
    r = generar_alertas_tecnicas(**params)
    assert "obra-regulada-amianto" in _ids_etiquetas(r)
    assert "alerta-fibrocemento-sin-gestion" not in _rule_ids_alertas(r)


def test_alertas_seguridad_separadas_por_umbral():
    """Por debajo de 2% S&S dispara crítica. Entre 2% y 3% dispara blindaje."""
    base = _defaults()
    base.update(aba_profundidad_m=4.0)   # zanja compleja activa

    # S&S 1.5% → crítica, sin blindaje.
    r = generar_alertas_tecnicas(**{**base, "pct_seguridad": 0.015})
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-seguridad-critica" in rule_ids
    assert "alerta-blindaje-necesario" not in rule_ids

    # S&S 2.5% → blindaje, sin crítica.
    r = generar_alertas_tecnicas(**{**base, "pct_seguridad": 0.025})
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-blindaje-necesario" in rule_ids
    assert "alerta-seguridad-critica" not in rule_ids

    # S&S 3.5% → ninguna de las dos.
    r = generar_alertas_tecnicas(**{**base, "pct_seguridad": 0.035})
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-seguridad-critica" not in rule_ids
    assert "alerta-blindaje-necesario" not in rule_ids


def test_alerta_coordinacion_servicios_requiere_dos_etiquetas():
    """alerta-coordinacion-servicios requiere tramo-urbano-denso + intervencion-infraestructura."""
    params = _defaults()

    # Solo urbano denso → no dispara (falta intervención).
    params.update(aba_longitud_m=150.0, acometidas_aba_n=10)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-coordinacion-servicios" not in _rule_ids_alertas(r)

    # Urbano denso + intervención → dispara.
    params["pozos_existentes_aba"] = "demolicion"
    r = generar_alertas_tecnicas(**params)
    assert "alerta-coordinacion-servicios" in _rule_ids_alertas(r)


# ---------------------------------------------------------------------------
# Metadatos de etiquetas y alertas (contrato del retorno)
# ---------------------------------------------------------------------------

def test_etiquetas_llevan_metadatos_completos():
    params = _defaults()
    params.update(desmontaje_tipo="fibrocemento")
    r = generar_alertas_tecnicas(**params)
    amianto = next(e for e in r["etiquetas"] if e["id"] == "obra-regulada-amianto")
    assert amianto["severidad"] in ("alta", "media", "baja")
    assert amianto["fuente"]     # no vacío
    assert amianto["nombre"]     # nombre humano


def test_alertas_llevan_rule_id_y_fuente():
    params = _defaults()
    params.update(aba_longitud_m=250.0, acometidas_aba_n=0)   # ABA larga sin acometidas
    r = generar_alertas_tecnicas(**params)
    alerta = next(a for a in r["alertas"] if a["rule_id"] == "alerta-aba-larga-sin-acometidas")
    assert alerta["nivel"] in ("error", "warning", "info")
    assert alerta["msg"]
    assert alerta["fuente"]
