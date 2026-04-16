"""
Utilidades compartidas entre módulos.

Responsabilidad única: funciones de formateo y búsqueda en catálogos.
"""

from __future__ import annotations

import logging
from typing import Any

from src.domain.parametros import ParametrosProyecto

logger = logging.getLogger(__name__)


# ─── Formateo ─────────────────────────────────────────────────────────────


def euro(valor: float) -> str:
    """Formatea un numero como moneda espanola (1.234,56 euros)."""
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# ─── Validación ───────────────────────────────────────────────────────────


def validar_parametros(p: ParametrosProyecto) -> list[str]:
    """Valida parámetros de entrada. Retorna lista de errores (vacía si OK)."""
    errores = []
    if p.aba_item is None and p.san_item is None:
        errores.append("Debe incluir al menos abastecimiento o saneamiento.")
    if p.aba_item is not None and p.aba_longitud_m <= 0:
        errores.append("Longitud de abastecimiento debe ser > 0.")
    if p.san_item is not None and p.san_longitud_m <= 0:
        errores.append("Longitud de saneamiento debe ser > 0.")
    if p.aba_item is not None and p.aba_profundidad_m <= 0:
        errores.append("Profundidad de abastecimiento debe ser > 0.")
    if p.san_item is not None and p.san_profundidad_m <= 0:
        errores.append("Profundidad de saneamiento debe ser > 0.")
    if errores:
        logger.warning("validar_parametros: %d error(es) de validación: %s", len(errores), errores)
    else:
        logger.debug("validar_parametros: OK")
    return errores


# ─── Búsqueda en catálogos ─────────────────────────────────────────────────


def find_item(items: list[dict], tipo: str, diametro: int) -> dict:
    """Busca una tubería por tipo y diámetro en un catálogo."""
    for item in items:
        if item["tipo"] == tipo and int(item["diametro_mm"]) == int(diametro):
            logger.debug("find_item: encontrado tipo=%s DN=%d → '%s'", tipo, diametro, item["label"])
            return item
    logger.error("find_item: NO ENCONTRADO tipo=%s DN=%d en catálogo de %d items "
                 "(labels disponibles: %s)",
                 tipo, diametro, len(items), [i.get("label") for i in items])
    raise ValueError(f"No se encontró tubería tipo={tipo}, diámetro={diametro}mm")


def find_by_label(items: list[dict], label: str) -> dict:
    """Busca un item por su label en un catálogo de materiales."""
    for item in items:
        if item["label"] == label:
            logger.debug("find_by_label: encontrado '%s'", label)
            return item
    logger.error("find_by_label: NO ENCONTRADO label='%s' en catálogo de %d items "
                 "(labels disponibles: %s)",
                 label, len(items), [i.get("label") for i in items])
    raise ValueError(f"No se encontró item con label='{label}'")


# ─── Exportación ───────────────────────────────────────────────────────────


def generar_texto_word(r: dict[str, Any]) -> str:
    """Genera texto listo para copiar a Word a partir del resultado del cálculo."""
    pcts = r["pcts"]
    lineas = [f"{k}: {euro(v['subtotal'])}" for k, v in r["capitulos"].items()]
    lineas.append(f"Presupuesto de Ejecución Material: {euro(r['pem'])}")
    lineas.append(f"{pcts['gg']*100:.0f} % Gastos Generales: {euro(r['gg'])}")
    lineas.append(f"{pcts['bi']*100:.0f} % Beneficio Industrial: {euro(r['bi'])}")
    lineas.append(f"Presupuesto Base de Licitación excluido IVA: {euro(r['pbl_sin_iva'])}")
    lineas.append(f"{pcts['iva']*100:.0f} % IVA: {euro(r['iva'])}")
    lineas.append(f"Presupuesto Base de Licitación incluido IVA: {euro(r['total'])}")
    return "\n".join(lineas)
