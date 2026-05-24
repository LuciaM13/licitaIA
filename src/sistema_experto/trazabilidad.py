"""
Provenance estática del sistema experto CLIPS.

Fuente canónica de la trazabilidad para defensa TFG: `RULE_PROVENANCE` mapea
cada `defrule` de `src.sistema_experto.reglas_clips` (17 reglas tipo alerta)
a su descripción humana, predicados sobre inputs y fuente normativa. La
función `explicar_alerta(...)` resuelve estos predicados contra los valores
reales del proyecto y produce un texto formateado listo para UI/persistencia.

Frontera arquitectónica (verificada en tests/test_fronteras_capas.py): este
módulo NO importa `clips`, `streamlit`, ni `sqlite3`. Solo `typing`,
`logging` y contratos puros del proyecto.

Justificación de provenance estática (no captura runtime de bindings CLIPS):
clipspy 1.0.6 no expone bindings por condición ni justification trace
(verificado en docs oficiales). En ingeniería del conocimiento, la
documentación de la base de reglas IS la trazabilidad — convención
correcta para defensa formal.
"""

from __future__ import annotations

import logging
from typing import Literal, TypedDict

from src.sistema_experto.tipos import CadenaItem

logger = logging.getLogger(__name__)


class Predicado(TypedDict, total=False):
    """Una condición sobre un slot de `datos-proyecto` que activa una regla."""
    slot: str
    operador: Literal[">", ">=", "<", "<=", "==", "!="]
    umbral: float | int | str
    unidad: str
    descripcion: str


class Subconjunto(TypedDict, total=False):
    """Subconjunto cohesivo de alertas dentro de una metaregla.

    Cada subconjunto agrupa reglas que comparten un mismo predicado de
    activación (por ejemplo, "max(prof_aba, prof_san) > 3.5 m"). El campo
    `rol` decide cómo combina la metaregla los subconjuntos:

      - 'obligatorio': debe disparar al menos UNA de las alertas del subconjunto.
      - 'alternativo': basta con que dispare UNA entre todos los subconjuntos
        marcados como 'alternativo' (OR entre alternativos).

    Logica completa: (todos los obligatorios cumplen) AND (al menos un
    alternativo cumple, si hay alternativos).
    """
    id: str
    nombre: str
    rol: Literal["obligatorio", "alternativo"]
    alertas: list[str]
    predicado_compartido: str


class EntradaProvenance(TypedDict, total=False):
    """Provenance estática de una regla CLIPS (etiqueta o alerta)."""
    capa: Literal[1, 2, 3]
    nivel: Literal["etiqueta", "alerta"]
    nombre_humano: str
    predicados_inputs: list[Predicado]
    etiquetas_requeridas: list[str]
    alertas_requeridas_dnf: list[list[str]]   # opcional, solo alerta-meta-*
    subconjuntos: list[Subconjunto]           # opcional, solo alerta-meta-*
    fuente: str
    fuente_ref: str


