"""
Tests del sistema experto: alertas tecnicas tras aplanado del motor CLIPS.

Excepcion justificada a la estrategia "solo AppTest" del proyecto: el motor
CLIPS es logica pura (no UI) y la verificacion de las alertas no tiene
representacion en AppTest. La demostracion del sistema experto es uno de los
argumentos centrales de la defensa del TFG, por lo que merece test pytest
directo sobre la funcion pura.

Tras el aplanado, el motor emite unicamente reglas con prefijo `alerta-` (17
reglas, todas capa 3). Las antiguas etiquetas de capa 1/2 ya no se emiten:
sus condiciones estan inlinadas en las alertas que las consumian. El campo
`r["etiquetas"]` se preserva como `[]` por compatibilidad transitoria.

Las antiguas reglas axioma R10/R11/R14 (acometidas/valvuleria sin red activa)
se retiraron al introducir el colapso de inputs en `generar_alertas_tecnicas`:
si una red esta inactiva, sus parametros se neutralizan antes de assertar el
hecho, por lo que esos axiomas defensivos quedaban inalcanzables. Los tests
`test_motor_colapsa_*` verifican ese invariante.
"""

from __future__ import annotations

import clips
import pytest

from src.sistema_experto.motor_clips import (
    _obtener_entorno_clips,
    generar_alertas_tecnicas,
)


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
        conduccion_provisional_m=0.0,
        pozos_existentes_aba="none", pozos_existentes_san="none",
        instalacion_valvuleria="enterrada",
    )


def _rule_ids_alertas(resultado: dict) -> set[str]:
    return {a["rule_id"] for a in resultado["alertas"]}


# ---------------------------------------------------------------------------
# Caso neutro: sin disparos
# ---------------------------------------------------------------------------

def test_proyecto_neutro_sin_alertas():
    r = generar_alertas_tecnicas(**_defaults())
    assert r["alertas"] == []


# ---------------------------------------------------------------------------
# Alerta de fibrocemento: condicion de amianto inlinada en la alerta.
# ---------------------------------------------------------------------------

def test_alerta_fibrocemento_requiere_amianto_y_gestion_cero():
    """La alerta dispara solo si desmontaje_tipo=fibrocemento y pct_gestion=0."""
    # Caso 1: fibrocemento + gestion 0 -> dispara
    params = _defaults()
    params.update(desmontaje_tipo="fibrocemento", pct_gestion=0.0)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-fibrocemento-sin-gestion" in _rule_ids_alertas(r)

    # Caso 2: fibrocemento + gestion 2% -> no dispara la alerta
    params["pct_gestion"] = 0.02
    r = generar_alertas_tecnicas(**params)
    assert "alerta-fibrocemento-sin-gestion" not in _rule_ids_alertas(r)


def test_alertas_seguridad_separadas_por_umbral():
    """Por debajo de 2% S&S dispara critica. Entre 2% y 3% dispara blindaje."""
    base = _defaults()
    base.update(aba_profundidad_m=4.0)   # condicion zanja profunda inlinada

    # S&S 1.5% -> critica, sin blindaje.
    r = generar_alertas_tecnicas(**{**base, "pct_seguridad": 0.015})
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-seguridad-critica" in rule_ids
    assert "alerta-blindaje-necesario" not in rule_ids

    # S&S 2.5% -> blindaje, sin critica.
    r = generar_alertas_tecnicas(**{**base, "pct_seguridad": 0.025})
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-blindaje-necesario" in rule_ids
    assert "alerta-seguridad-critica" not in rule_ids

    # S&S 3.5% -> ninguna de las dos.
    r = generar_alertas_tecnicas(**{**base, "pct_seguridad": 0.035})
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-seguridad-critica" not in rule_ids
    assert "alerta-blindaje-necesario" not in rule_ids




# ---------------------------------------------------------------------------
# Boundary del umbral inlinado de zanja profunda (3.5 m) en alertas de S&S.
# Tras el aplanado, la condicion `prof > 3.5` esta inlinada en
# alerta-seguridad-critica y alerta-blindaje-necesario; comprobamos boundary
# sobre la alerta directamente.
# ---------------------------------------------------------------------------

def test_alerta_seguridad_critica_dispara_a_4m():
    """Con prof > 3.5 m y pct_seguridad=0.01 (<2%), la alerta critica dispara."""
    params = _defaults()
    params.update(aba_profundidad_m=4.0, pct_seguridad=0.01)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-seguridad-critica" in _rule_ids_alertas(r)


