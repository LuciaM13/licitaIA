"""``capitulo_obra_civil``: tubería + excavación + arena/relleno + entibación.

Es el capítulo dominante del presupuesto: monta el desglose por metro
lineal y lo escala a la longitud del tramo. Los cánones de vertido se
devuelven aparte, en ``auxiliares``, para que ``bloques.py`` los mueva al
capítulo OTROS sin que cuenten dos veces.
"""

from __future__ import annotations

import logging

from src.modelo.geometria import GeometriaZanja, calcular_geometria
from src.modelo.tipos import ItemCatalogo, Precios
from src.presupuesto.capitulos_obra_civil._helpers import (
    _calcular_canones,
    _importe,
    _partidas_excavacion,
)

logger = logging.getLogger(__name__)


def capitulo_obra_civil(
    longitud: float,
    profundidad: float,
    item: ItemCatalogo,
    precios: Precios,
    *,
    es_san: bool = False,
    pct_manual: float = 0.30,
    espesor_pavimento_m: float = 0.0,
    entibacion_item: ItemCatalogo | None = None,
) -> tuple[float, dict, dict]:
    """
    Calcula el capítulo de Obra Civil por metro lineal escalado a la longitud.

    Returns:
        (subtotal, partidas, auxiliares)
        Los cánones de vertido se devuelven en auxiliares["canon_tierras"] y
        auxiliares["canon_mixto"] para que ensamblaje.py los mueva al capítulo OTROS.
    """
    red_label = "SAN" if es_san else "ABA"
    logger.debug("[OC-%s] Entrada: L=%.2f P=%.2f item=%s pct_manual=%.2f h_pav=%.3f entib=%s",
                 red_label, longitud, profundidad, item.get("label", "?"),
                 pct_manual, espesor_pavimento_m,
                 entibacion_item["label"] if entibacion_item else None)

    L = max(longitud, 0.0)
    P = max(profundidad, 0.0)
    h_pav = max(espesor_pavimento_m, 0.0)
    pct_m = max(0.0, min(1.0, float(pct_manual)))

    hay_entibacion = entibacion_item is not None

    # Geometría (por metro lineal)
    geo: GeometriaZanja = calcular_geometria(
        dn_mm=int(item["diametro_mm"]),
        profundidad_m=P,
        es_san=es_san,
        hay_entibacion=hay_entibacion,
        espesor_pavimento_m=h_pav,
    )

    exc = precios["excavacion"]
    factor_esponj = float(precios.get("factor_esponjamiento", 1.30))
    factor_piezas = float(item.get("factor_piezas", 1.0))
    precio_tuberia = float(item["precio_m"])
    nombre_tuberia = item["label"]

    # Volúmenes totales (× longitud)
    vol_zanja = geo.vol_zanja_m3 * L
    vol_arena = geo.vol_arena_pm * L
    vol_relleno = geo.vol_relleno_pm * L
    vol_transporte = vol_zanja                      # perfil completo

    logger.debug("[OC-%s] Geo: fondo=%.3f cima=%.3f P_exc=%.3f | vol: zanja=%.3f arena=%.3f relleno=%.3f"
                 " transporte=%.3f (esponj=%.2f)",
                 red_label, geo.ancho_fondo_m, geo.ancho_cima_m, geo.P_exc_m,
                 vol_zanja, vol_arena, vol_relleno,
                 vol_transporte, factor_esponj)
    logger.debug("[OC-%s] Tubería: %s precio=%.4f fp=%.2f → %.2f €",
                 red_label, nombre_tuberia, precio_tuberia, factor_piezas,
                 _importe(L, precio_tuberia * factor_piezas))

    # ── Partidas ──────────────────────────────────────────────────────────────
    partidas: dict[str, float] = {}

    # Tubería (con factor piezas especiales)
    partidas[nombre_tuberia] = _importe(L, precio_tuberia * factor_piezas)

    # Excavación (split manual/mecánica; umbral de precio según P cruda)
    partidas.update(_partidas_excavacion(vol_zanja, pct_m, P, exc))

    # Arriñonado
    partidas["Apoyo y arriñonado"] = _importe(vol_arena, exc["arrinonado"])

    # Relleno
    partidas["Relleno de albero"] = _importe(vol_relleno, exc["relleno"])

    # Carga y transporte
    partidas["Carga de tierras"] = _importe(vol_transporte, exc["carga_mec"])
    partidas["Transporte a vertedero"] = _importe(vol_transporte, exc["transporte"])

    # Entibación
    if entibacion_item is not None:
        sup_entib = geo.sup_entibacion_pm * L
        partidas[entibacion_item["label"]] = _importe(sup_entib, entibacion_item["precio_m2"])
        logger.debug("[OC-%s] Entibación: sup=%.3f × precio=%.4f = %.2f €",
                     red_label, sup_entib, entibacion_item["precio_m2"],
                     partidas[entibacion_item["label"]])
    else:
        logger.debug("[OC-%s] Sin entibación", red_label)

    # ── Cánones (se devuelven separados para capítulo OTROS) ─────────────────
    canon_tierras, canon_mixto = _calcular_canones(
        vol_zanja, factor_esponj, L, h_pav, geo.ancho_cima_m, es_san, exc)

    subtotal = sum(partidas.values())
    logger.debug("[OC-%s] Subtotal obra civil: %.2f € | canon_tierras=%.2f canon_mixto=%.2f",
                 red_label, subtotal, canon_tierras, canon_mixto)

    auxiliares = {
        # Datos geométricos (para debug y tests)
        "ancho_fondo_m":   geo.ancho_fondo_m,
        "ancho_cima_m":    geo.ancho_cima_m,
        "P_exc_m":         geo.P_exc_m,
        "vol_zanja_m3":    round(vol_zanja, 3),
        "vol_arena_m3":    round(vol_arena, 3),
        "vol_relleno_m3":  round(vol_relleno, 3),
        "pct_manual":      round(pct_m, 2),
        # Cánones (para capítulo OTROS)
        "canon_tierras":   round(canon_tierras, 2),
        "canon_mixto":     round(canon_mixto, 2),
    }

    return subtotal, partidas, auxiliares
