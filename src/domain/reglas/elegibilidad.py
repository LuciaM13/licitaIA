"""
Elegibilidad de materiales en Python puro (sin CLIPS).

Las decisiones de elegibilidad son filtros deterministas sobre catálogos
(red coincide, DN en rango, profundidad <= máx, etc.). No hay inferencia,
por lo que no justifican el overhead de un motor CLIPS.

El motor CLIPS se reserva para el subsistema de alertas técnicas
(``src.reglas.alertas_clips``), que clasifica el proyecto y emite avisos
al licitador con inferencia encadenada.

Convención ``None`` / wildcard:
  - En los catálogos JSON, ``red: null`` significa "aplica a cualquier red".
  - En los hechos CLIPS se serializa como ``"*"`` (ver ``NULL_SENTINEL``
    en ``src.domain.constantes``). Las funciones de abajo aceptan ambas
    representaciones.
"""

from __future__ import annotations

import logging

from src.domain.constantes import NULL_SENTINEL
from src.domain.tipos import ItemCatalogo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de coincidencia (wildcards)
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


# ---------------------------------------------------------------------------
# Funciones públicas de elegibilidad
# ---------------------------------------------------------------------------

def elegibles_entibacion(
    red: str, profundidad: float, catalogo: list[ItemCatalogo]
) -> list[int]:
    """Índices del catálogo de entibación elegibles para (red, profundidad).

    Criterio:
      - red del item coincide con la del proyecto o es wildcard,
      - profundidad de la zanja >= umbral_m del item.

    El umbral se usa con ``>=`` (no ``>``) para replicar el comportamiento
    del Excel SAN en la frontera 2.5 m.
    """
    indices = [
        i for i, it in enumerate(catalogo)
        if _red_coincide(it.get("red"), red)
        and profundidad >= float(it.get("umbral_m", 1.5))
    ]
    logger.debug("[ELEG-ENTIB] red=%s prof=%.2f → %d candidatos: %s",
                 red, profundidad, len(indices), indices)
    return indices


def elegibles_pozos(
    red: str, profundidad: float, diametro_mm: int, catalogo: list[ItemCatalogo]
) -> list[int]:
    """Índices del catálogo de pozos elegibles para (red, profundidad, DN).

    Criterio:
      - red del item coincide con la del proyecto o es wildcard,
      - profundidad <= profundidad_max del item (None = sin límite),
      - diametro_mm <= dn_max del item (None = sin límite).

    Se usa ``<=`` (no ``<``) porque los rangos en la BD son inclusivos en
    el extremo superior.
    """
    indices = [
        i for i, it in enumerate(catalogo)
        if _red_coincide(it.get("red"), red)
        and profundidad <= (
            float(it["profundidad_max"]) if it.get("profundidad_max") is not None else 9999.0
        )
        and diametro_mm <= (
            int(it["dn_max"]) if it.get("dn_max") is not None else 99999
        )
    ]
    logger.debug("[ELEG-POZO] red=%s prof=%.2f DN=%d → %d candidatos: %s",
                 red, profundidad, diametro_mm, len(indices), indices)
    return indices


def elegibles_valvuleria(
    diametro_mm: int, instalacion: str, catalogo: list[ItemCatalogo]
) -> list[int]:
    """Índices del catálogo de valvulería elegibles para (DN, instalación).

    Criterio:
      - dn_min <= diametro_mm <= dn_max,
      - instalación del item coincide con la del proyecto o es wildcard.

    Los items sin ``dn_min``/``dn_max`` se ignoran (catálogo mal formado).
    """
    indices = [
        i for i, it in enumerate(catalogo)
        if "dn_min" in it and "dn_max" in it
        and int(it["dn_min"]) <= diametro_mm <= int(it["dn_max"])
        and _inst_coincide(it.get("instalacion"), instalacion)
    ]
    logger.debug("[ELEG-VALV] DN=%d inst=%s → %d candidatos: %s",
                 diametro_mm, instalacion, len(indices), indices)
    return indices


def elegibles_desmontaje(
    tipo_desmontaje: str, diametro_mm: int, catalogo: list[ItemCatalogo]
) -> list[int]:
    """Índices del catálogo de desmontaje elegibles para (tipo, DN).

    Dos modos:
      - ``normal``: item con ``es_fibrocemento=0`` y ``diametro_mm <= dn_max``.
      - ``fibrocemento``: item con ``es_fibrocemento=1``. No se filtra por DN
        porque el coste lo domina el tratamiento del amianto, no el tamaño.
      - cualquier otro valor (ej. ``"none"``) → lista vacía.
    """
    if tipo_desmontaje == "normal":
        indices = [
            i for i, it in enumerate(catalogo)
            if not int(it.get("es_fibrocemento", 0))
            and diametro_mm <= int(it.get("dn_max", 0))
        ]
    elif tipo_desmontaje == "fibrocemento":
        indices = [
            i for i, it in enumerate(catalogo)
            if int(it.get("es_fibrocemento", 0))
        ]
    else:
        indices = []
    logger.debug("[ELEG-DESM] tipo=%s DN=%d → %d candidatos: %s",
                 tipo_desmontaje, diametro_mm, len(indices), indices)
    return indices