def test_alerta_seguridad_critica_no_dispara_a_3_4m():
    """Con prof por debajo del umbral inlinado (3.4 m), la alerta critica no dispara."""
    params = _defaults()
    params.update(aba_profundidad_m=3.4, pct_seguridad=0.01)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-seguridad-critica" not in _rule_ids_alertas(r)


# ---------------------------------------------------------------------------
# Metadatos de alertas (contrato del retorno)
# ---------------------------------------------------------------------------

def test_alertas_llevan_rule_id_y_fuente():
    params = _defaults()
    params.update(aba_longitud_m=250.0, acometidas_aba_n=0)   # ABA larga sin acometidas
    r = generar_alertas_tecnicas(**params)
    alerta = next(a for a in r["alertas"] if a["rule_id"] == "alerta-aba-larga-sin-acometidas")
    assert alerta["nivel"] in ("error", "warning", "info")
    assert alerta["msg"]
    assert alerta["fuente"]


# ---------------------------------------------------------------------------
# Reglas de enriquecimiento (15 reglas validadas con literatura y datos
# EMASESA reales) - verificacion de disparo sobre la alerta directamente.
# ---------------------------------------------------------------------------

# R1: profundidad ABA fuera del rango habitual del catalogo EMASESA [0.6, 6.0]

def test_prof_aba_fuera_rango_dispara_por_debajo():
    params = _defaults()
    params["aba_profundidad_m"] = 0.5
    r = generar_alertas_tecnicas(**params)
    assert "prof-aba-fuera-rango-catalogo" in _rule_ids_alertas(r)


def test_prof_aba_fuera_rango_dispara_por_encima():
    params = _defaults()
    params["aba_profundidad_m"] = 6.5
    r = generar_alertas_tecnicas(**params)
    assert "prof-aba-fuera-rango-catalogo" in _rule_ids_alertas(r)


def test_prof_aba_fuera_rango_no_dispara_dentro():
    """En el rango valido (0.6 <= p <= 6.0) la alerta no debe sonar."""
    params = _defaults()
    params["aba_profundidad_m"] = 1.5
    r = generar_alertas_tecnicas(**params)
    assert "prof-aba-fuera-rango-catalogo" not in _rule_ids_alertas(r)


# R2: profundidad SAN fuera de [1.0, 6.0]

def test_prof_san_fuera_rango_dispara_por_debajo():
    params = _defaults()
    params.update(san_activa=True, san_profundidad_m=0.8)
    r = generar_alertas_tecnicas(**params)
    assert "prof-san-fuera-rango-catalogo" in _rule_ids_alertas(r)


def test_prof_san_fuera_rango_no_dispara_san_inactiva():
    """Si SAN no esta activa, la regla no se evalua aunque profundidad sea baja."""
    params = _defaults()
    params.update(san_activa=False, san_profundidad_m=0.0)
    r = generar_alertas_tecnicas(**params)
    assert "prof-san-fuera-rango-catalogo" not in _rule_ids_alertas(r)


# Pozos profundos sin escala: condicion de saneamiento profundo inlinada.

def test_alerta_pozos_profundos_sin_escala_dispara():
    """Con san_activa, prof > 4.0 m y pozos_existentes_san parcial -> dispara."""
    params = _defaults()
    params.update(
        san_activa=True, san_profundidad_m=4.5,
        pozos_existentes_san="parcial",
    )
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pozos-profundos-sin-escala" in _rule_ids_alertas(r)


def test_alerta_pozos_profundos_no_dispara_sin_pozos():
    """Misma profundidad pero sin pozos existentes -> no dispara."""
    params = _defaults()
    params.update(
        san_activa=True, san_profundidad_m=4.5,
        pozos_existentes_san="none",
    )
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pozos-profundos-sin-escala" not in _rule_ids_alertas(r)


def test_alerta_pozos_profundos_no_dispara_san_somera():
    """Con pozos pero san_profundidad_m por debajo de 4.0 -> no dispara."""
    params = _defaults()
    params.update(
        san_activa=True, san_profundidad_m=2.0,
        pozos_existentes_san="parcial",
    )
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pozos-profundos-sin-escala" not in _rule_ids_alertas(r)


# R6: FD de gran diametro