RULE_PROVENANCE: dict[str, EntradaProvenance] = {
    # ── Reglas de alerta al licitador ──────────────────────────────────────

    "alerta-fibrocemento-sin-gestion": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Fibrocemento sin gestion ambiental",
        "predicados_inputs": [
            {"slot": "desmontaje_tipo", "operador": "==", "umbral": "fibrocemento", "unidad": "", "descripcion": "tipo de desmontaje declarado como fibrocemento"},
            {
                "slot": "pct_gestion",
                "operador": "==",
                "umbral": 0.0,
                "unidad": "%",
                "descripcion": "porcentaje de Gestion Ambiental al 0%",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "RD 396/2006",
        "fuente_ref": "RD 396/2006: la obra con amianto requiere partida de gestion ambiental.",
    },

    "alerta-seguridad-critica": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Seguridad critica en obra compleja",
        "predicados_inputs": [
            {"slot": "aba_profundidad_m", "operador": ">", "umbral": 3.5, "unidad": "m", "descripcion": "profundidad ABA por encima del umbral de zanja compleja"},
            {"slot": "san_profundidad_m", "operador": ">", "umbral": 3.5, "unidad": "m", "descripcion": "profundidad SAN por encima del umbral de zanja compleja"},
            {
                "slot": "pct_seguridad",
                "operador": "<",
                "umbral": 0.02,
                "unidad": "%",
                "descripcion": "porcentaje de Seguridad y Salud por debajo del umbral critico",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Excel EMASESA",
        "fuente_ref": "",
    },

    "alerta-blindaje-necesario": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Blindaje recomendado",
        "predicados_inputs": [
            {"slot": "aba_profundidad_m", "operador": ">", "umbral": 3.5, "unidad": "m", "descripcion": "profundidad ABA por encima del umbral de zanja compleja"},
            {"slot": "san_profundidad_m", "operador": ">", "umbral": 3.5, "unidad": "m", "descripcion": "profundidad SAN por encima del umbral de zanja compleja"},
            {
                "slot": "pct_seguridad",
                "operador": ">=",
                "umbral": 0.02,
                "unidad": "%",
                "descripcion": "Seguridad por encima del umbral critico",
            },
            {
                "slot": "pct_seguridad",
                "operador": "<",
                "umbral": 0.03,
                "unidad": "%",
                "descripcion": "Seguridad por debajo del umbral de holgura para obra compleja",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Excel EMASESA",
        "fuente_ref": "",
    },

    "alerta-aba-larga-sin-acometidas": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "ABA larga sin acometidas",
        "predicados_inputs": [
            {"slot": "aba_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "ABA activa"},
            {
                "slot": "aba_longitud_m",
                "operador": ">",
                "umbral": 200.0,
                "unidad": "m",
                "descripcion": "longitud ABA superior al umbral de 'larga'",
            },
            {
                "slot": "acometidas_aba_n",
                "operador": "==",
                "umbral": 0,
                "unidad": "ud",
                "descripcion": "sin acometidas",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "regla interna",
        "fuente_ref": "",
    },

    "alerta-entibacion-doble": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Entibacion duplicada",
        "predicados_inputs": [
            {"slot": "aba_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "red ABA activa"},
            {"slot": "san_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "red SAN activa"},
            {"slot": "_aba_san_delta_m", "operador": "<", "umbral": 0.3, "unidad": "m", "descripcion": "diferencia |aba_profundidad - san_profundidad| inferior al umbral de zanja compartida"},
        ],
        "etiquetas_requeridas": [],
        "fuente": "regla interna",
        "fuente_ref": "",
    },

    "alerta-valvuleria-aproximada": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Valvuleria aproximada para DN grande",
        "predicados_inputs": [
            {"slot": "aba_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "ABA activa"},
            {
                "slot": "aba_diametro_mm",
                "operador": ">",
                "umbral": 300,
                "unidad": "mm",
                "descripcion": "diametro ABA por encima del umbral de aproximacion",
            },
            {
                "slot": "instalacion_valvuleria",
                "operador": "==",
                "umbral": "enterrada",
                "unidad": "",
                "descripcion": "valvuleria en zanja enterrada",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "audit BD-Excel A2C 2026-04-19",
        "fuente_ref": "Audit interno 2026-04-19 detecto sesgo en BD para DN > 300 mm.",
    },

    "prof-aba-fuera-rango-catalogo": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Profundidad ABA fuera del rango habitual",
        "predicados_inputs": [
            {"slot": "aba_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "ABA activa"},
            {
                "slot": "aba_profundidad_m",
                "operador": "<",
                "umbral": 0.6,
                "unidad": "m",
                "descripcion": "por debajo del minimo del catalogo EMASESA",
            },
            {
                "slot": "aba_profundidad_m",
                "operador": ">",
                "umbral": 6.0,
                "unidad": "m",
                "descripcion": "por encima del maximo del catalogo EMASESA",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Said 2024 / Aschilean 2018",
        "fuente_ref": (
            "Said et al. 2024 (deflexion bajo carga de trafico) y Aschilean et al. 2018 "
            "(Water): rangos respaldados por carga viva y catalogo EMASESA."
        ),
    },

    "prof-san-fuera-rango-catalogo": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Profundidad SAN fuera del rango habitual",
        "predicados_inputs": [
            {"slot": "san_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "SAN activa"},
            {
                "slot": "san_profundidad_m",
                "operador": "<",
                "umbral": 1.0,
                "unidad": "m",
                "descripcion": "saneamiento por gravedad bajo acometidas requiere minimo mas alto",
            },
            {
                "slot": "san_profundidad_m",
                "operador": ">",
                "umbral": 6.0,
                "unidad": "m",
                "descripcion": "por encima del maximo del catalogo EMASESA",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Ma 2024 / catalogo EMASESA",
        "fuente_ref": (
            "Ma et al. 2024 (Structures) modelan burial depth + traffic; catalogo "
            "EMASESA define el rango operativo."
        ),
    },

    "alerta-pozos-profundos-sin-escala": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Pozos profundos sin pates ni ventilacion",
        "predicados_inputs": [
            {"slot": "san_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "red SAN activa"},
            {"slot": "san_profundidad_m", "operador": ">", "umbral": 4.0, "unidad": "m", "descripcion": "profundidad SAN por encima del umbral de saneamiento profundo"},
            {
                "slot": "pozos_existentes_san",
                "operador": "!=",
                "umbral": "none",
                "unidad": "",
                "descripcion": "pozos preexistentes en SAN a tratar",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Ryoo 2023 / Smith 2014",
        "fuente_ref": (
            "Ryoo et al. 2023 documenta 165 muertes en pozos en 10 anos en Corea, "
            "letalidad 47%; Smith et al. 2014 (J. Occup. Environ. Hyg.) sobre "
            "atmosferas mortales en espacios confinados."
        ),
    },

    "alerta-fd-dn-grande-empuje": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Tuberia FD de gran diametro: empuje en codos y derivaciones en T",
        "predicados_inputs": [
            {
                "slot": "aba_tipo_tuberia",
                "operador": "==",
                "umbral": "FD",
                "unidad": "",
                "descripcion": "tuberia de fundicion ductil",
            },
            {
                "slot": "aba_diametro_mm",
                "operador": ">=",
                "umbral": 400,
                "unidad": "mm",
                "descripcion": "diametro grande, empuje hidraulico significativo",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Chen 2023 / Rajah 2021",
        "fuente_ref": (
            "Chen et al. 2023 (TUST) modelo 3D para DI; Rajah et al. 2021 (Pipelines) "
            "ASCE unified approach for thrust restraint design."
        ),
    },

    "alerta-pe-dn-pequeno-presion": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "PE de pequeno diametro: confirmar presion nominal",
        "predicados_inputs": [
            {
                "slot": "aba_tipo_tuberia",
                "operador": "==",
                "umbral": "PE-100",
                "unidad": "",
                "descripcion": "tuberia PE-100 (o PE-80)",
            },
            {
                "slot": "aba_diametro_mm",
                "operador": "<=",
                "umbral": 90,
                "unidad": "mm",
                "descripcion": "diametro pequeno: presion nominal relativa alta",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Bouaziz 2018 / Gaidi 2024",
        "fuente_ref": (
            "Bouaziz et al. 2018 (Fatigue Fract. Eng. Mater. Struct.) defectos "
            "criticos HDPE; Gaidi et al. 2024 (J. Mech. Eng. Sci.) J-integral "
            "para fallos bajo presion."
        ),
    },

    "alerta-densidad-acometidas-anomala": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Densidad de acometidas inusual",
        "predicados_inputs": [
            {
                "slot": "_densidad_acometidas",
                "operador": ">",
                "umbral": 0.30,
                "unidad": "ud/m",
                "descripcion": "(acometidas_aba_n + acometidas_san_n) / max(aba_longitud_m, 1.0)",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "EMASESA real (corpus 7 proyectos)",
        "fuente_ref": (
            "Maximo observado en el corpus EMASESA: 0.16 ud/m (GOB.25.020). "
            "Ratios > 0.30 son anomalos y sugieren error de captura."
        ),
    },

    "alerta-trafico-sin-conduccion-provisional": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Tramo urbano denso sin conduccion provisional",
        "predicados_inputs": [
            {"slot": "aba_activa", "operador": "==", "umbral": 1, "unidad": "", "descripcion": "red ABA activa"},
            {"slot": "aba_longitud_m", "operador": ">", "umbral": 100.0, "unidad": "m", "descripcion": "longitud ABA superior al umbral urbano"},
            {"slot": "acometidas_aba_n", "operador": ">", "umbral": 5, "unidad": "ud", "descripcion": "numero de acometidas ABA por encima del umbral urbano"},
            {
                "slot": "conduccion_provisional_m",
                "operador": "==",
                "umbral": 0.0,
                "unidad": "m",
                "descripcion": "no se ha previsto conduccion provisional",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Tanoli 2019 / Wu 2021",
        "fuente_ref": (
            "Tanoli et al. 2019 (Automation in Construction) damage prevention en "
            "servicios enterrados; Wu et al. 2021 (RESS) marco cuantitativo bayesiano."
        ),
    },

    "alerta-pct-seguridad-rango-anomalo": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Porcentaje de Seguridad fuera del rango habitual",
        "predicados_inputs": [
            {
                "slot": "pct_seguridad",
                "operador": "<",
                "umbral": 0.01,
                "unidad": "%",
                "descripcion": "por debajo del 1% (anomalo segun corpus EMASESA y literatura)",
            },
            {
                "slot": "pct_seguridad",
                "operador": ">",
                "umbral": 0.10,
                "unidad": "%",
                "descripcion": "por encima del 10% (anomalo)",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "Shohet 2018 / Bachar 2024",
        "fuente_ref": (
            "Shohet et al. 2018 (Safety Science): optimo 1.0%; Bachar et al. 2024 "
            "(Safety Science): hasta 3.8% en PYMEs; corpus EMASESA real 2.78-7.36%."
        ),
    },

    "alerta-pct-gestion-rango-anomalo": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Porcentaje de Gestion Ambiental fuera del rango habitual EMASESA",
        "predicados_inputs": [
            {
                "slot": "pct_gestion",
                "operador": "<",
                "umbral": 0.005,
                "unidad": "%",
                "descripcion": "por debajo del 0.5%",
            },
            {
                "slot": "pct_gestion",
                "operador": ">",
                "umbral": 0.11,
                "unidad": "%",
                "descripcion": "por encima del 11% (max EMASESA real 10.13%)",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "EMASESA real (corpus 7 proyectos)",
        "fuente_ref": (
            "Mediana observada 7.81%, max 10.13%. GA agrega Gestion Residuos + "
            "Proteccion Arbolado, por eso el rango es mas alto que el de gestion "
            "de residuos puro en literatura internacional (1-3%)."
        ),
    },

    "alerta-amianto-sin-margen-seguridad": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Obra con amianto y margen de Seguridad ajustado",
        "predicados_inputs": [
            {"slot": "desmontaje_tipo", "operador": "==", "umbral": "fibrocemento", "unidad": "", "descripcion": "tipo de desmontaje declarado como fibrocemento"},
            {
                "slot": "pct_seguridad",
                "operador": "<",
                "umbral": 0.04,
                "unidad": "%",
                "descripcion": "S&S por debajo del margen heuristico operativo para amianto",
            },
        ],
        "etiquetas_requeridas": [],
        "fuente": "RD 396/2006 + Gottesfeld 2023",
        "fuente_ref": (
            "RD 396/2006 sobre amianto (planes de trabajo, RERA); Gottesfeld 2023 "
            "(Annals of Work Exposures): exposicion 11-129 fibras/cm3 al cortar AC. "
            "Umbral 4% es heuristica operativa EMASESA, no derivada cuantitativamente "
            "de literatura."
        ),
    },

    "alerta-meta-proyecto-alto-riesgo": {
        "capa": 3,
        "nivel": "alerta",
        "nombre_humano": "Proyecto de alto riesgo (alerta agregada)",
        "predicados_inputs": [],
        "etiquetas_requeridas": [],
        # Tres subconjuntos cohesivos. Cada uno con su predicado compartido y su rol:
        #   - obligatorio: tiene que disparar al menos UNA de su lista
        #   - alternativo: basta con que dispare UNA entre todos los 'alternativo'
        # Logica de disparo: (todos los obligatorios cumplen) AND (al menos un alternativo cumple).
        # Para esta regla: ?r1 obligatorio AND (?r2 OR ?r3).
        "subconjuntos": [
            {
                "id": "r1",
                "nombre": "Riesgo geometrico de la zanja",
                "rol": "obligatorio",
                "alertas": ["alerta-seguridad-critica",
                            "alerta-blindaje-necesario"],
                "predicado_compartido": "max(prof_aba, prof_san) > 3.5 m + umbral pct_seguridad",
            },
            {
                "id": "r2",
                "nombre": "Riesgo de contexto urbano denso",
                "rol": "alternativo",
                "alertas": ["alerta-trafico-sin-conduccion-provisional"],
                "predicado_compartido": "aba_longitud_m > 100 AND acometidas_aba_n > 5",
            },
            {
                "id": "r3",
                "nombre": "Riesgo de material peligroso (amianto)",
                "rol": "alternativo",
                "alertas": ["alerta-fibrocemento-sin-gestion",
                            "alerta-amianto-sin-margen-seguridad"],
                "predicado_compartido": "desmontaje_tipo == 'fibrocemento'",
            },
        ],
        # Forma DNF colapsada (lista de OR-grupos AND-encadenados). Se mantiene
        # para que cualquier renderer antiguo siga funcionando: ?r2 y ?r3 se
        # unen en el segundo grupo porque ambos son alternativos entre si.
        "alertas_requeridas_dnf": [
            ["alerta-seguridad-critica", "alerta-blindaje-necesario"],
            ["alerta-trafico-sin-conduccion-provisional",
             "alerta-fibrocemento-sin-gestion", "alerta-amianto-sin-margen-seguridad"],
        ],
        "fuente": "regla agregada (combina otras alertas)",
        "fuente_ref": (
            "Encadenamiento real: la regla solo lee otras alertas, no toca inputs. "
            "Reintroduce el razonamiento de orden superior tras el aplanado del SE. "
            "Estructura: ?r1 (geometrico, obligatorio) AND "
            "(?r2 urbano denso OR ?r3 amianto, ambos alternativos)."
        ),
    },
}


def _formatear_predicado(predicado: Predicado, inputs: dict) -> str:
    slot = predicado["slot"]
    operador = predicado["operador"]
    umbral = predicado.get("umbral")
    unidad = predicado.get("unidad", "")
    descripcion = predicado.get("descripcion", "")
    valor_real = inputs.get(slot, "?")
    if isinstance(valor_real, float):
        valor_str = f"{valor_real:.2f}"
    else:
        valor_str = str(valor_real)
    sufijo = f" {unidad}" if unidad else ""
    umbral_str = f"{umbral}{sufijo}" if umbral is not None else ""
    return (
        f"  - {slot} = {valor_str}{sufijo} {operador} {umbral_str} "
        f"({descripcion})."
    )


def explicar_alerta(
    rule_id: str,
    etiquetas_activas: set[str],
    inputs: dict,
    alertas_activas: set[str] | None = None,
) -> CadenaItem:
    """Devuelve un CadenaItem con texto formateado listo para UI/persistencia.

    El texto incluye los valores reales de los inputs (LD-2). Ejemplo de retorno:

        "Regla disparada: alerta-fibrocemento-sin-gestion (Fibrocemento sin gestion
         ambiental) — CAPA 3.
         Condiciones sobre inputs:
           - desmontaje_tipo = fibrocemento == fibrocemento (...).
           - pct_gestion = 0.00 % == 0.0 % (porcentaje de Gestion Ambiental al 0%).
         Fuente: RD 396/2006 (RD 396/2006: la obra con amianto requiere partida...)"

    Args:
        rule_id: rule_id de la alerta emitida por CLIPS. Debe existir en
            RULE_PROVENANCE.
        etiquetas_activas: parametro mantenido por compatibilidad transitoria
            con consumidores antiguos; ahora se ignora porque no hay etiquetas
            intermedias en el sistema.
        inputs: dict con los slots de datos-proyecto y sus valores reales. Puede
            incluir slots virtuales precalculados por el caller, como
            `_aba_san_delta_m` (= abs(aba_profundidad_m - san_profundidad_m))
            necesario para la regla `alerta-entibacion-doble`.
        alertas_activas: conjunto de `rule_id`s de alertas ya emitidas por el
            motor en esta ejecucion. Solo lo consumen las reglas meta cuya
            entrada en RULE_PROVENANCE define `subconjuntos` (preferido) o
            `alertas_requeridas_dnf` (fallback), es decir, encadenamiento
            real sobre otras alertas. Para reglas base se ignora; queda como
            `None` por defecto.

    Returns:
        CadenaItem con capa, rule_id, nivel, texto (multilinea) y fuente.
    """
    del etiquetas_activas  # ignorado: compatibilidad transitoria

    if rule_id not in RULE_PROVENANCE:
        logger.warning("[SE] rule_id '%s' sin entrada en RULE_PROVENANCE", rule_id)
        return {
            "capa": 3,
            "rule_id": rule_id,
            "nivel": "alerta",
            "texto": f"Sin provenance disponible para regla '{rule_id}'.",
            "fuente": "provisional",
        }

    entrada = RULE_PROVENANCE[rule_id]
    nombre = entrada["nombre_humano"]
    capa = entrada["capa"]
    nivel = entrada["nivel"]

    bloques: list[str] = []
    bloques.append(f"Regla disparada: {rule_id} ({nombre}) — CAPA {capa}.")

    subconjuntos = entrada.get("subconjuntos")
    alertas_dnf = entrada.get("alertas_requeridas_dnf")
    if subconjuntos and alertas_activas is not None:
        # Render estructurado por subconjuntos cohesivos (con rol y nombre).
        bloques.append("Apoyada en alertas (combinacion):")
        for sub in subconjuntos:
            sub_alertas = sub.get("alertas", [])
            activos = [rid for rid in sub_alertas if rid in alertas_activas]
            rol = sub.get("rol", "")
            sub_nombre = sub.get("nombre", "")
            marca = "ACTIVO" if activos else "no activo"
            if activos:
                detalle = ", ".join(activos)
            else:
                detalle = "(ninguna activa)"
            bloques.append(
                f"  - [{rol}] {sub_nombre} ({marca}): {detalle}."
            )
    elif alertas_dnf and alertas_activas is not None:
        # Fallback: render plano DNF (lista de OR-grupos AND-encadenados).
        bloques.append("Apoyada en alertas (combinacion):")
        for grupo in alertas_dnf:
            activos = [rid for rid in grupo if rid in alertas_activas]
            if len(grupo) == 1:
                mark = "activa" if activos else "NO activa"
                bloques.append(f"  - {grupo[0]} ({mark}).")
            else:
                bloques.append(
                    f"  - alguna de [{', '.join(grupo)}]: "
                    f"activa(s) -> {', '.join(activos) if activos else '(ninguna)'}."
                )

    predicados = entrada.get("predicados_inputs", [])
    if predicados:
        bloques.append("Condiciones sobre inputs:")
        for p in predicados:
            bloques.append(_formatear_predicado(p, inputs))

    fuente = entrada.get("fuente", "")
    fuente_ref = entrada.get("fuente_ref", "")
    if fuente_ref:
        bloques.append(f"Fuente: {fuente} ({fuente_ref})")
    else:
        bloques.append(f"Fuente: {fuente}")

    return {
        "capa": capa,
        "rule_id": rule_id,
        "nivel": nivel,
        "texto": "\n".join(bloques),
        "fuente": fuente,
    }
