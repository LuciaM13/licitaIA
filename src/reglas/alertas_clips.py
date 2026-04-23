"""
Motor CLIPS que emite alertas técnicas sobre parámetros del proyecto.

Esta es la única parte del proyecto que invoca CLIPS. Crea un entorno por
llamada (``clips.Environment()``), carga plantillas y reglas, asserta un
único hecho ``datos-proyecto`` con los parámetros de entrada y recoge los
hechos ``etiqueta`` y ``alerta`` producidos por la inferencia.

**No selecciona materiales**. La selección de material es determinista y
vive en ``src.reglas.decisor``. CLIPS aquí actúa como validador/alerter:
etiqueta el proyecto (zanja compleja, tramo urbano denso, amianto, etc.) y
emite alertas dirigidas al licitador cuando ciertas combinaciones de
parámetros requieren atención (seguridad insuficiente, profundidad elevada,
etc.). Esta distinción está declarada en la memoria del TFG.
"""

from __future__ import annotations

import logging

import clips

from src.reglas.templates import TEMPLATES, RULES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _iter_construcciones(fuente: str):
    """Itera bloques CLIPS ``defrule``/``deftemplate`` saltando banners de comentarios.

    El splitting por línea en blanco usado antes rompe cuando hay banners
    ASCII de sección (solo líneas ``;``) entre construcciones, porque
    ``env.build`` rechaza un bloque sin cabecera válida.
    """
    for bloque in fuente.strip().split("\n\n"):
        bloque = bloque.strip()
        if not bloque:
            continue
        # Considerar solo bloques que contengan al menos una línea no-comentario
        # que empiece con "(def" (deftemplate, defrule, defglobal, etc.).
        lineas_reales = [
            l.strip() for l in bloque.splitlines()
            if l.strip() and not l.strip().startswith(";")
        ]
        if not any(l.startswith("(def") for l in lineas_reales):
            continue
        yield bloque


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def generar_alertas_tecnicas(
    aba_activa: bool,
    san_activa: bool,
    aba_longitud_m: float,
    aba_profundidad_m: float,
    san_profundidad_m: float,
    aba_diametro_mm: int,
    san_diametro_mm: int,
    aba_tipo_tuberia: str,
    acometidas_aba_n: int,
    acometidas_san_n: int,
    desmontaje_tipo: str,
    pct_seguridad: float,
    pct_gestion: float,
    pct_servicios_afectados: float,
    conduccion_provisional_m: float,
    pozos_existentes_aba: str,
    pozos_existentes_san: str,
    instalacion_valvuleria: str,
) -> dict:
    """
    Ejecuta el motor CLIPS sobre los parámetros del proyecto.

    El motor primero clasifica la obra emitiendo **etiquetas** (hechos
    derivados) y después emite **alertas** al licitador que pueden apoyarse
    en esas etiquetas (inferencia encadenada).

    No selecciona materiales ni influye en el cálculo numérico del
    presupuesto. Solo etiqueta y avisa.

    Returns:
        {
            "etiquetas": [
                {"id": str, "nombre": str, "severidad": "alta"|"media"|"baja",
                 "fuente": str},
                ...
            ],
            "alertas": [
                {"nivel": "error"|"warning"|"info", "msg": str,
                 "rule_id": str, "fuente": str},
                ...
            ],
        }
    """
    env = clips.Environment()
    try:
        for bloque in _iter_construcciones(TEMPLATES):
            env.build(bloque)
        for bloque in _iter_construcciones(RULES):
            env.build(bloque)

        env.find_template("datos-proyecto").assert_fact(
            aba_activa=1 if aba_activa else 0,
            san_activa=1 if san_activa else 0,
            aba_longitud_m=float(aba_longitud_m),
            aba_profundidad_m=float(aba_profundidad_m),
            san_profundidad_m=float(san_profundidad_m),
            aba_diametro_mm=int(aba_diametro_mm),
            san_diametro_mm=int(san_diametro_mm),
            aba_tipo_tuberia=str(aba_tipo_tuberia).strip(),
            acometidas_aba_n=int(acometidas_aba_n),
            acometidas_san_n=int(acometidas_san_n),
            desmontaje_tipo=desmontaje_tipo.strip().lower(),
            pct_seguridad=float(pct_seguridad),
            pct_gestion=float(pct_gestion),
            pct_servicios_afectados=float(pct_servicios_afectados),
            conduccion_provisional_m=float(conduccion_provisional_m),
            pozos_existentes_aba=str(pozos_existentes_aba).strip().lower(),
            pozos_existentes_san=str(pozos_existentes_san).strip().lower(),
            instalacion_valvuleria=str(instalacion_valvuleria).strip().lower(),
        )

        n_fired = env.run()
        logger.debug("[SE] CLIPS run() → %d reglas disparadas", n_fired)

        etiquetas: list[dict] = []
        alertas: list[dict] = []
        for fact in env.facts():
            name = fact.template.name
            if name == "etiqueta":
                etiquetas.append({
                    "id": str(fact["id"]),
                    "nombre": str(fact["nombre"]),
                    "severidad": str(fact["severidad"]),
                    "fuente": str(fact["fuente"]),
                })
            elif name == "alerta":
                alertas.append({
                    "nivel": str(fact["nivel"]),
                    "msg": str(fact["msg"]),
                    "rule_id": str(fact["rule_id"]),
                    "fuente": str(fact["fuente"]),
                })

        logger.debug("[SE] Emitidas %d etiquetas y %d alertas",
                     len(etiquetas), len(alertas))
        return {"etiquetas": etiquetas, "alertas": alertas}
    finally:
        del env