def test_alerta_fd_dn_grande_empuje_dispara():
    params = _defaults()
    params.update(aba_tipo_tuberia="FD", aba_diametro_mm=500)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-fd-dn-grande-empuje" in _rule_ids_alertas(r)


def test_alerta_fd_dn_grande_no_dispara_pe():
    """Mismo DN pero material PE no dispara la alerta de empuje."""
    params = _defaults()
    params.update(aba_tipo_tuberia="PE-100", aba_diametro_mm=500)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-fd-dn-grande-empuje" not in _rule_ids_alertas(r)


# R7: PE pequeño DN

def test_alerta_pe_dn_pequeno_dispara():
    params = _defaults()
    params.update(aba_tipo_tuberia="PE-100", aba_diametro_mm=90)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pe-dn-pequeno-presion" in _rule_ids_alertas(r)


def test_alerta_pe_dn_pequeno_no_dispara_dn_grande():
    params = _defaults()
    params.update(aba_tipo_tuberia="PE-100", aba_diametro_mm=160)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pe-dn-pequeno-presion" not in _rule_ids_alertas(r)


# R8: densidad de acometidas anomala

def test_alerta_densidad_acometidas_dispara():
    """Ratio > 0.30 ud/m: 35 acometidas en 100 m = 0.35."""
    params = _defaults()
    params.update(aba_longitud_m=100.0, acometidas_aba_n=35)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-densidad-acometidas-anomala" in _rule_ids_alertas(r)


def test_alerta_densidad_acometidas_no_dispara_normal():
    """Ratio tipico EMASESA 0.04-0.16 no debe disparar."""
    params = _defaults()
    params.update(aba_longitud_m=100.0, acometidas_aba_n=10)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-densidad-acometidas-anomala" not in _rule_ids_alertas(r)


# R9: trafico sin conduccion provisional (condicion de tramo urbano denso inlinada)

def test_alerta_trafico_sin_conduccion_provisional_dispara():
    params = _defaults()
    params.update(
        aba_longitud_m=150.0, acometidas_aba_n=8,
        conduccion_provisional_m=0.0,
    )
    r = generar_alertas_tecnicas(**params)
    assert "alerta-trafico-sin-conduccion-provisional" in _rule_ids_alertas(r)


def test_alerta_trafico_no_dispara_si_hay_conduccion():
    params = _defaults()
    params.update(
        aba_longitud_m=150.0, acometidas_aba_n=8,
        conduccion_provisional_m=120.0,
    )
    r = generar_alertas_tecnicas(**params)
    assert "alerta-trafico-sin-conduccion-provisional" not in _rule_ids_alertas(r)


# R12: pct_seguridad fuera de [0.01, 0.10]

def test_alerta_pct_seguridad_dispara_por_debajo():
    params = _defaults()
    params["pct_seguridad"] = 0.005
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pct-seguridad-rango-anomalo" in _rule_ids_alertas(r)


def test_alerta_pct_seguridad_dispara_por_encima():
    params = _defaults()
    params["pct_seguridad"] = 0.15
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pct-seguridad-rango-anomalo" in _rule_ids_alertas(r)


def test_alerta_pct_seguridad_no_dispara_dentro():
    params = _defaults()
    params["pct_seguridad"] = 0.04
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pct-seguridad-rango-anomalo" not in _rule_ids_alertas(r)


# R13: pct_gestion fuera de [0.005, 0.11]

def test_alerta_pct_gestion_dispara_por_encima():
    """EMASESA real max 10.13%; > 11% es anomalo."""
    params = _defaults()
    params["pct_gestion"] = 0.13
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pct-gestion-rango-anomalo" in _rule_ids_alertas(r)


def test_alerta_pct_gestion_no_dispara_alto_normal_emasesa():
    """En el corpus EMASESA real la mediana es 7.81% - debe estar dentro del rango."""
    params = _defaults()
    params["pct_gestion"] = 0.078
    r = generar_alertas_tecnicas(**params)
    assert "alerta-pct-gestion-rango-anomalo" not in _rule_ids_alertas(r)


# R15: amianto + S&S < 4% (condicion de amianto inlinada en la alerta)

def test_alerta_amianto_sin_margen_seguridad_dispara():
    params = _defaults()
    params.update(desmontaje_tipo="fibrocemento", pct_seguridad=0.03)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-amianto-sin-margen-seguridad" in _rule_ids_alertas(r)


