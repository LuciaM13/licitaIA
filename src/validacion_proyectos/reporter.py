"""Generador de tablas Markdown y bloque agregado para el TFG section 4.2.

Privacidad: resumen_4_2_md NO reproduce descripciones literales de partidas.
Solo agregados (conteos, ratios, importes acumulados por familia/catalogo).
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Iterable

from src.validacion_proyectos.tipos import GapReport

logger = logging.getLogger(__name__)


def _fmt_eur(x: float) -> str:
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(x: float) -> str:
    return f"{x * 100:+.2f} %"


def tabla_gap_global(reports: Iterable[GapReport]) -> str:
    lines = [
        "| Expediente | PEM real ajust. | PEM LIA | Δ € | Δ % |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in reports:
        lines.append(
            f"| {r.expediente} | {_fmt_eur(r.pem_real_ajustado)} | "
            f"{_fmt_eur(r.pem_licitaia)} | {_fmt_eur(r.gap_abs)} | {_fmt_pct(r.gap_pct)} |"
        )
    return "\n".join(lines)


def tabla_gap_capitulos(report: GapReport) -> str:
    lines = [
        f"### {report.expediente}",
        "",
        "| Cap | Nombre | PEM real | PEM LIA | Δ € | Δ % |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for c in report.por_capitulo:
        lines.append(
            f"| {c.capitulo} | {c.nombre_canonico} | {_fmt_eur(c.pem_real)} | "
            f"{_fmt_eur(c.pem_licitaia)} | {_fmt_eur(c.gap_abs)} | {_fmt_pct(c.gap_pct)} |"
        )
    return "\n".join(lines)


def tabla_huerfanas_top(reports: Iterable[GapReport], n: int = 20) -> str:
    """Agrega huerfanas por (catalogo_candidato, motivo) y muestra top N por importe.

    NO reproduce la descripcion cruda: agrupa por catalogo destino mas cercano.
    """
    grupos: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in reports:
        for h in r.huerfanas:
            cat = (h.candidato_mas_cercano or {}).get("catalogo", "(sin candidato)")
            grupos[(str(cat), h.motivo)].append(h.partida.importe)

    filas = sorted(
        ((k, sum(v), len(v)) for k, v in grupos.items()),
        key=lambda x: x[1],
        reverse=True,
    )[:n]

    lines = [
        "| Catalogo destino | Motivo | N | Importe acumulado |",
        "|---|---|---:|---:|",
    ]
    for (cat, motivo), importe, count in filas:
        lines.append(f"| {cat} | {motivo} | {count} | {_fmt_eur(importe)} |")
    return "\n".join(lines)


def tabla_gap_categorizado(report: GapReport) -> str:
    """Descomposicion del gap por fuente: alcance, cobertura catalogo, residual."""
    importe_excluido = report.pem_real_bruto - report.pem_real_ajustado
    cobertura = sum(h.partida.importe for h in report.huerfanas)
    residual = report.gap_abs - cobertura
    den = report.pem_real_ajustado if report.pem_real_ajustado else 1.0
    lines = [
        f"### Categorización del gap — {report.expediente}",
        "",
        "| Fuente del gap | Importe € | % sobre PEM real ajustado |",
        "|---|---:|---:|",
        f"| Alcance (caps + partidas excluidas) | {_fmt_eur(importe_excluido)} | {_fmt_pct(importe_excluido / den)} |",
        f"| Cobertura catálogo (huérfanas) | {_fmt_eur(cobertura)} | {_fmt_pct(cobertura / den)} |",
        f"| Aproximación (residual no explicado) | {_fmt_eur(residual)} | {_fmt_pct(residual / den)} |",
        f"| TOTAL | {_fmt_eur(report.gap_abs)} | {_fmt_pct(report.gap_pct)} |",
    ]
    return "\n".join(lines)


def resumen_4_2_md(reports: list[GapReport]) -> str:
    """Bloque Markdown para insertar en notebook/resultados_tfg.md section 4.2.

    Solo agregados; sin descripciones literales (privacidad EMASESA).
    """
    n_proy = len(reports)
    if n_proy == 0:
        return "# 4.2 Validacion contra obras EMASESA reales\n\n_Sin proyectos analizados._\n"

    pem_real_total = sum(r.pem_real_ajustado for r in reports)
    pem_lia_total = sum(r.pem_licitaia for r in reports)
    gap_abs_total = pem_lia_total - pem_real_total
    gap_pct_global = gap_abs_total / pem_real_total if pem_real_total else 0.0

    huerfanas_total = sum(len(r.huerfanas) for r in reports)
    motivos = Counter(h.motivo for r in reports for h in r.huerfanas)

    lines = [
        "# 4.2 Validacion contra obras EMASESA reales",
        "",
        f"Proyectos analizados: **{n_proy}**.",
        "",
        "## Gap global agregado",
        "",
        f"- PEM real ajustado acumulado: {_fmt_eur(pem_real_total)}",
        f"- PEM LicitaIA acumulado: {_fmt_eur(pem_lia_total)}",
        f"- Diferencia absoluta: {_fmt_eur(gap_abs_total)}",
        f"- Diferencia relativa: {_fmt_pct(gap_pct_global)}",
        "",
        "## Tabla de gap por proyecto",
        "",
        tabla_gap_global(reports),
        "",
        "## Partidas huerfanas",
        "",
        f"Total huerfanas detectadas: **{huerfanas_total}**.",
        "",
    ]
    for motivo, count in motivos.most_common():
        lines.append(f"- {motivo}: {count}")
    lines.extend([
        "",
        "## Huerfanas top (agregadas por catalogo destino)",
        "",
        tabla_huerfanas_top(reports, n=30),
        "",
    ])
    return "\n".join(lines)
