"""
Motor CLIPS que emite alertas técnicas sobre parámetros del proyecto.

Esta es la única parte del proyecto que invoca CLIPS. Mantiene una única
instancia ``clips.Environment`` cacheada a nivel de módulo (con plantillas
y reglas ya construidas) y la reutiliza en cada llamada haciendo
``env.reset()`` para limpiar hechos sin perder las reglas compiladas. Esto
encaja con el discurso del TFG de "una instancia stateless por sesión".

Asserta un único hecho ``datos-proyecto`` con los parámetros de entrada y
recoge los hechos ``alerta`` producidos por la inferencia.

**No selecciona materiales**. La selección de material es determinista y
vive en ``src.sistema_experto.decisor``. CLIPS aquí actúa como validador/alerter:
emite alertas dirigidas al licitador cuando ciertas combinaciones de
parámetros requieren atención (seguridad insuficiente, profundidad elevada,
etc.). Esta distinción está declarada en la memoria del TFG.
"""

from __future__ import annotations

import functools
import logging

import clips

from src.sistema_experto.reglas_clips import TEMPLATES, RULES
from src.sistema_experto.trazabilidad import RULE_PROVENANCE, explicar_alerta

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
# Entorno CLIPS cacheado (una sola instancia por proceso)
# ---------------------------------------------------------------------------
# Nota: usamos ``functools.lru_cache`` (no ``st.cache_resource``) para no
# acoplar la capa de motor a Streamlit. ``motor_clips`` debe ser lógica pura
# importable desde tests y otros contextos sin UI.

