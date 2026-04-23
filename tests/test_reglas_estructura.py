"""Tests que verifican el nuevo layout de ``src/reglas/`` tras el Paso 3 del refactor.

Cubre:
  - Los tres módulos nuevos (``decisor``, ``alertas_clips``, ``explicaciones``)
    exponen sus funciones públicas bajo los nombres honestos.
  - Los shims de compatibilidad (``motor``, ``trazabilidad``) siguen exportando
    los nombres antiguos para no romper imports legacy.
  - ``alertas_clips`` es el único módulo bajo ``src/reglas/`` que importa CLIPS;
    ``decisor`` y ``explicaciones`` son Python puro.

Objetivo del paso: alinear código ↔ memoria del TFG. La memoria declara que
CLIPS emite únicamente alertas técnicas; la selección de material es
determinista. Esta separación debe ser visible al abrir la carpeta.
"""
from __future__ import annotations

import ast
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Nuevos módulos exponen los nombres honestos
# ---------------------------------------------------------------------------

def test_decisor_expone_resolver_decisiones():
    from src.reglas.decisor import resolver_decisiones
    assert callable(resolver_decisiones)


def test_alertas_clips_expone_generar_alertas_tecnicas():
    from src.reglas.alertas_clips import generar_alertas_tecnicas
    assert callable(generar_alertas_tecnicas)


def test_explicaciones_expone_generar_explicaciones():
    from src.reglas.explicaciones import generar_explicaciones
    assert callable(generar_explicaciones)


# ---------------------------------------------------------------------------
# Shims de compatibilidad mantienen los nombres antiguos
# ---------------------------------------------------------------------------

def test_shim_motor_reexporta_nombres_antiguos():
    from src.reglas.motor import (
        resolver_decisiones,
        evaluar_sistema_experto,
        generar_alertas_tecnicas,
    )
    assert callable(resolver_decisiones)
    assert callable(evaluar_sistema_experto)
    # evaluar_sistema_experto es alias de generar_alertas_tecnicas (mismo callable)
    assert evaluar_sistema_experto is generar_alertas_tecnicas


def test_shim_trazabilidad_reexporta_generar_trazabilidad():
    from src.reglas.trazabilidad import (
        generar_trazabilidad,
        generar_explicaciones,
    )
    assert callable(generar_trazabilidad)
    # generar_trazabilidad es alias de generar_explicaciones
    assert generar_trazabilidad is generar_explicaciones


# ---------------------------------------------------------------------------
# Separación CLIPS-only: solo alertas_clips importa ``clips``
# ---------------------------------------------------------------------------

def _importa_modulo(fichero: Path, modulo: str) -> bool:
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name.split(".")[0] == modulo:
                    return True
        elif isinstance(nodo, ast.ImportFrom):
            if (nodo.module or "").split(".")[0] == modulo:
                return True
    return False


def test_decisor_no_importa_clips():
    fichero = _REPO_ROOT / "src" / "reglas" / "decisor.py"
    assert not _importa_modulo(fichero, "clips"), (
        "decisor.py es lógica determinista Python; no debe importar CLIPS. "
        "Si necesitas inferencia CLIPS, úsala en alertas_clips.py."
    )


def test_explicaciones_no_importa_clips():
    fichero = _REPO_ROOT / "src" / "reglas" / "explicaciones.py"
    assert not _importa_modulo(fichero, "clips"), (
        "explicaciones.py es formateo de cadenas; no debe importar CLIPS."
    )


def test_alertas_clips_si_importa_clips():
    """Verificación positiva: alertas_clips.py SÍ usa CLIPS. Esa es su razón de ser."""
    fichero = _REPO_ROOT / "src" / "reglas" / "alertas_clips.py"
    assert _importa_modulo(fichero, "clips"), (
        "alertas_clips.py debe importar clips; es el motor CLIPS del sistema."
    )