def test_alerta_amianto_no_dispara_sin_amianto():
    """Sin fibrocemento, S&S=0.03 no dispara esta regla especifica
    (si podria disparar otras como rango anomalo)."""
    params = _defaults()
    params.update(desmontaje_tipo="none", pct_seguridad=0.03)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-amianto-sin-margen-seguridad" not in _rule_ids_alertas(r)


def test_alerta_amianto_no_dispara_con_margen_suficiente():
    params = _defaults()
    params.update(desmontaje_tipo="fibrocemento", pct_seguridad=0.05)
    r = generar_alertas_tecnicas(**params)
    assert "alerta-amianto-sin-margen-seguridad" not in _rule_ids_alertas(r)


# ---------------------------------------------------------------------------
# Sad-path del motor: error al construir el entorno CLIPS
# ---------------------------------------------------------------------------
# El motor cachea una unica instancia de ``clips.Environment`` con
# ``functools.lru_cache``. Si la construccion de plantillas/reglas falla,
# la excepcion nativa de CLIPS debe propagarse al llamador (no se envuelve
# en una excepcion del proyecto: no existe ``MotorExpertoError`` en la
# convencion actual). Limpiamos el cache antes y despues para no contaminar
# el resto de la suite.

def test_build_falla_propaga_clipserror(monkeypatch):
    """Si ``env.build`` lanza ``CLIPSError`` durante la inicializacion del
    entorno cacheado, la excepcion debe propagarse desde la funcion publica.
    """
    _obtener_entorno_clips.cache_clear()
    try:
        build_original = clips.Environment.build
        llamadas = {"n": 0}

        def build_que_falla(self, construct):
            llamadas["n"] += 1
            if llamadas["n"] == 1:
                # CLIPSError requiere (env, message). Pasamos None como env y
                # un mensaje explicito para evitar lookups internos del router.
                raise clips.CLIPSError(None, message="fallo simulado en build")
            return build_original(self, construct)

        monkeypatch.setattr(clips.Environment, "build", build_que_falla)

        with pytest.raises(clips.CLIPSError):
            generar_alertas_tecnicas(
                aba_activa=True, san_activa=False,
                aba_longitud_m=50.0, aba_profundidad_m=1.5, san_profundidad_m=0.0,
                aba_diametro_mm=200, san_diametro_mm=0, aba_tipo_tuberia="PE-100",
                acometidas_aba_n=2, acometidas_san_n=0,
                desmontaje_tipo="none",
                pct_seguridad=0.04, pct_gestion=0.02,
                conduccion_provisional_m=0.0,
                pozos_existentes_aba="none", pozos_existentes_san="none",
                instalacion_valvuleria="enterrada",
            )
    finally:
        # Aseguramos que ningun cache envenenado se filtre a otros tests.
        _obtener_entorno_clips.cache_clear()


# ---------------------------------------------------------------------------
# Meta-alerta: encadenamiento real (lee otras alertas, no datos-proyecto).
# Topologia DNF:
#   Grupo 1 (OR): alerta-seguridad-critica OR alerta-blindaje-necesario
#   AND
#   Grupo 2 (OR): alerta-trafico-sin-conduccion-provisional
#                 OR alerta-fibrocemento-sin-gestion
#                 OR alerta-amianto-sin-margen-seguridad
# ---------------------------------------------------------------------------

def test_alerta_meta_dispara_con_seguridad_critica_y_amianto():
    """Meta encadena: seguridad-critica AND amianto-sin-margen-seguridad."""
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=4.0,  # zanja compleja
        pct_seguridad=0.01,                       # critica (< 0.02) + amianto-sin-margen (< 0.04)
        desmontaje_tipo="fibrocemento",
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-seguridad-critica" in rule_ids
    assert "alerta-amianto-sin-margen-seguridad" in rule_ids
    assert "alerta-meta-proyecto-alto-riesgo" in rule_ids


def test_alerta_meta_dispara_con_blindaje_y_trafico():
    """Meta encadena: blindaje-necesario AND trafico-sin-conduccion-provisional."""
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=4.0,    # zanja compleja
        pct_seguridad=0.025,                        # blindaje (entre 0.02 y 0.03)
        aba_longitud_m=150.0, acometidas_aba_n=10,  # tramo urbano denso
        conduccion_provisional_m=0.0,               # sin conduccion -> trafico
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-blindaje-necesario" in rule_ids
    assert "alerta-trafico-sin-conduccion-provisional" in rule_ids
    assert "alerta-meta-proyecto-alto-riesgo" in rule_ids


