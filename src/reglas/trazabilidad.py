"""
Generación de explicaciones en lenguaje natural para las decisiones del sistema experto.

Estas funciones reciben los parámetros de entrada y los resultados del motor CLIPS
y producen frases en castellano listas para mostrar en la UI.

Son funciones puras: no tienen efectos laterales, sin acceso a BD ni CLIPS.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _fmt_prof(p: float) -> str:
    return f"{p:.2f} m".replace(".", ",")


def _fmt_dn(dn: int) -> str:
    return f"DN={dn} mm"


def explicar_entibacion(
    profundidad: float,
    red: str,
    candidatos: list[dict],
    item_seleccionado: dict | None,
) -> str:
    """Genera explicación de la decisión de entibación."""
    p_fmt = _fmt_prof(profundidad)

    if item_seleccionado is None:
        umbral_ref = _umbral_red(candidatos, red)
        if umbral_ref is not None:
            return f"No se incluye. Profundidad {p_fmt}, umbral {_fmt_prof(umbral_ref)} en {red}."
        return f"No se incluye. Sin umbral definido para red {red}."

    umbral = float(item_seleccionado.get("umbral_m", 0))
    label = item_seleccionado.get("label", "entibación")
    n_candidatos = len(candidatos)

    if n_candidatos > 1:
        return (
            f"«{label}». Profundidad {p_fmt} ≥ umbral {_fmt_prof(umbral)}. "
            f"Seleccionado entre {n_candidatos} elegibles por mayor especificidad."
        )
    return f"«{label}». Profundidad {p_fmt} ≥ umbral {_fmt_prof(umbral)}."


def _umbral_red(candidatos_catalogo: list[dict], red: str) -> float | None:
    """Devuelve el umbral mínimo del catálogo para la red dada (para el mensaje de 'no aplica')."""
    # candidatos aquí es el catálogo completo, filtramos por red o wildcard
    umbrales = [
        float(it["umbral_m"])
        for it in candidatos_catalogo
        if it.get("red") == red or it.get("red") is None
    ]
    return min(umbrales) if umbrales else None


def explicar_pozo(
    profundidad: float,
    diametro_mm: int,
    red: str,
    n_candidatos: int,
    item_seleccionado: dict | None,
) -> str:
    """Genera explicación de la decisión de pozo de registro."""
    p_fmt = _fmt_prof(profundidad)
    dn_fmt = _fmt_dn(diametro_mm)

    if item_seleccionado is None:
        return f"Sin pozo elegible. {dn_fmt}, {p_fmt}, red {red}."

    label = item_seleccionado.get("label", "pozo de registro")
    pmax = item_seleccionado.get("profundidad_max")
    dmax = item_seleccionado.get("dn_max")

    detalles = [dn_fmt, p_fmt, f"red {red}"]
    if pmax is not None:
        detalles.append(f"prof. máx {_fmt_prof(float(pmax))}")
    if dmax is not None and int(dmax) < 99999:
        detalles.append(f"DN máx {dmax} mm")

    info = ", ".join(detalles)

    if n_candidatos > 1:
        return f"«{label}». {info}. Seleccionado entre {n_candidatos} elegibles por mayor especificidad."
    return f"«{label}». {info}."


def explicar_valvuleria(
    diametro_mm: int,
    instalacion: str,
    items_seleccionados: list[dict],
) -> str:
    """Genera explicación de los elementos de valvulería seleccionados."""
    dn_fmt = _fmt_dn(diametro_mm)
    inst_fmt = instalacion if instalacion != "*" else "cualquier instalación"

    if not items_seleccionados:
        return f"Sin elementos elegibles. {dn_fmt}, instalación {inst_fmt}."

    n = len(items_seleccionados)
    labels = [it.get("label", "?") for it in items_seleccionados]
    lista = ", ".join(f"«{l}»" for l in labels)

    return f"{n} elemento{'s' if n > 1 else ''}. {dn_fmt}, instalación {inst_fmt}. {lista}."


def explicar_desmontaje(
    desmontaje_tipo: str,
    diametro_mm: int,
    n_candidatos: int,
    item_seleccionado: dict | None,
) -> str:
    """Genera explicación de la decisión de desmontaje de tubería existente."""
    dn_fmt = _fmt_dn(diametro_mm)

    if desmontaje_tipo == "none":
        return "No se incluye. Sin tubería existente a desmontar."

    if item_seleccionado is None:
        return f"Sin ítem elegible. Tipo «{desmontaje_tipo}», {dn_fmt}."

    label = item_seleccionado.get("label", "desmontaje")

    if desmontaje_tipo == "fibrocemento":
        return f"«{label}». Precio único por ml, independiente del diámetro."

    dmax = item_seleccionado.get("dn_max")
    if dmax is not None:
        return f"«{label}». {dn_fmt}, cubre hasta DN={dmax} mm."
    return f"«{label}». {dn_fmt}."


def generar_trazabilidad(
    red: str,
    diametro_mm: int,
    profundidad: float,
    instalacion: str,
    desmontaje_tipo: str,
    cat_entibacion: list[dict],
    idx_entibacion: list[int],
    item_entibacion: dict | None,
    idx_pozos: list[int],
    item_pozo: dict | None,
    items_valvuleria: list[dict],
    idx_desmontaje: list[int],
    item_desmontaje: dict | None,
) -> list[str]:
    """
    Genera la lista completa de explicaciones para una red (ABA o SAN).

    Devuelve una lista de strings, uno por cada decisión del sistema experto.
    """
    logger.debug("[TRAZ-%s] Generando trazabilidad: DN=%d P=%.2f inst=%s desm=%s",
                 red, diametro_mm, profundidad, instalacion, desmontaje_tipo)

    txt_entib = explicar_entibacion(
        profundidad=profundidad,
        red=red,
        candidatos=cat_entibacion,
        item_seleccionado=item_entibacion,
    )
    logger.debug("[TRAZ-%s] Entibación: %s", red, txt_entib)

    txt_pozo = explicar_pozo(
        profundidad=profundidad,
        diametro_mm=diametro_mm,
        red=red,
        n_candidatos=len(idx_pozos),
        item_seleccionado=item_pozo,
    )
    logger.debug("[TRAZ-%s] Pozo: %s", red, txt_pozo)

    txt_valv = explicar_valvuleria(
        diametro_mm=diametro_mm,
        instalacion=instalacion,
        items_seleccionados=items_valvuleria,
    )
    logger.debug("[TRAZ-%s] Valvulería: %s", red, txt_valv)

    txt_desm = explicar_desmontaje(
        desmontaje_tipo=desmontaje_tipo,
        diametro_mm=diametro_mm,
        n_candidatos=len(idx_desmontaje),
        item_seleccionado=item_desmontaje,
    )
    logger.debug("[TRAZ-%s] Desmontaje: %s", red, txt_desm)

    return [txt_entib, txt_pozo, txt_valv, txt_desm]
