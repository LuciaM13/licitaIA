"""Capítulos 03-04: Pavimentación ABA y SAN.

Cada bloque busca la fila de demolición en el catálogo (red × tipo ×
unidad × material), llama a ``capitulo_demolicion`` + ``capitulo_pavimentacion``,
y opcionalmente añade ``capitulo_subbase`` si el espesor de la sub-base
es > 0.
"""

from __future__ import annotations

import logging

from src.modelo.parametros import ParametrosProyecto
from src.modelo.tipos import Precios
from src.presupuesto.bloques._comun import _acumular
from src.presupuesto.capitulos_superficie import (
    capitulo_demolicion,
    capitulo_pavimentacion,
    capitulo_subbase,
)
from src.presupuesto.materiales import (
    buscar_demolicion_requerida as _buscar_demolicion_requerida,
)

logger = logging.getLogger(__name__)


def ensamblar_pavimentacion_aba(
    p: ParametrosProyecto,
    precios: Precios,
    items_ci: dict,
    espesores: dict,
    caps: dict,
) -> None:
    """Capítulo 03 - Pavimentación Abastecimiento."""
    if not p.aba_activa:
        return

    logger.info("── CAP 03: PAVIMENTACIÓN ABA ──")
    logger.debug("[PAV-ABA] acerado_m2=%.2f bordillo_m=%.2f subbase_esp=%.3f mat(bord=%s acer=%s calz=%s)",
                 p.pav_aba_acerado_m2, p.pav_aba_bordillo_m, p.subbase_aba_espesor_m,
                 p.material_demo_bordillo_aba, p.material_demo_acerado_aba,
                 p.material_demo_calzada_aba)
    cat_demo_aba = precios.get("demolicion_aba", [])

    # Lookups por (tipo, unidad, material) — sin factor parche. El precio
    # de cada fila coincide con Excel oficial (invariante verificada en
    # test_bd_invariante_ci.py).
    item_acerado_aba = _buscar_demolicion_requerida(
        cat_demo_aba, "acerado", "m2", p.material_demo_acerado_aba,
        "ABA", p.pav_aba_acerado_m2)
    item_bordillo_aba = _buscar_demolicion_requerida(
        cat_demo_aba, "bordillo", "m", p.material_demo_bordillo_aba,
        "ABA", p.pav_aba_bordillo_m)
    _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
              capitulo_demolicion(p.pav_aba_acerado_m2, item_acerado_aba,
                                  p.pav_aba_bordillo_m, item_bordillo_aba))
    _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
              capitulo_pavimentacion(p.pav_aba_acerado_m2, items_ci["pav_aba_acerado_item"],
                                     p.pav_aba_bordillo_m, items_ci["pav_aba_bordillo_item"],
                                     factor_item1=1.0))
    # Calzada ABA (demolición + reposición)
    if p.pav_aba_calzada_m2 > 0:
        demo_calzada_aba = _buscar_demolicion_requerida(
            cat_demo_aba, "calzada", "m2", p.material_demo_calzada_aba,
            "ABA", p.pav_aba_calzada_m2)
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_demolicion(p.pav_aba_calzada_m2, demo_calzada_aba,
                                      0, None))
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_pavimentacion(p.pav_aba_calzada_m2, items_ci["pav_aba_calzada_item"],
                                         0, items_ci["pav_aba_bordillo_item"],
                                         calzada_conversion=True,
                                         espesores=espesores))
    if p.subbase_aba_espesor_m > 0:
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_subbase(p.pav_aba_acerado_m2 + p.pav_aba_calzada_m2,
                                   p.subbase_aba_espesor_m, items_ci["subbase_aba_item"]))

    _sub_pav_aba = caps.get("PAVIMENTACIÓN ABASTECIMIENTO", {}).get("subtotal", 0)
    logger.info("[PAV-ABA] SUBTOTAL CAP 03: %.2f €", _sub_pav_aba)


def ensamblar_pavimentacion_san(
    p: ParametrosProyecto,
    precios: Precios,
    items_ci: dict,
    espesores: dict,
    caps: dict,
) -> None:
    """Capítulo 04 - Pavimentación Saneamiento."""
    if not p.san_activa:
        return

    logger.info("── CAP 04: PAVIMENTACIÓN SAN ──")
    logger.debug("[PAV-SAN] calzada_m2=%.2f acera_m2=%.2f subbase_esp=%.3f mat(acer=%s calz=%s)",
                 p.pav_san_calzada_m2, p.pav_san_acera_m2, p.subbase_san_espesor_m,
                 p.material_demo_acerado_san, p.material_demo_calzada_san)
    cat_demo_san = precios.get("demolicion_san", [])
    item_calzada = _buscar_demolicion_requerida(
        cat_demo_san, "calzada", "m2", p.material_demo_calzada_san,
        "SAN", p.pav_san_calzada_m2)
    item_acera = _buscar_demolicion_requerida(
        cat_demo_san, "acerado", "m2", p.material_demo_acerado_san,
        "SAN", p.pav_san_acera_m2)
    _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
              capitulo_demolicion(p.pav_san_calzada_m2, item_calzada,
                                  p.pav_san_acera_m2, item_acera))
    _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
              capitulo_pavimentacion(p.pav_san_calzada_m2, items_ci["pav_san_calzada_item"],
                                     p.pav_san_acera_m2, items_ci["pav_san_acera_item"],
                                     calzada_conversion=True, espesores=espesores,
                                     factor_item1=1.0))
    if p.subbase_san_espesor_m > 0:
        _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
                  capitulo_subbase(p.pav_san_calzada_m2 + p.pav_san_acera_m2,
                                   p.subbase_san_espesor_m, items_ci["subbase_san_item"]))

    _sub_pav_san = caps.get("PAVIMENTACIÓN SANEAMIENTO", {}).get("subtotal", 0)
    logger.info("[PAV-SAN] SUBTOTAL CAP 04: %.2f €", _sub_pav_san)
