"""Modulo de validacion cruzada Excel maestro EMASESA <-> proyectos individuales.

API publica:
  - validar_proyecto(yaml_path, precios) -> GapReport
  - validar_lote(yaml_paths, precios) -> list[GapReport]
  - dataclasses: PartidaReal, ProyectoReal, MetaProyecto, Huerfana, GapCapitulo, GapReport

Importa del orquestador y del catalogo, NO toca BD ni Streamlit.
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any, Iterable

from src.catalogo.carga import aplicar_ci
from src.validacion_proyectos.cargador_yaml import cargar_parametros
from src.validacion_proyectos.comparador import comparar
from src.validacion_proyectos.detector_huerfanas import detectar
from src.validacion_proyectos.ejecutor import ejecutar
from src.validacion_proyectos.parser_excel import parsear_proyecto
from src.validacion_proyectos.tipos import (
    GapCapitulo,
    GapReport,
    Huerfana,
    MetaProyecto,
    PartidaReal,
    ProyectoReal,
)

logger = logging.getLogger(__name__)


__all__ = [
    "validar_proyecto",
    "validar_lote",
    "PartidaReal",
    "ProyectoReal",
    "MetaProyecto",
    "Huerfana",
    "GapCapitulo",
    "GapReport",
]


def _precios_ci_copy(precios_base: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una copia POST aplicar_ci() sin mutar el dict del caller."""
    pci = copy.deepcopy(precios_base)
    aplicar_ci(pci)
    return pci


def validar_proyecto(yaml_path: Path | str, precios_base: dict[str, Any]) -> GapReport:
    """Pipeline completo para un proyecto: parse XLSX, ejecuta orquestador, compara.

    El parser del XLSX deriva la ruta del campo `fuente_xlsx` del YAML.
    """
    yaml_path = Path(yaml_path)
    logger.info("validar_proyecto INICIO yaml=%s", yaml_path)

    precios_ci = _precios_ci_copy(precios_base)
    p, meta = cargar_parametros(yaml_path, precios_ci)

    import yaml as _yaml
    with yaml_path.open("r", encoding="utf-8") as f:
        cfg = _yaml.safe_load(f) or {}
    fuente = cfg.get("fuente_xlsx")
    if not fuente:
        raise ValueError(f"YAML {yaml_path} no declara 'fuente_xlsx'")
    real = parsear_proyecto(Path(fuente))

    resultado = ejecutar(p, precios_base, expediente=meta.expediente)
    huerfanas = tuple(detectar(real, precios_ci))
    report = comparar(real, resultado, meta, huerfanas=huerfanas)
    logger.info("validar_proyecto FIN expediente=%s gap_pct=%.4f", meta.expediente, report.gap_pct)
    return report


def validar_lote(yaml_paths: Iterable[Path | str], precios_base: dict[str, Any]) -> list[GapReport]:
    reports: list[GapReport] = []
    for yp in yaml_paths:
        try:
            reports.append(validar_proyecto(yp, precios_base))
        except Exception as e:
            logger.warning("validar_lote: error procesando %s -> %s", yp, e)
    return reports
