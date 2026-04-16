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

from src.reglas.templates import TEMPLATES, RULES, NULL_SENTINEL, TEMPLATES_ALERTAS, RULES_ALERTAS
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
from src.reglas.trazabilidad import generar_trazabilidad

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers: carga de catálogos como hechos CLIPS
# ---------------------------------------------------------------------------

def _cargar_entibacion(env: clips.Environment, precios: dict) -> list[dict]:
    catalogo = precios.get("catalogo_entibacion", [])
    if not catalogo:
        logger.warning("[CLIPS] Catálogo de entibación vacío")
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
    if not catalogo:
        logger.warning("[CLIPS] Catálogo de pozos vacío")
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
    if not catalogo:
        logger.warning("[CLIPS] Catálogo de valvulería vacío")
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
    if not catalogo:
        logger.warning("[CLIPS] Catálogo de desmontaje vacío")
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


def _buscar_ganador_idx(item: dict | None, catalogo: list[dict]) -> int | None:
    """Devuelve el índice del item ganador en el catálogo, o None."""
    if item is None:
        return None
    label = item.get("label")
    for i, cat_item in enumerate(catalogo):
        if cat_item.get("label") == label:
            return i
    return None


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
            "trazabilidad":   list[str],  # Explicaciones en lenguaje natural
        }
    """
    tipo_norm = normalizar_tipo(tipo_tuberia)
    red_norm = normalizar_red(red)
    inst_norm = normalizar_instalacion(instalacion)
    desm_norm = desmontaje_tipo.strip().lower()

    logger.info("resolver_decisiones: tipo=%s DN=%d red=%s prof=%.2f inst=%s desm=%s",
                tipo_norm, diametro_mm, red_norm, profundidad, inst_norm, desm_norm)

    # 1. Factor piezas (sin CLIPS - decisión determinista por tipo)
    factor_piezas = FACTORES_PIEZAS.get(tipo_norm, 1.0)
    logger.debug("  factor_piezas(%s) = %.2f", tipo_norm, factor_piezas)

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
        logger.debug("  Catálogos cargados: entib=%d pozos=%d valv=%d desm=%d",
                     len(cat_entibacion), len(cat_pozos), len(cat_valvuleria), len(cat_desmontaje))

        # Cargar hechos de entrada (parámetros del proyecto)
        env.find_template("datos-tuberia").assert_fact(
            tipo=tipo_norm, diametro_mm=diametro_mm, red=red_norm)
        env.find_template("datos-zanja").assert_fact(
            profundidad=float(profundidad), red=red_norm)
        env.find_template("datos-instalacion").assert_fact(instalacion=inst_norm)
        env.find_template("datos-desmontaje").assert_fact(tipo_desmontaje=desm_norm)
        logger.debug("  Hechos entrada CLIPS: tuberia(tipo=%s DN=%d red=%s) "
                     "zanja(prof=%.2f red=%s) inst=%s desm=%s",
                     tipo_norm, diametro_mm, red_norm, profundidad, red_norm,
                     inst_norm, desm_norm)

        # Snapshot de hechos pre-run (catálogos cargados)
        n_hechos_pre = sum(1 for _ in env.facts())
        logger.debug("  Hechos totales pre-run: %d", n_hechos_pre)

        # Ejecutar motor de inferencia (forward chaining)
        n_fired = env.run()
        logger.debug("  CLIPS run() → %d reglas disparadas", n_fired)

        # Recoger candidatos elegibles
        idx_entibacion = _recoger_candidatos(env, "candidato-entibacion")
        idx_pozos = _recoger_candidatos(env, "candidato-pozo")
        idx_valvuleria = _recoger_candidatos(env, "candidato-valvuleria")
        idx_desmontaje = _recoger_candidatos(env, "candidato-desmontaje")
        logger.debug("  Candidatos CLIPS: entib=%s pozos=%s valv=%s desm=%s",
                     idx_entibacion, idx_pozos, idx_valvuleria, idx_desmontaje)

        # Log detallado de cada candidato para trazabilidad
        for i in idx_entibacion:
            it = cat_entibacion[i]
            logger.debug("    entib[%d]: red=%s umbral=%.2f label=%s",
                         i, it.get("red"), it.get("umbral_m", 0), it.get("label", "?"))
        for i in idx_pozos:
            it = cat_pozos[i]
            logger.debug("    pozo[%d]: red=%s p_max=%s dn_max=%s label=%s",
                         i, it.get("red"), it.get("profundidad_max", "∞"),
                         it.get("dn_max", "∞"), it.get("label", "?"))
        for i in idx_valvuleria:
            it = cat_valvuleria[i]
            logger.debug("    valv[%d]: dn_min=%d dn_max=%d inst=%s label=%s",
                         i, it.get("dn_min", 0), it.get("dn_max", 0),
                         it.get("instalacion", "?"), it.get("label", "?"))
        for i in idx_desmontaje:
            it = cat_desmontaje[i]
            logger.debug("    desm[%d]: es_fibro=%d dn_max=%d label=%s",
                         i, it.get("es_fibrocemento", 0),
                         it.get("dn_max", 0), it.get("label", "?"))

    finally:
        del env  # Destruir entorno para evitar estado residual

    # Desempate en Python
    entib_item = desempatar_entibacion(idx_entibacion, cat_entibacion)
    pozo_item = desempatar_pozo(idx_pozos, cat_pozos)
    valv_items = ordenar_valvuleria(idx_valvuleria, cat_valvuleria)
    desm_item = desempatar_desmontaje(idx_desmontaje, cat_desmontaje) if desm_norm != "none" else None
    logger.debug("  Desempate → entib=%s pozo=%s valv=%d desm=%s",
                 entib_item["label"] if entib_item else None,
                 pozo_item["label"] if pozo_item else None,
                 len(valv_items),
                 desm_item["label"] if desm_item else None)

    # Trazabilidad: explicaciones en lenguaje natural de cada decisión
    trazabilidad = generar_trazabilidad(
        red=red_norm,
        diametro_mm=diametro_mm,
        profundidad=profundidad,
        instalacion=inst_norm,
        desmontaje_tipo=desm_norm,
        cat_entibacion=cat_entibacion,
        idx_entibacion=idx_entibacion,
        item_entibacion=entib_item,
        idx_pozos=idx_pozos,
        item_pozo=pozo_item,
        items_valvuleria=valv_items,
        idx_desmontaje=idx_desmontaje,
        item_desmontaje=desm_item,
    )

    # Datos de candidatos para UI semi-automática
    _valv_labels_ganadores = {it.get("label") for it in valv_items}
    valv_ganadores_idx = [
        i for i in idx_valvuleria
        if cat_valvuleria[i].get("label") in _valv_labels_ganadores
    ]

    candidatos = {
        "entibacion": {
            "catalogo": cat_entibacion,
            "elegibles_idx": idx_entibacion,
            "ganador_idx": _buscar_ganador_idx(entib_item, cat_entibacion),
        },
        "pozo_registro": {
            "catalogo": cat_pozos,
            "elegibles_idx": idx_pozos,
            "ganador_idx": _buscar_ganador_idx(pozo_item, cat_pozos),
        },
        "valvuleria": {
            "catalogo": cat_valvuleria,
            "elegibles_idx": idx_valvuleria,
            "ganadores_idx": valv_ganadores_idx,
        },
        "desmontaje": {
            "catalogo": cat_desmontaje,
            "elegibles_idx": idx_desmontaje,
            "ganador_idx": _buscar_ganador_idx(desm_item, cat_desmontaje),
        },
    }

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
        "trazabilidad": trazabilidad,
        "candidatos": candidatos,
    }


# ---------------------------------------------------------------------------
# Alertas de validación técnica (CLIPS)
# ---------------------------------------------------------------------------

def evaluar_alertas(
    aba_activa: bool,
    san_activa: bool,
    aba_longitud_m: float,
    aba_profundidad_m: float,
    san_profundidad_m: float,
    acometidas_aba_n: int,
    desmontaje_tipo: str,
    pct_seguridad: float,
    pct_gestion: float,
) -> list[dict]:
    """
    Ejecuta las reglas de alerta CLIPS sobre los parámetros del proyecto.

    Returns:
        Lista de dicts con {"nivel": "error"|"warning"|"info", "msg": str}
    """
    env = clips.Environment()
    try:
        for bloque in TEMPLATES_ALERTAS.strip().split("\n\n"):
            bloque = bloque.strip()
            if bloque:
                env.build(bloque)
        for bloque in RULES_ALERTAS.strip().split("\n\n"):
            bloque = bloque.strip()
            if bloque:
                env.build(bloque)

        env.find_template("datos-proyecto").assert_fact(
            aba_activa=1 if aba_activa else 0,
            san_activa=1 if san_activa else 0,
            aba_longitud_m=float(aba_longitud_m),
            aba_profundidad_m=float(aba_profundidad_m),
            san_profundidad_m=float(san_profundidad_m),
            acometidas_aba_n=int(acometidas_aba_n),
            desmontaje_tipo=desmontaje_tipo.strip().lower(),
            pct_seguridad=float(pct_seguridad),
            pct_gestion=float(pct_gestion),
        )

        n_fired = env.run()
        logger.debug("[ALERTAS] CLIPS run() → %d reglas disparadas", n_fired)

        alertas = []
        for fact in env.facts():
            if fact.template.name == "alerta":
                alertas.append({
                    "nivel": str(fact["nivel"]),
                    "msg": str(fact["msg"]),
                })

        return alertas
    finally:
        del env


# ---------------------------------------------------------------------------
# Pre-evaluación Python pura (sin CLIPS) para UI reactiva inline
# ---------------------------------------------------------------------------

def _red_coincide(item_red: str | None, red: str) -> bool:
    """True si la red del item coincide con la red del proyecto o es wildcard."""
    if item_red is None or item_red == NULL_SENTINEL:
        return True
    return str(item_red).strip().upper() == red.strip().upper()


def _inst_coincide(item_inst: str | None, instalacion: str) -> bool:
    """True si la instalación del item coincide o es wildcard."""
    if item_inst is None or item_inst == NULL_SENTINEL:
        return True
    return str(item_inst).strip().lower() == instalacion.strip().lower()


def preevaluar_materiales(
    tipo_tuberia: str,
    diametro_mm: int,
    red: str,
    profundidad: float,
    precios: dict,
    instalacion: str,
    desmontaje_tipo: str,
) -> dict:
    """
    Evaluación rápida de materiales en Python puro (sin CLIPS).

    Replica la misma lógica de elegibilidad y desempate que resolver_decisiones()
    pero sin instanciar un clips.Environment, para uso reactivo en la UI.

    Returns: misma estructura que resolver_decisiones().
    """
    tipo_norm = normalizar_tipo(tipo_tuberia)
    red_norm = normalizar_red(red)
    inst_norm = normalizar_instalacion(instalacion)
    desm_norm = desmontaje_tipo.strip().lower()

    factor_piezas = FACTORES_PIEZAS.get(tipo_norm, 1.0)

    # Cargar catálogos
    cat_entibacion = precios.get("catalogo_entibacion", [])
    cat_pozos = precios.get("catalogo_pozos", [])
    cat_valvuleria = precios.get("catalogo_valvuleria", [])
    cat_desmontaje = precios.get("catalogo_desmontaje", [])

    # Elegibilidad: mismas reglas que templates.py pero en Python
    idx_entibacion = [
        i for i, it in enumerate(cat_entibacion)
        if _red_coincide(it.get("red"), red_norm)
        and profundidad >= float(it.get("umbral_m", 1.5))
    ]

    idx_pozos = [
        i for i, it in enumerate(cat_pozos)
        if _red_coincide(it.get("red"), red_norm)
        and profundidad <= (float(it["profundidad_max"]) if it.get("profundidad_max") is not None else 9999.0)
        and diametro_mm <= (int(it["dn_max"]) if it.get("dn_max") is not None else 99999)
    ]

    idx_valvuleria = [
        i for i, it in enumerate(cat_valvuleria)
        if "dn_min" in it and "dn_max" in it
        and int(it["dn_min"]) <= diametro_mm <= int(it["dn_max"])
        and _inst_coincide(it.get("instalacion"), inst_norm)
    ]

    idx_desmontaje = []
    if desm_norm == "normal":
        idx_desmontaje = [
            i for i, it in enumerate(cat_desmontaje)
            if not int(it.get("es_fibrocemento", 0))
            and diametro_mm <= int(it.get("dn_max", 0))
        ]
    elif desm_norm == "fibrocemento":
        idx_desmontaje = [
            i for i, it in enumerate(cat_desmontaje)
            if int(it.get("es_fibrocemento", 0))
        ]

    # Desempate (reutiliza funciones Python existentes)
    entib_item = desempatar_entibacion(idx_entibacion, cat_entibacion)
    pozo_item = desempatar_pozo(idx_pozos, cat_pozos)
    valv_items = ordenar_valvuleria(idx_valvuleria, cat_valvuleria)
    desm_item = desempatar_desmontaje(idx_desmontaje, cat_desmontaje) if desm_norm != "none" else None

    # Trazabilidad
    trazabilidad = generar_trazabilidad(
        red=red_norm,
        diametro_mm=diametro_mm,
        profundidad=profundidad,
        instalacion=inst_norm,
        desmontaje_tipo=desm_norm,
        cat_entibacion=cat_entibacion,
        idx_entibacion=idx_entibacion,
        item_entibacion=entib_item,
        idx_pozos=idx_pozos,
        item_pozo=pozo_item,
        items_valvuleria=valv_items,
        idx_desmontaje=idx_desmontaje,
        item_desmontaje=desm_item,
    )

    # Candidatos para UI
    _valv_labels_ganadores = {it.get("label") for it in valv_items}
    valv_ganadores_idx = [
        i for i in idx_valvuleria
        if cat_valvuleria[i].get("label") in _valv_labels_ganadores
    ]

    candidatos = {
        "entibacion": {
            "catalogo": cat_entibacion,
            "elegibles_idx": idx_entibacion,
            "ganador_idx": _buscar_ganador_idx(entib_item, cat_entibacion),
        },
        "pozo_registro": {
            "catalogo": cat_pozos,
            "elegibles_idx": idx_pozos,
            "ganador_idx": _buscar_ganador_idx(pozo_item, cat_pozos),
        },
        "valvuleria": {
            "catalogo": cat_valvuleria,
            "elegibles_idx": idx_valvuleria,
            "ganadores_idx": valv_ganadores_idx,
        },
        "desmontaje": {
            "catalogo": cat_desmontaje,
            "elegibles_idx": idx_desmontaje,
            "ganador_idx": _buscar_ganador_idx(desm_item, cat_desmontaje),
        },
    }

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
        "trazabilidad": trazabilidad,
        "candidatos": candidatos,
    }
