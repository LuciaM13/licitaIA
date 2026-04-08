"""
Motor de reglas CLIPS para decisiones de elegibilidad de materiales.

Responsabilidad única: dado un conjunto de parámetros del proyecto y el
diccionario completo de precios, determinar qué items del catálogo son
elegibles para cada decisión y cuál es el mejor entre los elegibles.

Arquitectura interna:
  1. CLIPS evalúa las reglas de elegibilidad y marca candidatos.
  2. Python (desempates.py) elige el ganador entre los candidatos.

Cada llamada crea y destruye su propio clips.Environment para evitar
estado residual entre consultas.

Interfaz pública:
  resolver_decisiones(tipo, dn, red, profundidad, precios, instalacion, desmontaje)
  → dict con factor_piezas, entibacion, pozo_registro, valvuleria, desmontaje
"""

from __future__ import annotations

import logging

import clips

from src.reglas.templates import TEMPLATES, RULES, NULL_SENTINEL
from src.reglas.normalizacion import (
    FACTORES_PIEZAS,
    normalizar_tipo,
    normalizar_red,
    normalizar_instalacion,
    null_a_sentinel,
)
from src.reglas.desempates import (
    desempatar_entibacion,
    desempatar_pozo,
    ordenar_valvuleria,
    desempatar_desmontaje,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers: carga de catálogos como hechos CLIPS
# ---------------------------------------------------------------------------

def _cargar_entibacion(env: clips.Environment, precios: dict) -> list[dict]:
    catalogo = precios.get("catalogo_entibacion", [])
    tmpl = env.find_template("item-entibacion")
    for idx, item in enumerate(catalogo):
        tmpl.assert_fact(
            idx=idx,
            red=null_a_sentinel(item.get("red")),
            umbral_m=float(item.get("umbral_m", 1.5)),
        )
    return catalogo


def _cargar_pozos(env: clips.Environment, precios: dict) -> list[dict]:
    catalogo = precios.get("catalogo_pozos", [])
    tmpl = env.find_template("item-pozo")
    for idx, item in enumerate(catalogo):
        tmpl.assert_fact(
            idx=idx,
            red=null_a_sentinel(item.get("red")),
            profundidad_max=float(item["profundidad_max"]) if item.get("profundidad_max") is not None else 9999.0,
            dn_max=int(item["dn_max"]) if item.get("dn_max") is not None else 99999,
        )
    return catalogo


def _cargar_valvuleria(env: clips.Environment, precios: dict) -> list[dict]:
    catalogo = precios.get("catalogo_valvuleria", [])
    tmpl = env.find_template("item-valvuleria")
    for idx, item in enumerate(catalogo):
        if "dn_min" not in item or "dn_max" not in item:
            continue
        tmpl.assert_fact(
            idx=idx,
            dn_min=int(item["dn_min"]),
            dn_max=int(item["dn_max"]),
            instalacion=null_a_sentinel(item.get("instalacion")),
        )
    return catalogo


def _cargar_desmontaje(env: clips.Environment, precios: dict) -> list[dict]:
    catalogo = precios.get("catalogo_desmontaje", [])
    tmpl = env.find_template("item-desmontaje")
    for idx, item in enumerate(catalogo):
        tmpl.assert_fact(
            idx=idx,
            es_fibrocemento=int(item.get("es_fibrocemento", 0)),
            dn_max=int(item["dn_max"]),
        )
    return catalogo


def _recoger_candidatos(env: clips.Environment, template_name: str) -> list[int]:
    return [int(fact["idx"]) for fact in env.facts()
            if fact.template.name == template_name]


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def resolver_decisiones(
    tipo_tuberia: str,
    diametro_mm: int,
    red: str,
    profundidad: float,
    precios: dict,
    instalacion: str,
    desmontaje_tipo: str,
) -> dict:
    """
    Resuelve las decisiones de elegibilidad de materiales usando CLIPS.

    Returns:
        {
            "factor_piezas":  float,
            "entibacion":     {"necesaria": bool, "item": dict | None},
            "pozo_registro":  {"item": dict | None},
            "valvuleria":     {"items": list[dict]},
            "desmontaje":     {"item": dict | None},
        }
    """
    tipo_norm = normalizar_tipo(tipo_tuberia)
    red_norm = normalizar_red(red)
    inst_norm = normalizar_instalacion(instalacion)
    desm_norm = desmontaje_tipo.strip().lower()

    logger.info("resolver_decisiones: tipo=%s DN=%d red=%s prof=%.2f inst=%s desm=%s",
                tipo_norm, diametro_mm, red_norm, profundidad, inst_norm, desm_norm)

    # 1. Factor piezas (sin CLIPS — decisión determinista por tipo)
    factor_piezas = FACTORES_PIEZAS.get(tipo_norm, 1.0)

    # 2-5. Motor CLIPS para elegibilidad
    env = clips.Environment()
    try:
        # Construir templates y reglas
        for bloque in TEMPLATES.strip().split("\n\n"):
            bloque = bloque.strip()
            if bloque:
                env.build(bloque)
        for bloque in RULES.strip().split("\n\n"):
            bloque = bloque.strip()
            if bloque:
                env.build(bloque)

        # Cargar catálogos como hechos
        cat_entibacion = _cargar_entibacion(env, precios)
        cat_pozos = _cargar_pozos(env, precios)
        cat_valvuleria = _cargar_valvuleria(env, precios)
        cat_desmontaje = _cargar_desmontaje(env, precios)

        # Cargar hechos de entrada (parámetros del proyecto)
        env.find_template("datos-tuberia").assert_fact(
            tipo=tipo_norm, diametro_mm=diametro_mm, red=red_norm)
        env.find_template("datos-zanja").assert_fact(
            profundidad=float(profundidad), red=red_norm)
        env.find_template("datos-instalacion").assert_fact(instalacion=inst_norm)
        env.find_template("datos-desmontaje").assert_fact(tipo_desmontaje=desm_norm)

        # Ejecutar motor de inferencia (forward chaining)
        env.run()

        # Recoger candidatos elegibles
        idx_entibacion = _recoger_candidatos(env, "candidato-entibacion")
        idx_pozos = _recoger_candidatos(env, "candidato-pozo")
        idx_valvuleria = _recoger_candidatos(env, "candidato-valvuleria")
        idx_desmontaje = _recoger_candidatos(env, "candidato-desmontaje")

    finally:
        del env  # Destruir entorno para evitar estado residual

    # Desempate en Python
    entib_item = desempatar_entibacion(idx_entibacion, cat_entibacion)
    pozo_item = desempatar_pozo(idx_pozos, cat_pozos)
    valv_items = ordenar_valvuleria(idx_valvuleria, cat_valvuleria)
    desm_item = desempatar_desmontaje(idx_desmontaje, cat_desmontaje) if desm_norm != "none" else None

    return {
        "factor_piezas": factor_piezas,
        "entibacion": {
            "necesaria": entib_item is not None,
            "item": entib_item,
        },
        "pozo_registro": {
            "item": pozo_item,
        },
        "valvuleria": {
            "items": valv_items,
        },
        "desmontaje": {
            "item": desm_item,
        },
    }
