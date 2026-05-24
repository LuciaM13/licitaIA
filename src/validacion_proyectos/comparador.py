"""Comparador PEM real (BC3 EMASESA) vs PEM LicitaIA -> GapReport.

Compara magnitudes homogeneas: usa resultado["pem"] (NO total con IVA).
El gap por capitulo recorre el MAPEO_EMASESA_LICITAIA y descarta capitulos
fuera de alcance declarados en MetaProyecto.
"""

from __future__ import annotations

import logging
from typing import Any

from src.validacion_proyectos.mapeo_capitulos import (
    MAPEO_EMASESA_LICITAIA,
    normalizar_capitulos_licitaia,
)
from src.validacion_proyectos.tipos import (
    GapCapitulo,
    GapReport,
    Huerfana,
    MetaProyecto,
    ProyectoReal,
)

logger = logging.getLogger(__name__)


def _safe_pct(num: float, den: float) -> float:
    if den == 0.0:
        return 0.0
    return num / den


def comparar(
    real: ProyectoReal,
    resultado: dict[str, Any],
    meta: MetaProyecto,
    huerfanas: tuple[Huerfana, ...] = (),
) -> GapReport:
    logger.info("comparar INICIO expediente=%s", meta.expediente)
    pem_real_bruto = float(real.pem_total)
    fuera_alcance = set(meta.capitulos_fuera_alcance)
    partidas_fuera = set(meta.partidas_fuera_alcance)
    importe_caps_fuera = sum(real.capitulos_real.get(c, 0.0) for c in fuera_alcance)
    importe_partidas_fuera = sum(
        p.importe for p in real.partidas
        if p.codigo in partidas_fuera and p.capitulo not in fuera_alcance
    )
    pem_excluido = importe_caps_fuera + importe_partidas_fuera
    pem_real_ajustado = pem_real_bruto - pem_excluido

    pem_licitaia = float(resultado.get("pem", 0.0))
    gap_abs = pem_licitaia - pem_real_ajustado
    gap_pct = _safe_pct(gap_abs, pem_real_ajustado)

    capitulos_lia = normalizar_capitulos_licitaia(resultado)
    por_capitulo: list[GapCapitulo] = []
    for cap_num, nombre_canonico in MAPEO_EMASESA_LICITAIA.items():
        if cap_num in fuera_alcance:
            continue
        pem_real_cap = real.capitulos_real.get(cap_num, 0.0)
        pem_lia_cap = capitulos_lia.get(nombre_canonico, 0.0)
        gap_abs_cap = pem_lia_cap - pem_real_cap
        gap_pct_cap = _safe_pct(gap_abs_cap, pem_real_cap)
        por_capitulo.append(GapCapitulo(
            capitulo=cap_num,
            nombre_canonico=nombre_canonico,
            pem_real=pem_real_cap,
            pem_licitaia=pem_lia_cap,
            gap_abs=gap_abs_cap,
            gap_pct=gap_pct_cap,
        ))

    report = GapReport(
        expediente=meta.expediente,
        pem_real_bruto=pem_real_bruto,
        pem_real_ajustado=pem_real_ajustado,
        pem_licitaia=pem_licitaia,
        gap_abs=gap_abs,
        gap_pct=gap_pct,
        por_capitulo=tuple(por_capitulo),
        huerfanas=tuple(huerfanas),
        capitulos_excluidos=tuple(sorted(fuera_alcance)),
    )
    logger.info("comparar FIN expediente=%s gap_abs=%.2f gap_pct=%.4f",
                meta.expediente, gap_abs, gap_pct)
    return report
