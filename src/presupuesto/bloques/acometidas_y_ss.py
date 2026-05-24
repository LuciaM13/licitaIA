"""Capítulos 05-08: Acometidas (ABA, SAN) y Seguridad/Salud + Gestión Ambiental.

  - ``ensamblar_acometidas`` — añade los capítulos 05 (ABA) y 06 (SAN)
    según el tipo de acometida por defecto del catálogo.
  - ``ensamblar_seguridad_gestion`` — calcula S&S y GA como porcentajes
    sobre la **base de S&S**, que excluye cánones, materiales y desmontaje
    (ver convención del Excel EMASESA).
"""

from __future__ import annotations

import logging

from src.modelo.parametros import ParametrosProyecto
from src.modelo.tipos import Precios
from src.presupuesto.bloques._comun import _acumular
from src.presupuesto.capitulos_superficie import capitulo_acometidas

logger = logging.getLogger(__name__)


def ensamblar_acometidas(
    p: ParametrosProyecto,
    precios: Precios,
    caps: dict,
) -> None:
    """Capítulos 05-06 - Acometidas ABA y SAN."""
    if p.aba_activa:
        logger.info("── CAP 05: ACOMETIDAS ABA ──")
        acometidas_aba = precios["acometidas_aba_tipos"]
        tipo_aba = precios["acometida_aba_defecto"]
        if tipo_aba not in acometidas_aba:
            raise ValueError(
                f"El tipo de acometida ABA por defecto '{tipo_aba}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        factor_aba = float(precios.get("acometidas_aba_factores", {}).get(tipo_aba, 1.2))
        logger.debug("[ACOM-ABA] n=%d tipo=%s precio=%.2f factor=%.2f",
                     p.acometidas_aba_n, tipo_aba, acometidas_aba[tipo_aba], factor_aba)
        _acumular(caps, "ACOMETIDAS ABASTECIMIENTO",
                  capitulo_acometidas(p.acometidas_aba_n,
                                      acometidas_aba[tipo_aba],
                                      "Acometidas ABA", factor=factor_aba))

    if p.san_activa:
        logger.info("── CAP 06: ACOMETIDAS SAN ──")
        acometidas_san = precios["acometidas_san_tipos"]
        tipo_san = precios["acometida_san_defecto"]
        if tipo_san not in acometidas_san:
            raise ValueError(
                f"El tipo de acometida SAN por defecto '{tipo_san}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        factor_san = float(precios.get("acometidas_san_factores", {}).get(tipo_san, 1.0))
        logger.debug("[ACOM-SAN] n=%d tipo=%s precio=%.2f factor=%.2f",
                     p.acometidas_san_n, tipo_san, acometidas_san[tipo_san], factor_san)
        _acumular(caps, "ACOMETIDAS SANEAMIENTO",
                  capitulo_acometidas(p.acometidas_san_n,
                                      acometidas_san[tipo_san],
                                      "Acometidas SAN", factor=factor_san))


def ensamblar_seguridad_gestion(
    p: ParametrosProyecto,
    caps: dict,
    estado: dict,
) -> None:
    """Capítulos 07-08 - Seguridad y Salud / Gestión Ambiental."""
    _base_ss_keys = {
        "OBRA CIVIL ABASTECIMIENTO", "OBRA CIVIL SANEAMIENTO",
        "PAVIMENTACIÓN ABASTECIMIENTO", "PAVIMENTACIÓN SANEAMIENTO",
        "ACOMETIDAS ABASTECIMIENTO", "ACOMETIDAS SANEAMIENTO",
    }
    _suma_bruta = sum(c["subtotal"] for nombre, c in caps.items() if nombre in _base_ss_keys)
    base_ss = max(0.0, _suma_bruta - estado["excluir_ss"] - estado["materiales_total"])
    logger.info("── CAPS 07-08: S&S / GA ──")
    logger.debug("base_ss = suma_caps(%.2f) - excluir_ss(%.2f) - materiales(%.2f) = %.2f",
                 _suma_bruta, estado["excluir_ss"], estado["materiales_total"], base_ss)

    if p.pct_seguridad > 0:
        importe_ss = base_ss * p.pct_seguridad
        _acumular(caps, "SEGURIDAD Y SALUD",
                  (importe_ss, {"Seguridad y Salud": importe_ss}))

    if p.pct_servicios_afectados > 0:
        importe_sa = base_ss * p.pct_servicios_afectados
        _acumular(caps, "SEGURIDAD Y SALUD",
                  (importe_sa, {"Servicios afectados": importe_sa}))

    if p.pct_gestion > 0:
        importe_ga = base_ss * p.pct_gestion
        _acumular(caps, "GESTIÓN AMBIENTAL",
                  (importe_ga, {"Gestión ambiental": importe_ga}))
