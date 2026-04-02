"""
Ensamblaje del presupuesto y resumen financiero.

Reúne los capítulos calculados en calcular.py, los numera,
y genera el resumen financiero (PEM + GG + BI + IVA).
"""

from __future__ import annotations

from typing import Any, Dict

from src import config as dc
from src.config import ParametrosProyecto
from src.calcular import (
    _capitulo_obra_civil_red,
    _capitulo_pavimentacion,
    _capitulo_acometidas,
    _capitulo_importe_fijo,
)


# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN FINANCIERO
# ═══════════════════════════════════════════════════════════════════════════════
# PEM + Gastos Generales + Beneficio Industrial + IVA = Total

def _resumen_financiero(capitulos: dict, pcts: dict) -> Dict[str, Any]:
    pem = sum(c["subtotal"] for c in capitulos.values())
    gg = pem * pcts["gg"]
    bi = pem * pcts["bi"]
    pbl_sin_iva = pem + gg + bi
    iva = pbl_sin_iva * pcts["iva"]
    total = pbl_sin_iva + iva
    return {
        "pem": pem,
        "gg": gg, "bi": bi,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva, "total": total,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
# Ensambla todos los capítulos y el resumen financiero.
# Los capítulos se numeran (01, 02…) y solo se incluyen los que aplican.

# Añade un capítulo al diccionario si el resultado no es None
def _agregar_capitulo(capitulos: dict, cap_num: int, nombre: str,
                      resultado: tuple[float, dict] | None) -> int:
    if resultado is None:
        return cap_num
    subtotal, partidas = resultado
    capitulos[f"{cap_num:02d} {nombre}"] = {"subtotal": subtotal, "partidas": partidas}
    return cap_num + 1


def calcular_presupuesto(p: ParametrosProyecto, precios: dict) -> Dict[str, Any]:
    exc = precios["excavacion"]
    pcts = {"gg": precios["pct_gg"], "bi": precios["pct_bi"], "iva": precios["pct_iva"]}
    espesores = precios["espesores_calzada"]
    acometidas_aba = precios["acometidas_aba_tipos"]
    acometidas_san = precios["acometidas_san_tipos"]

    capitulos = {}
    capitulo_num = 1
    aux_aba = aux_san = None

    # Obra civil ABA
    if p.aba_item is not None and p.aba_longitud_m > 0:
        cap_aba, partidas_aba, aux_aba = _capitulo_obra_civil_red(
            p.aba_longitud_m, p.aba_profundidad_m,
            p.aba_item["precio_m"], p.aba_item["label"],
            exc, diametro_mm=p.aba_item["diametro_mm"],
        )
        capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "OBRA CIVIL ABASTECIMIENTO",
                                         (cap_aba, partidas_aba))

    # Obra civil SAN
    if p.san_item is not None and p.san_longitud_m > 0:
        cap_san, partidas_san, aux_san = _capitulo_obra_civil_red(
            p.san_longitud_m, p.san_profundidad_m,
            p.san_item["precio_m"], p.san_item["label"],
            exc, diametro_mm=p.san_item["diametro_mm"],
            es_san=True,
        )
        capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "OBRA CIVIL SANEAMIENTO",
                                         (cap_san, partidas_san))

    # Pavimentación ABA
    if p.aba_item is not None:
        capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "PAVIMENTACIÓN ABASTECIMIENTO",
                                         _capitulo_pavimentacion(
                                             p.pav_aba_acerado_m2, p.pav_aba_acerado_item,
                                             p.pav_aba_bordillo_m, p.pav_aba_bordillo_item))

    # Pavimentación SAN
    if p.san_item is not None:
        capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "PAVIMENTACIÓN SANEAMIENTO",
                                         _capitulo_pavimentacion(
                                             p.pav_san_calzada_m2, p.pav_san_calzada_item,
                                             p.pav_san_acera_m2, p.pav_san_acera_item,
                                             calzada_conversion=True,
                                             espesores=espesores))

    # Acometidas ABA
    if p.aba_item is not None:
        capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "ACOMETIDAS ABASTECIMIENTO",
                                         _capitulo_acometidas(p.acometidas_aba_n,
                                                              acometidas_aba[dc.ACOMETIDA_ABA],
                                                              "Acometidas ABA"))

    # Acometidas SAN
    if p.san_item is not None:
        capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "ACOMETIDAS SANEAMIENTO",
                                         _capitulo_acometidas(p.acometidas_san_n,
                                                              acometidas_san[dc.ACOMETIDA_SAN],
                                                              "Acometidas SAN"))

    # Seguridad y Gestión (importes fijos)
    subtotal_obra = sum(c["subtotal"] for c in capitulos.values())

    capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "SEGURIDAD Y SALUD",
                                     _capitulo_importe_fijo(p.importe_seguridad, "Seguridad y Salud"))
    capitulo_num = _agregar_capitulo(capitulos, capitulo_num, "GESTIÓN AMBIENTAL",
                                     _capitulo_importe_fijo(p.importe_gestion, "Gestión ambiental"))

    # Resumen financiero
    fin = _resumen_financiero(capitulos, pcts)

    pct_seg_info = (p.importe_seguridad / subtotal_obra * 100) if subtotal_obra > 0 and p.importe_seguridad > 0 else 0.0
    pct_gest_info = (p.importe_gestion / subtotal_obra * 100) if subtotal_obra > 0 and p.importe_gestion > 0 else 0.0

    return {
        "capitulos": capitulos,
        **fin,
        "pcts": pcts,
        "pct_seguridad_info": round(pct_seg_info, 2),
        "pct_gestion_info": round(pct_gest_info, 2),
        "auxiliares": {"aba": aux_aba or {}, "san": aux_san or {}},
    }
