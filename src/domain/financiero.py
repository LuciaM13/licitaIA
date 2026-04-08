"""
Resumen financiero — fórmulas puras verificadas contra el Excel EMASESA.

Alineado con el cuadro resumen de las hojas de cálculo:
  (1) SUMA (a+b+c+d)  → PEM base
  (2) G.G. 13%        → pct_gg sobre base sin materiales
  (3) B.I. 6%         → pct_bi sobre base sin materiales
  (e) MATERIALES      → suministro puro (excluido de GG/BI)
  PEC sin IVA         → ROUNDUP a decena
  IVA                 → pct_iva sobre PEC
  TOTAL               → PEC + IVA

Este módulo no importa nada externo al dominio.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ResumenFinanciero:
    pem: float           # Suma de todos los capítulos
    base_gg_bi: float    # PEM sin materiales (base sobre la que aplican GG y BI)
    gg: float
    bi: float
    pbl_sin_iva: float   # PEC redondeado a decena superior
    iva: float
    total: float


def calcular_resumen(
    pem: float,
    materiales: float,
    pct_gg: float,
    pct_bi: float,
    pct_iva: float,
) -> ResumenFinanciero:
    """
    Calcula el resumen financiero completo a partir del PEM y los porcentajes.

    El PEM ya incluye los materiales; estos se excluyen solo de la base GG/BI
    (comportamiento del Excel EMASESA: GG y BI aplican sobre J61 sin incluir e)MATERIALES).

    Args:
        pem: Suma de todos los capítulos (incluyendo materiales).
        materiales: Importe del capítulo de suministro de materiales ABA.
        pct_gg: Porcentaje de Gastos Generales (ej. 0.13 para 13%).
        pct_bi: Porcentaje de Beneficio Industrial (ej. 0.06 para 6%).
        pct_iva: Porcentaje de IVA (ej. 0.21 para 21%).
    """
    base_gg_bi = pem - materiales
    gg = base_gg_bi * pct_gg
    bi = base_gg_bi * pct_bi
    # ROUNDUP a la decena superior — Excel: ROUNDUP((PEM+GG+BI)/10)*10
    pbl_sin_iva = math.ceil((pem + gg + bi) / 10) * 10
    iva = pbl_sin_iva * pct_iva
    total = pbl_sin_iva + iva

    return ResumenFinanciero(
        pem=round(pem, 2),
        base_gg_bi=round(base_gg_bi, 2),
        gg=round(gg, 2),
        bi=round(bi, 2),
        pbl_sin_iva=round(pbl_sin_iva, 2),
        iva=round(iva, 2),
        total=round(total, 2),
    )
