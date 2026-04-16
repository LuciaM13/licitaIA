"""Cálculo de partidas de suministro de materiales (excluidas de GG/BI).

Extraído de ensamblaje.py para mantener ese módulo por debajo de 550 líneas.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def materiales_aba(
    longitud: float, item: dict, decisiones: dict
) -> tuple[float, dict] | None:
    """Suministro de material puro ABA (excluido de base GG/BI)."""
    logger.debug("[MAT-ABA] Inicio - L=%.2f item=%s", longitud, item.get("label", "?"))
    partidas: dict[str, float] = {}

    precio_mat_m = float(item.get("precio_material_m", 0.0) or 0.0)
    factor_piezas = float(item.get("factor_piezas", 1.0))
    if precio_mat_m > 0:
        imp = longitud * precio_mat_m * factor_piezas
        partidas[item["label"] + " (suministro)"] = imp
        logger.debug("[MAT-ABA]   Suministro tubería: L=%.2f × precio_mat=%.4f × fp=%.2f = %.2f",
                     longitud, precio_mat_m, factor_piezas, imp)
    else:
        logger.debug("[MAT-ABA]   Sin suministro tubería (precio_material_m=0)")

    for v in decisiones["valvuleria"]["items"]:
        intervalo = float(v.get("intervalo_m", 0))
        precio_mat = float(v.get("precio_material", 0.0) or 0.0)
        if intervalo <= 0 or precio_mat <= 0:
            logger.debug("[MAT-ABA]   Valv '%s' descartada: intervalo=%.1f precio_mat=%.4f",
                         v.get("label", "?"), intervalo, precio_mat)
            continue
        n = longitud / intervalo
        fp = float(v.get("factor_piezas", 1.0))
        imp = n * precio_mat * fp
        partidas[v["label"] + " (material)"] = imp
        logger.debug("[MAT-ABA]   Valv '%s': n=%.2f × precio_mat=%.4f × fp=%.2f = %.2f",
                     v["label"], n, precio_mat, fp, imp)

    pozo_item = decisiones["pozo_registro"]["item"]
    if pozo_item is not None:
        precio_tapa_mat = float(pozo_item.get("precio_tapa_material", 0.0) or 0.0)
        intervalo_poz = float(pozo_item.get("intervalo", 0))
        if precio_tapa_mat > 0 and intervalo_poz > 0:
            imp = (longitud / intervalo_poz) * precio_tapa_mat
            partidas["Tapa pozo registro ABA (material)"] = imp
            logger.debug("[MAT-ABA]   Tapa pozo: n=%.2f × precio=%.4f = %.2f",
                         longitud / intervalo_poz, precio_tapa_mat, imp)
        else:
            logger.debug("[MAT-ABA]   Sin tapa pozo (precio_tapa_mat=%.4f intervalo=%.1f)",
                         precio_tapa_mat, intervalo_poz)
    else:
        logger.debug("[MAT-ABA]   Sin pozo_item → sin tapa material")

    if not partidas:
        logger.debug("[MAT-ABA] Resultado: None (sin partidas)")
        return None
    total = sum(partidas.values())
    logger.debug("[MAT-ABA] Resultado: %.2f € (%d partidas)", total, len(partidas))
    return total, partidas


def materiales_san(
    longitud: float, profundidad: float, pozo_item: dict | None
) -> tuple[float, dict] | None:
    """Suministro de material puro SAN (excluido de base GG/BI).

    Incluye:
    - Tapa pozo registro SAN (suministro material): n_pozos * precio_tapa_material
    - Pates de pozo (escalones): n_pozos * n_pates(prof) * precio_pate_material
      Fórmula Excel H45: H29 * IF(D19<2.5, 6, IF(D19<3.5, 9, 12))
    """
    if pozo_item is None:
        logger.debug("[MAT-SAN] pozo_item=None → return None")
        return None

    intervalo_poz = float(pozo_item.get("intervalo", 0))
    if intervalo_poz <= 0:
        logger.debug("[MAT-SAN] intervalo_poz=%.1f → return None", intervalo_poz)
        return None

    partidas: dict[str, float] = {}
    n_pozos = longitud / intervalo_poz
    logger.debug("[MAT-SAN] L=%.2f prof=%.2f intervalo=%.1f → n_pozos=%.2f",
                 longitud, profundidad, intervalo_poz, n_pozos)

    # Tapa pozo registro (suministro material)
    precio_tapa_mat = float(pozo_item.get("precio_tapa_material", 0.0) or 0.0)
    if precio_tapa_mat > 0:
        imp = n_pozos * precio_tapa_mat
        partidas["Tapa pozo registro SAN (material)"] = imp
        logger.debug("[MAT-SAN]   Tapa: n=%.2f × %.4f = %.2f", n_pozos, precio_tapa_mat, imp)
    else:
        logger.debug("[MAT-SAN]   Sin tapa (precio_tapa_material=0)")

    # Pates (escalones de pozo) - cantidad depende de la profundidad de la zanja
    precio_pate_mat = float(pozo_item.get("precio_pate_material", 0.0) or 0.0)
    if precio_pate_mat > 0:
        if profundidad < 2.5:
            n_pates = 6
        elif profundidad < 3.5:
            n_pates = 9
        else:
            n_pates = 12
        imp = n_pozos * n_pates * precio_pate_mat
        partidas["Pates pozo registro SAN (material)"] = imp
        logger.debug("[MAT-SAN]   Pates: n_pozos=%.2f × n_pates=%d × %.4f = %.2f",
                     n_pozos, n_pates, precio_pate_mat, imp)
    else:
        logger.debug("[MAT-SAN]   Sin pates (precio_pate_material=0)")

    if not partidas:
        logger.debug("[MAT-SAN] Resultado: None (sin partidas)")
        return None
    total = sum(partidas.values())
    logger.debug("[MAT-SAN] Resultado: %.2f € (%d partidas)", total, len(partidas))
    return total, partidas


def demo_items(red: str, precios: dict) -> tuple[dict | None, dict | None]:
    """Extrae items de demolición por unidad (m2 y m) del catálogo."""
    clave = f"demolicion_{red.lower()}"
    cat = precios.get(clave, [])
    logger.debug("[DEMO-ITEMS] Catálogo '%s': %d items", clave, len(cat))
    by_unit: dict[str, dict] = {}
    for item in cat:
        u = item.get("unidad", "")
        if u in by_unit:
            logger.error("[DEMO-ITEMS] Unidad duplicada '%s' en catálogo '%s'", u, clave)
            raise ValueError(
                f"El catálogo 'demolicion_{red.lower()}' tiene unidad duplicada '{u}'."
            )
        by_unit[u] = item
    item_m2 = by_unit.get("m2")
    item_m = by_unit.get("m")
    logger.debug("[DEMO-ITEMS] Resultado: m2=%s m=%s",
                 item_m2["label"] if item_m2 else None,
                 item_m["label"] if item_m else None)
    return item_m2, item_m
