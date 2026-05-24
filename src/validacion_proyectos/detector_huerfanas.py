"""Detector de partidas reales sin contrapartida en el catalogo CI.

CRITICO: precios_ci debe pasarse POST aplicar_ci(). Los precios del Excel
EMASESA real ya llevan el 1.05 incorporado; comparar contra precios BASE da
gaps sistematicos del 5%.

Estrategia:
  1. Aplanar precios_ci a un indice [(catalogo_key, label, descripcion_norm,
     precio)] recorriendo _CI_CAMPOS de src.catalogo.carga.
  2. Para cada PartidaReal, normalizar (NFKD + minusculas + abreviaturas
     EMASESA) y buscar mejor candidato con difflib.SequenceMatcher >= 0.75.
  3. Sin candidato -> Huerfana(motivo="sin_match_descripcion").
  4. Con candidato pero precio fuera de tol_pct -> Huerfana(motivo=
     "match_pero_precio_fuera_tolerancia").
"""

from __future__ import annotations

import difflib
import logging
import unicodedata
from typing import Any

from src.catalogo.carga import _CI_CAMPOS
from src.validacion_proyectos.tipos import Huerfana, ProyectoReal

logger = logging.getLogger(__name__)


# Tabla de abreviaturas EMASESA -> forma canonica.
# Aplicada DESPUES de minusculas y eliminacion de acentos. Por eso las claves
# estan ya en minusculas y sin tildes.
_ABREVIATURAS: dict[str, str] = {
    "ent.": "enterrada",
    "ø": "dn",
    "fd": "fundicion ductil",
    "pe": "polietileno",
    "pvc": "pvc",
    "dn": "diametro nominal",
    "san.": "saneamiento",
    "aba.": "abastecimiento",
    "fc": "fibrocemento",
}


def _normalizar(texto: str) -> str:
    """NFKD + minusculas + tabla de abreviaturas EMASESA."""
    if not texto:
        return ""
    s = unicodedata.normalize("NFKD", texto)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    for abrev, expansion in _ABREVIATURAS.items():
        s = s.replace(abrev, expansion)
    s = " ".join(s.split())
    return s


def _aplanar_catalogo(precios_ci: dict[str, Any]) -> list[dict[str, Any]]:
    """Aplana precios_ci a una lista de candidatos comparables."""
    candidatos: list[dict[str, Any]] = []
    catalogos_vistos: set[str] = set()
    for catalogo_key, campo_precio in _CI_CAMPOS:
        if catalogo_key in catalogos_vistos:
            continue
        catalogos_vistos.add(catalogo_key)
        items = precios_ci.get(catalogo_key, []) or []
        for it in items:
            label = str(it.get("label", "") or "")
            if not label:
                continue
            precio = it.get(campo_precio)
            if precio is None:
                # Algunos catalogos comparten clave pero no campo (e.g. precio_material).
                # Buscamos cualquier campo de precio del item como fallback.
                for k in ("precio", "precio_m", "precio_m2", "precio_m3"):
                    if k in it and it[k]:
                        precio = it[k]
                        break
            try:
                precio_f = float(precio) if precio is not None else 0.0
            except (TypeError, ValueError):
                precio_f = 0.0
            candidatos.append({
                "catalogo": catalogo_key,
                "label": label,
                "descripcion_norm": _normalizar(label),
                "precio": precio_f,
            })
    logger.info("_aplanar_catalogo -> %d candidatos en %d catalogos",
                len(candidatos), len(catalogos_vistos))
    return candidatos


def _mejor_candidato(
    descripcion_norm: str,
    candidatos: list[dict[str, Any]],
    umbral: float = 0.75,
) -> tuple[dict[str, Any] | None, float]:
    mejor: dict[str, Any] | None = None
    mejor_ratio = 0.0
    for c in candidatos:
        ratio = difflib.SequenceMatcher(None, descripcion_norm, c["descripcion_norm"]).ratio()
        if ratio > mejor_ratio:
            mejor_ratio = ratio
            mejor = c
    if mejor_ratio < umbral:
        return None, mejor_ratio
    return mejor, mejor_ratio


def detectar(
    real: ProyectoReal,
    precios_ci: dict[str, Any],
    *,
    tol_pct: float = 0.05,
) -> list[Huerfana]:
    logger.info("detectar INICIO expediente=%s partidas=%d tol_pct=%.3f",
                real.expediente, len(real.partidas), tol_pct)
    candidatos = _aplanar_catalogo(precios_ci)
    huerfanas: list[Huerfana] = []
    for partida in real.partidas:
        norm = _normalizar(partida.descripcion)
        candidato, similitud = _mejor_candidato(norm, candidatos)
        if candidato is None:
            huerfanas.append(Huerfana(
                partida=partida,
                motivo="sin_match_descripcion",
                candidato_mas_cercano=None,
                similitud=similitud,
                delta_pct=None,
            ))
            continue
        precio_cat = candidato["precio"]
        if precio_cat <= 0:
            continue
        delta = (partida.precio_unitario - precio_cat) / precio_cat
        if abs(delta) > tol_pct:
            huerfanas.append(Huerfana(
                partida=partida,
                motivo="match_pero_precio_fuera_tolerancia",
                candidato_mas_cercano=dict(candidato),
                similitud=similitud,
                delta_pct=delta,
            ))

    huerfanas.sort(key=lambda h: h.partida.importe, reverse=True)
    logger.info("detectar FIN huerfanas=%d", len(huerfanas))
    return huerfanas