def test_alerta_meta_no_dispara_solo_seguridad_critica():
    """Solo cumple Grupo 1 del DNF: meta no debe dispararse."""
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=4.0,
        pct_seguridad=0.01,
        # SIN amianto, SIN tramo urbano denso, CON conduccion provisional
        conduccion_provisional_m=10.0,
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-seguridad-critica" in rule_ids
    assert "alerta-meta-proyecto-alto-riesgo" not in rule_ids


def test_alerta_meta_no_dispara_solo_fibrocemento():
    """Solo cumple Grupo 2 del DNF: meta no debe dispararse."""
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=2.0,    # NO zanja compleja
        pct_seguridad=0.05,                         # ni critica ni blindaje
        desmontaje_tipo="fibrocemento",
        pct_gestion=0.0,                            # fibrocemento-sin-gestion
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-fibrocemento-sin-gestion" in rule_ids
    assert "alerta-meta-proyecto-alto-riesgo" not in rule_ids


def test_alerta_meta_no_dispara_proyecto_neutro():
    """Sin disparos base, meta no se dispara."""
    params = _defaults()
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    assert "alerta-meta-proyecto-alto-riesgo" not in rule_ids


def test_alerta_meta_dispara_con_r1_y_solo_amianto_sin_urbano():
    """Meta dispara con ?r1 (geometrico) AND ?r3 (amianto), SIN ?r2 (urbano).

    Verifica que el subconjunto urbano denso no es necesario: basta con
    cualquiera de los dos alternativos (?r2 OR ?r3).
    """
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=4.0,    # ?r1: zanja profunda
        pct_seguridad=0.025,                        # ?r1: blindaje (2-3%)
        desmontaje_tipo="fibrocemento",             # ?r3: amianto
        pct_gestion=0.0,                            # ?r3: fibrocemento-sin-gestion
        # NO tramo urbano denso (longitud y acometidas dejan ?r2 sin disparar).
        aba_longitud_m=50.0, acometidas_aba_n=2,
        conduccion_provisional_m=10.0,              # garantiza no trafico-sin-conduccion
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    # ?r1 disparado:
    assert "alerta-blindaje-necesario" in rule_ids
    # ?r3 disparado:
    assert "alerta-fibrocemento-sin-gestion" in rule_ids
    # ?r2 NO disparado:
    assert "alerta-trafico-sin-conduccion-provisional" not in rule_ids
    # Meta dispara igualmente:
    assert "alerta-meta-proyecto-alto-riesgo" in rule_ids


def test_alerta_meta_dispara_con_r1_y_solo_urbano_sin_amianto():
    """Meta dispara con ?r1 (geometrico) AND ?r2 (urbano), SIN ?r3 (amianto).

    Verifica el simetrico: basta con que dispare urbano denso, sin amianto.
    """
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=4.0,     # ?r1: zanja profunda
        pct_seguridad=0.025,                         # ?r1: blindaje (2-3%)
        aba_longitud_m=150.0, acometidas_aba_n=10,   # ?r2: tramo urbano denso
        conduccion_provisional_m=0.0,                # ?r2: trafico-sin-conduccion
        desmontaje_tipo="none",                      # NO amianto
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    # ?r1 disparado:
    assert "alerta-blindaje-necesario" in rule_ids
    # ?r2 disparado:
    assert "alerta-trafico-sin-conduccion-provisional" in rule_ids
    # ?r3 NO disparado:
    assert "alerta-fibrocemento-sin-gestion" not in rule_ids
    assert "alerta-amianto-sin-margen-seguridad" not in rule_ids
    # Meta dispara igualmente:
    assert "alerta-meta-proyecto-alto-riesgo" in rule_ids


def test_alerta_meta_no_dispara_solo_subconjuntos_alternativos():
    """Solo ?r2 (urbano) + ?r3 (amianto) sin ?r1 (geometrico): meta no dispara.

    El subconjunto ?r1 es obligatorio: sin zanja profunda + S&S bajo, no hay
    metaregla aunque coincidan los dos alternativos.
    """
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=2.0,     # NO zanja profunda
        pct_seguridad=0.05,                          # NO bandas de ?r1
        aba_longitud_m=150.0, acometidas_aba_n=10,   # ?r2: urbano denso
        conduccion_provisional_m=0.0,                # ?r2: trafico-sin-conduccion
        desmontaje_tipo="fibrocemento",              # ?r3: amianto
        pct_gestion=0.0,                             # ?r3: fibrocemento-sin-gestion
    )
    r = generar_alertas_tecnicas(**params)
    rule_ids = _rule_ids_alertas(r)
    # ?r2 y ?r3 disparados:
    assert "alerta-trafico-sin-conduccion-provisional" in rule_ids
    assert "alerta-fibrocemento-sin-gestion" in rule_ids
    # ?r1 NO disparado:
    assert "alerta-seguridad-critica" not in rule_ids
    assert "alerta-blindaje-necesario" not in rule_ids
    # Meta NO dispara (falta el obligatorio ?r1):
    assert "alerta-meta-proyecto-alto-riesgo" not in rule_ids


