"""
Motor experto basado en CLIPSpy para decisiones de negocio EMASESA.

Este modulo extrae la logica de decision (elegibilidad) que antes estaba
embebida en src/calcular.py y la implementa como reglas CLIPS.

Arquitectura:
  - CLIPS filtra candidatos elegibles (defrule).
  - Python resuelve ranking y desempate entre candidatos.
  - Cada llamada a resolver_decisiones() crea y destruye su propio
    clips.Environment para evitar estado residual.

Decisiones manejadas:
  1. factor_piezas por tipo de tuberia
  2. Entibacion (necesaria/no, item seleccionado)
  3. Pozo de registro aplicable
  4. Valvuleria aplicable (lista de items)
  5. Desmontaje de tuberia existente
"""

from __future__ import annotations

import logging

import clips

from src.desempates import (
    desempatar_entibacion,
    desempatar_pozo,
    ordenar_valvuleria,
    desempatar_desmontaje,
)
from src.normalizacion import (
    FACTORES_PIEZAS,
    NULL_SENTINEL,
    normalizar_tipo,
    normalizar_red,
    normalizar_instalacion,
    null_to_sentinel,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Definiciones CLIPS (templates y reglas)
# ============================================================================

_TEMPLATES = """
(deftemplate datos-tuberia
  (slot tipo (type STRING))
  (slot diametro_mm (type INTEGER))
  (slot red (type STRING)))

(deftemplate datos-zanja
  (slot profundidad (type FLOAT))
  (slot red (type STRING)))

(deftemplate datos-instalacion
  (slot instalacion (type STRING)))

(deftemplate datos-desmontaje
  (slot tipo_desmontaje (type STRING)))

(deftemplate item-entibacion
  (slot idx (type INTEGER))
  (slot red (type STRING))
  (slot umbral_m (type FLOAT)))

(deftemplate item-pozo
  (slot idx (type INTEGER))
  (slot red (type STRING))
  (slot profundidad_max (type FLOAT))
  (slot dn_max (type INTEGER)))

(deftemplate item-valvuleria
  (slot idx (type INTEGER))
  (slot dn_min (type INTEGER))
  (slot dn_max (type INTEGER))
  (slot instalacion (type STRING)))

(deftemplate item-desmontaje
  (slot idx (type INTEGER))
  (slot es_fibrocemento (type INTEGER))
  (slot dn_max (type INTEGER)))

(deftemplate candidato-entibacion
  (slot idx (type INTEGER)))

(deftemplate candidato-pozo
  (slot idx (type INTEGER)))

(deftemplate candidato-valvuleria
  (slot idx (type INTEGER)))

(deftemplate candidato-desmontaje
  (slot idx (type INTEGER)))
"""

_RULES = """
; --- Entibacion: candidatos elegibles ---
; Un item de entibacion es candidato si:
;   - Su red coincide con la del proyecto, o su red es NULL (sentinel "*")
;   - La profundidad de la zanja es estrictamente mayor que su umbral
(defrule entibacion-elegible
  (datos-zanja (profundidad ?p) (red ?red-proyecto))
  (item-entibacion (idx ?i) (red ?r) (umbral_m ?u))
  (test (or (eq ?r "*") (eq ?r ?red-proyecto)))
  (test (> ?p ?u))
  =>
  (assert (candidato-entibacion (idx ?i))))

; --- Pozo de registro: candidatos elegibles ---
; Un item de pozo es candidato si:
;   - Su red coincide o es NULL
;   - profundidad < profundidad_max (o profundidad_max es sentinel 9999.0)
;   - diametro_mm <= dn_max (o dn_max es sentinel 99999)
(defrule pozo-elegible
  (datos-tuberia (diametro_mm ?dn) (red ?red-proyecto))
  (datos-zanja (profundidad ?p))
  (item-pozo (idx ?i) (red ?r) (profundidad_max ?pmax) (dn_max ?dmax))
  (test (or (eq ?r "*") (eq ?r ?red-proyecto)))
  (test (< ?p ?pmax))
  (test (<= ?dn ?dmax))
  =>
  (assert (candidato-pozo (idx ?i))))

; --- Valvuleria: candidatos elegibles ---
; Un item de valvuleria es candidato si:
;   - dn_min <= diametro_mm <= dn_max
;   - Su instalacion coincide o es NULL
(defrule valvuleria-elegible
  (datos-tuberia (diametro_mm ?dn))
  (datos-instalacion (instalacion ?inst))
  (item-valvuleria (idx ?i) (dn_min ?dmin) (dn_max ?dmax) (instalacion ?vinst))
  (test (<= ?dmin ?dn))
  (test (<= ?dn ?dmax))
  (test (or (eq ?vinst "*") (eq ?vinst ?inst)))
  =>
  (assert (candidato-valvuleria (idx ?i))))

; --- Desmontaje: candidatos elegibles ---
; Un item de desmontaje es candidato si:
;   - es_fibrocemento coincide con el tipo solicitado
;   - Para no-fibrocemento: diametro_mm <= dn_max
;   - Para fibrocemento: sin filtro de dn_max (todos aplican)
(defrule desmontaje-elegible-normal
  (datos-desmontaje (tipo_desmontaje "normal"))
  (datos-tuberia (diametro_mm ?dn))
  (item-desmontaje (idx ?i) (es_fibrocemento 0) (dn_max ?dmax))
  (test (<= ?dn ?dmax))
  =>
  (assert (candidato-desmontaje (idx ?i))))

(defrule desmontaje-elegible-fibrocemento
  (datos-desmontaje (tipo_desmontaje "fibrocemento"))
  (item-desmontaje (idx ?i) (es_fibrocemento 1))
  =>
  (assert (candidato-desmontaje (idx ?i))))
"""


# ============================================================================
# Funciones auxiliares: carga de catalogos como hechos CLIPS
# ============================================================================

def _cargar_entibacion(env: clips.Environment, precios: dict) -> list[dict]:
    """Carga items del catalogo de entibacion como hechos CLIPS.

    Retorna la lista original indexada para traduccion posterior.
    """
    catalogo = precios.get("catalogo_entibacion", [])
    tmpl = env.find_template("item-entibacion")
    for idx, item in enumerate(catalogo):
        red_val = null_to_sentinel(item.get("red"))
        umbral = float(item.get("umbral_m", 1.5))
        tmpl.assert_fact(idx=idx, red=red_val, umbral_m=umbral)
    return catalogo


def _cargar_pozos(env: clips.Environment, precios: dict) -> list[dict]:
    """Carga items del catalogo de pozos como hechos CLIPS."""
    catalogo = precios.get("catalogo_pozos", [])
    tmpl = env.find_template("item-pozo")
    for idx, item in enumerate(catalogo):
        red_val = null_to_sentinel(item.get("red"))
        prof_max = float(item["profundidad_max"]) if item.get("profundidad_max") is not None else 9999.0
        dn_max = int(item["dn_max"]) if item.get("dn_max") is not None else 99999
        tmpl.assert_fact(idx=idx, red=red_val, profundidad_max=prof_max, dn_max=dn_max)
    return catalogo


def _cargar_valvuleria(env: clips.Environment, precios: dict) -> list[dict]:
    """Carga items del catalogo de valvuleria como hechos CLIPS."""
    catalogo = precios.get("catalogo_valvuleria", [])
    tmpl = env.find_template("item-valvuleria")
    for idx, item in enumerate(catalogo):
        # Skip items sin dn_min o dn_max (mismo guard que el codigo original)
        if "dn_min" not in item or "dn_max" not in item:
            continue
        inst_val = null_to_sentinel(item.get("instalacion"))
        tmpl.assert_fact(
            idx=idx,
            dn_min=int(item["dn_min"]),
            dn_max=int(item["dn_max"]),
            instalacion=inst_val,
        )
    return catalogo


def _cargar_desmontaje(env: clips.Environment, precios: dict) -> list[dict]:
    """Carga items del catalogo de desmontaje como hechos CLIPS."""
    catalogo = precios.get("catalogo_desmontaje", [])
    tmpl = env.find_template("item-desmontaje")
    for idx, item in enumerate(catalogo):
        tmpl.assert_fact(
            idx=idx,
            es_fibrocemento=int(item.get("es_fibrocemento", 0)),
            dn_max=int(item["dn_max"]),
        )
    return catalogo


# ============================================================================
# Funciones auxiliares: lectura de candidatos y desempate en Python
# ============================================================================

def _recoger_candidatos(env: clips.Environment, template_name: str) -> list[int]:
    """Recoge todos los indices de candidatos marcados por CLIPS."""
    indices = []
    for fact in env.facts():
        if fact.template.name == template_name:
            indices.append(int(fact["idx"]))
    return indices


# ============================================================================
# API PUBLICA
# ============================================================================

def resolver_decisiones(
    tipo_tuberia: str,
    diametro_mm: int,
    red: str,
    profundidad: float,
    precios: dict,
    instalacion: str,
    desmontaje_tipo: str,
) -> dict:
    """Resuelve todas las decisiones de negocio usando el motor CLIPS.

    CLIPS determina elegibilidad (que candidatos cumplen las condiciones).
    Python resuelve ranking y desempate entre candidatos.

    Cada llamada crea y destruye su propio clips.Environment para evitar
    estado residual entre llamadas.

    Args:
        tipo_tuberia: Tipo de tuberia (FD, PE-100, Gres, etc.)
        diametro_mm: Diametro nominal en mm.
        red: Red del proyecto (ABA o SAN).
        profundidad: Profundidad de la zanja en metros.
        precios: Dict completo de precios (de cargar_todo()).
        instalacion: Tipo de instalacion de valvuleria (enterrada, pozo).
        desmontaje_tipo: Tipo de desmontaje (none, normal, fibrocemento).

    Returns:
        Dict con las decisiones:
        {
            "factor_piezas": float,
            "entibacion": {"necesaria": bool, "item": dict | None},
            "pozo_registro": {"item": dict | None},
            "valvuleria": {"items": list[dict]},
            "desmontaje": {"item": dict | None},
        }
    """
    # --- Normalizar inputs ---
    tipo_norm = normalizar_tipo(tipo_tuberia)
    red_norm = normalizar_red(red)
    inst_norm = normalizar_instalacion(instalacion)
    desmontaje_norm = desmontaje_tipo.strip().lower()

    logger.info(
        "resolver_decisiones: tipo=%s, DN=%d, red=%s, prof=%.2f, inst=%s, desm=%s",
        tipo_norm, diametro_mm, red_norm, profundidad, inst_norm, desmontaje_norm,
    )

    # --- 1. factor_piezas (decision pura, no requiere CLIPS) ---
    # NOTE: El codigo original lee factor_piezas del item dict (item.get("factor_piezas", 1.0)),
    # que ya viene calculado desde la DB. Aqui determinamos el factor por tipo de tuberia
    # como decision del motor, que es coherente con la spec. El valor almacenado en DB
    # deberia coincidir con esta tabla.
    factor_piezas = FACTORES_PIEZAS.get(tipo_norm, 1.0)
    logger.debug("factor_piezas para tipo '%s': %.2f", tipo_norm, factor_piezas)

    # --- 2-5. Crear entorno CLIPS para elegibilidad ---
    env = clips.Environment()

    try:
        # Construir templates y reglas
        for definition in _TEMPLATES.strip().split("\n\n"):
            definition = definition.strip()
            if definition:
                env.build(definition)
        for definition in _RULES.strip().split("\n\n"):
            definition = definition.strip()
            if definition:
                env.build(definition)

        # Cargar catalogos como hechos
        cat_entibacion = _cargar_entibacion(env, precios)
        cat_pozos = _cargar_pozos(env, precios)
        cat_valvuleria = _cargar_valvuleria(env, precios)
        cat_desmontaje = _cargar_desmontaje(env, precios)

        # Cargar hechos de entrada (consulta)
        tmpl_tuberia = env.find_template("datos-tuberia")
        tmpl_tuberia.assert_fact(tipo=tipo_norm, diametro_mm=diametro_mm, red=red_norm)

        tmpl_zanja = env.find_template("datos-zanja")
        tmpl_zanja.assert_fact(profundidad=float(profundidad), red=red_norm)

        tmpl_inst = env.find_template("datos-instalacion")
        tmpl_inst.assert_fact(instalacion=inst_norm)

        tmpl_desm = env.find_template("datos-desmontaje")
        tmpl_desm.assert_fact(tipo_desmontaje=desmontaje_norm)

        # Ejecutar motor de inferencia
        env.run()

        # Recoger candidatos elegibles de cada decision
        idx_entibacion = _recoger_candidatos(env, "candidato-entibacion")
        idx_pozos = _recoger_candidatos(env, "candidato-pozo")
        idx_valvuleria = _recoger_candidatos(env, "candidato-valvuleria")
        idx_desmontaje = _recoger_candidatos(env, "candidato-desmontaje")

    finally:
        # Destruir entorno CLIPS
        del env

    # --- Desempate en Python ---

    # 2. Entibacion
    entib_item = desempatar_entibacion(idx_entibacion, cat_entibacion)
    entibacion_necesaria = entib_item is not None

    # 3. Pozo de registro
    pozo_item = desempatar_pozo(idx_pozos, cat_pozos)

    # 4. Valvuleria
    valvuleria_items = ordenar_valvuleria(idx_valvuleria, cat_valvuleria)

    # 5. Desmontaje
    desmontaje_item = None
    if desmontaje_norm != "none":
        desmontaje_item = desempatar_desmontaje(idx_desmontaje, cat_desmontaje)

    resultado = {
        "factor_piezas": factor_piezas,
        "entibacion": {
            "necesaria": entibacion_necesaria,
            "item": entib_item,
        },
        "pozo_registro": {
            "item": pozo_item,
        },
        "valvuleria": {
            "items": valvuleria_items,
        },
        "desmontaje": {
            "item": desmontaje_item,
        },
    }

    logger.info(
        "Decisiones: factor=%.2f, entib=%s, pozo=%s, valv=%d items, desm=%s",
        factor_piezas,
        entibacion_necesaria,
        pozo_item.get("label", "None") if pozo_item else "None",
        len(valvuleria_items),
        desmontaje_item.get("label", "None") if desmontaje_item else "None",
    )

    return resultado