@functools.lru_cache(maxsize=1)
def _obtener_entorno_clips() -> clips.Environment:
    """Crea el ``Environment`` y construye plantillas + reglas una sola vez.

    Las llamadas posteriores reutilizan la misma instancia. Para limpiar los
    hechos entre invocaciones, el llamador debe hacer ``env.reset()`` antes
    de asertar nuevos datos: ``reset()`` purga la working memory pero
    preserva las construcciones (deftemplate/defrule) ya compiladas.
    """
    env = clips.Environment()
    for bloque in _iter_construcciones(TEMPLATES):
        try:
            env.build(bloque)
        except clips.CLIPSError:
            logger.exception("Error compilando template CLIPS:\n%s", bloque)
            raise
    for bloque in _iter_construcciones(RULES):
        try:
            env.build(bloque)
        except clips.CLIPSError:
            logger.exception("Error compilando regla CLIPS:\n%s", bloque)
            raise
    return env


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
    conduccion_provisional_m: float,
    pozos_existentes_aba: str,
    pozos_existentes_san: str,
    instalacion_valvuleria: str,
) -> dict:
    """
    Ejecuta el motor CLIPS sobre los parámetros del proyecto.

    El motor evalúa los parámetros del proyecto y emite alertas al licitador
    cuando ciertas combinaciones requieren atención. No hay clasificación
    intermedia ni encadenamiento entre reglas: cada regla mira directamente
    los slots de ``datos-proyecto`` y asserta un hecho ``alerta``.

    Invariante de coherencia: si una red está inactiva, sus parámetros se
    colapsan a valores neutros (longitud/profundidad/diametro 0, acometidas
    0, valvulería y pozos "none", tipo de tubería ""). Esto evita falsos
    positivos por defaults fantasma de la UI y libera a las reglas de tener
    que llevar guardas defensivas redundantes.

    No selecciona materiales ni influye en el cálculo numérico del
    presupuesto. Solo avisa.

    Returns:
        {
            "etiquetas": [],   # vacio: campo conservado por compatibilidad transitoria
            "alertas": [
                {"nivel": "error"|"warning"|"info", "msg": str,
                 "rule_id": str, "fuente": str},
                ...
            ],
            "cadena_inferencia": [
                {"capa": 3, "rule_id": str, "nivel": "alerta",
                 "texto": str, "fuente": str},
                ...
            ],
        }

        Cada item de ``cadena_inferencia`` es un ``CadenaItem`` (ver
        ``src.catalogo.editor.contratos.CadenaItem``).
    """
    env = _obtener_entorno_clips()
    # ``reset`` limpia la working memory pero preserva los deftemplate/defrule
    # ya construidos: es seguro reutilizar la instancia entre llamadas.
    env.reset()

    # Coherencia por construcción: si una red está inactiva, sus parámetros se
    # colapsan a valores neutros antes de assertar el hecho. La UI puede dejar
    # defaults fantasma vivos (p.ej. instalacion_valvuleria="enterrada" cuando
    # ABA no está activa) o inicializar acometidas desde defaults_ui aunque la
    # red no esté activa; el motor neutraliza esos casos para que las reglas
    # no necesiten guardas defensivas. Esta colapsación sustituyó a los
    # antiguos axiomas R10/R11/R14, que quedaban inalcanzables.
    if not aba_activa:
        aba_longitud_m = 0.0
        aba_profundidad_m = 0.0
        aba_diametro_mm = 0
        aba_tipo_tuberia = ""
        acometidas_aba_n = 0
        instalacion_valvuleria = "none"
        pozos_existentes_aba = "none"
    if not san_activa:
        san_profundidad_m = 0.0
        san_diametro_mm = 0
        acometidas_san_n = 0
        pozos_existentes_san = "none"

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
        conduccion_provisional_m=float(conduccion_provisional_m),
        pozos_existentes_aba=str(pozos_existentes_aba).strip().lower(),
        pozos_existentes_san=str(pozos_existentes_san).strip().lower(),
        instalacion_valvuleria=str(instalacion_valvuleria).strip().lower(),
    )

    n_fired = env.run()
    logger.debug("[SE] CLIPS run() → %d reglas disparadas", n_fired)

    alertas: list[dict] = []
    for fact in env.facts():
        if fact.template.name == "alerta":
            alertas.append({
                "nivel": str(fact["nivel"]),
                "msg": str(fact["msg"]),
                "rule_id": str(fact["rule_id"]),
                "fuente": str(fact["fuente"]),
            })

    logger.debug("[SE] Emitidas %d alertas", len(alertas))

    # Construir cadena de inferencia (provenance estática del SE).
    # Empaquetar inputs en el shape que espera explicar_alerta.
    # Coincide 1:1 con los slots de datos-proyecto. Slot virtual
    # _aba_san_delta_m precalculado para la trazabilidad de
    # alerta-entibacion-doble.
    inputs_dict: dict[str, object] = {
        "aba_activa": 1 if aba_activa else 0,
        "san_activa": 1 if san_activa else 0,
        "aba_longitud_m": float(aba_longitud_m),
        "aba_profundidad_m": float(aba_profundidad_m),
        "san_profundidad_m": float(san_profundidad_m),
        "aba_diametro_mm": int(aba_diametro_mm),
        "san_diametro_mm": int(san_diametro_mm),
        "aba_tipo_tuberia": str(aba_tipo_tuberia).strip(),
        "acometidas_aba_n": int(acometidas_aba_n),
        "acometidas_san_n": int(acometidas_san_n),
        "desmontaje_tipo": desmontaje_tipo.strip().lower(),
        "pct_seguridad": float(pct_seguridad),
        "pct_gestion": float(pct_gestion),
        "conduccion_provisional_m": float(conduccion_provisional_m),
        "pozos_existentes_aba": str(pozos_existentes_aba).strip().lower(),
        "pozos_existentes_san": str(pozos_existentes_san).strip().lower(),
        "instalacion_valvuleria": str(instalacion_valvuleria).strip().lower(),
        # Slot virtual para la trazabilidad de alerta-entibacion-doble.
        "_aba_san_delta_m": abs(float(aba_profundidad_m) - float(san_profundidad_m)),
    }

    from src.sistema_experto.tipos import CadenaItem

    ids_alertas_emitidas = {a["rule_id"] for a in alertas}

    cadena: list[CadenaItem] = []
    for al in alertas:
        rid = al["rule_id"]
        if rid not in RULE_PROVENANCE:
            logger.warning("[SE] alerta '%s' sin entrada en RULE_PROVENANCE", rid)
            continue
        cadena.append(explicar_alerta(rid, set(), inputs_dict, alertas_activas=ids_alertas_emitidas))

    logger.debug("[SE] cadena_inferencia construida con %d items", len(cadena))
    return {
        "etiquetas": [],  # campo conservado por compatibilidad transitoria; siempre vacio
        "alertas": alertas,
        "cadena_inferencia": cadena,
    }