def test_cadena_inferencia_meta_documenta_encadenamiento():
    """Cuando la meta dispara, la cadena_inferencia contiene >=3 items con
    los rule_id correctos y el item de la meta cita las alertas que la activaron."""
    params = _defaults()
    params.update(
        aba_activa=True, aba_profundidad_m=4.0,
        pct_seguridad=0.01,
        desmontaje_tipo="fibrocemento",
    )
    r = generar_alertas_tecnicas(**params)
    cadena = r["cadena_inferencia"]
    rule_ids_cadena = {item["rule_id"] for item in cadena}
    assert "alerta-seguridad-critica" in rule_ids_cadena
    assert "alerta-amianto-sin-margen-seguridad" in rule_ids_cadena
    assert "alerta-meta-proyecto-alto-riesgo" in rule_ids_cadena
    assert len(cadena) >= 3

    meta_item = next(it for it in cadena if it["rule_id"] == "alerta-meta-proyecto-alto-riesgo")
    assert meta_item["nivel"] == "alerta"
    # La meta debe explicitar la combinacion DNF de alertas previas:
    assert "Apoyada en alertas" in meta_item["texto"]
    # Una alerta de Grupo 1 debe aparecer como activa:
    assert ("alerta-seguridad-critica" in meta_item["texto"]
            or "alerta-blindaje-necesario" in meta_item["texto"])


# ---------------------------------------------------------------------------
# Invariante de colapsacion (sustituye a los antiguos axiomas R10/R11/R14)
# ---------------------------------------------------------------------------

def test_motor_colapsa_aba_inactiva():
    """Con aba_activa=False, los parametros ABA 'sucios' se neutralizan en el
    motor y no provocan alertas dependientes de ABA. Esto reemplaza al antiguo
    axioma alerta-valvuleria-sin-red-aba y bloquea la regresion del falso
    positivo de densidad en modo SAN-only detectado el 2026-05-23."""
    params = _defaults()
    params.update(
        aba_activa=False,
        aba_longitud_m=999.0, aba_profundidad_m=5.0, aba_diametro_mm=500,
        aba_tipo_tuberia="FD",
        acometidas_aba_n=99, acometidas_san_n=99,
        instalacion_valvuleria="enterrada",
        pozos_existentes_aba="demolicion",
    )
    r = generar_alertas_tecnicas(**params)
    rules = _rule_ids_alertas(r)
    # Reglas dependientes de ABA que NO deben dispararse pese a inputs sucios:
    assert "alerta-densidad-acometidas-anomala" not in rules
    assert "alerta-aba-larga-sin-acometidas" not in rules
    assert "alerta-fd-dn-grande-empuje" not in rules
    assert "alerta-prof-aba-fuera-rango-catalogo" not in rules
    assert "alerta-valvuleria-aproximada" not in rules


def test_motor_colapsa_san_inactiva():
    """Con san_activa=False, los parametros SAN 'sucios' se neutralizan."""
    params = _defaults()
    params.update(
        san_activa=False,
        san_profundidad_m=5.0, san_diametro_mm=500,
        acometidas_san_n=99,
        pozos_existentes_san="demolicion",
    )
    r = generar_alertas_tecnicas(**params)
    rules = _rule_ids_alertas(r)
    assert "alerta-prof-san-fuera-rango-catalogo" not in rules
    assert "alerta-pozos-profundos-sin-escala" not in rules
    # Densidad usa aba_longitud=50 (defaults) y aba activa: la suma
    # acometidas_aba+acometidas_san debe basarse en acometidas_san colapsado
    # a 0, por lo que solo cuenta acometidas_aba=2 → ratio 2/50=0.04, no dispara.
    assert "alerta-densidad-acometidas-anomala" not in rules
