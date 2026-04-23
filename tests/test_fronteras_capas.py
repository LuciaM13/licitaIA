"""Test AST que verifica las fronteras arquitectónicas entre capas.

Convierte la arquitectura documentada en ADR-001 (plan de Fase 3) en un
invariante verificable. Si un módulo cruza una frontera prohibida, el
test falla con mensaje accionable. Así las reglas de capas no se
degradan con el tiempo.

Política de excepciones
-----------------------
Cualquier excepción a una regla debe vivir en ``_EXCEPCIONES`` con
comentario obligatorio citando el motivo. Añadir una excepción nueva en
el futuro requiere justificación escrita en este fichero. Si una capa
necesita >3 excepciones, revisar el diseño antes de ampliar la lista
(probablemente el movimiento reciente rompió la frontera).

Excepción a la regla "solo AppTest": invariante estructural puro sin
superficie Streamlit.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Reglas declarativas (capa → módulos top-level prohibidos)
# ---------------------------------------------------------------------------
# Clave: ruta relativa a src/ que cubre una capa completa o un conjunto de
# ficheros concretos. Valor: lista de módulos raíz (primer componente de
# ``from X.Y import Z``) que esa capa NO puede importar.
#
# Semántica "top-level": prohibir ``streamlit`` captura también
# ``streamlit.testing``; prohibir ``src.ui`` captura ``src.ui.session``.

_REGLAS: list[tuple[str, tuple[str, ...]]] = [
    # Dominio: ninguna dependencia externa al propio dominio.
    ("src/domain", (
        "streamlit", "clips", "sqlite3",
    )),
    # Aplicación: no toca UI ni widgets. Sí puede tocar dominio,
    # presupuesto (cálculos), reglas (decisor) e infraestructura (el
    # use case de historial tiene persistencia embebida — aceptado en
    # ADR-001 como transición pragmática).
    ("src/aplicacion", (
        "streamlit",
    )),
    # Presupuesto: cálculos por capítulo, sin CLIPS ni persistencia ni UI.
    ("src/presupuesto", (
        "streamlit", "clips", "sqlite3",
    )),
    # Infraestructura: adaptadores, no UI.
    ("src/infraestructura", (
        "streamlit",
    )),
]

# Ficheros bajo ``src/reglas`` con reglas específicas: solo
# ``alertas_clips.py`` puede importar ``clips`` (es su razón de ser).
_REGLAS_REGLAS: list[tuple[str, tuple[str, ...]]] = [
    ("src/reglas/decisor.py", ("streamlit", "clips", "sqlite3")),
    ("src/reglas/explicaciones.py", ("streamlit", "clips", "sqlite3")),
    ("src/reglas/normalizacion.py", ("streamlit", "clips", "sqlite3")),
    # Nota: elegibilidad.py y desempates.py se movieron a src/domain/reglas/
    # en Paso 2 de Fase 3. El chequeo de esa carpeta lo cubre la regla de
    # ``src/domain`` arriba.
    # templates.py carga las reglas CLIPS como strings; no ejecuta CLIPS.
    ("src/reglas/templates.py", ("streamlit", "sqlite3")),
    # motor.py y trazabilidad.py son shims de re-export: no tocan clips
    # directamente (re-exportan desde decisor/alertas_clips).
    ("src/reglas/motor.py", ("streamlit", "sqlite3")),
    ("src/reglas/trazabilidad.py", ("streamlit", "sqlite3")),
]


# ---------------------------------------------------------------------------
# Excepciones explícitas y justificadas
# ---------------------------------------------------------------------------
# Clave: (ruta_relativa_fichero, modulo_importado). Valor: razón.
# Añadir entradas aquí requiere comentario obligatorio.

_EXCEPCIONES: dict[tuple[str, str], str] = {
    ("src/reglas/alertas_clips.py", "clips"):
        "Razón de ser del fichero: es el único adaptador al motor CLIPS.",
}


# ---------------------------------------------------------------------------
# AST walk
# ---------------------------------------------------------------------------

def _imports_top_level(ruta: Path) -> list[tuple[int, str]]:
    """Devuelve lista de (línea, módulo_top_level) imports del fichero."""
    try:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    resultado: list[tuple[int, str]] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                top = alias.name.split(".")[0]
                resultado.append((nodo.lineno, top))
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                top = nodo.module.split(".")[0]
                resultado.append((nodo.lineno, top))
    return resultado


def _ficheros_bajo(directorio: str) -> list[Path]:
    ruta = _REPO_ROOT / directorio
    if not ruta.exists():
        return []
    return [p for p in ruta.rglob("*.py") if p.name != "__pycache__"]


def _ruta_relativa(fichero: Path) -> str:
    return str(fichero.relative_to(_REPO_ROOT)).replace("\\", "/")


# ---------------------------------------------------------------------------
# Tests parametrizados
# ---------------------------------------------------------------------------

def _violaciones(
    fichero: Path, prohibidos: tuple[str, ...]
) -> list[tuple[int, str]]:
    """Devuelve lista de (línea, módulo) que violan la regla, excluyendo excepciones."""
    rel = _ruta_relativa(fichero)
    out: list[tuple[int, str]] = []
    for lineno, top in _imports_top_level(fichero):
        if top not in prohibidos:
            continue
        if (rel, top) in _EXCEPCIONES:
            continue
        out.append((lineno, top))
    return out


@pytest.mark.parametrize("capa, prohibidos", _REGLAS)
def test_capa_no_cruza_frontera(capa: str, prohibidos: tuple[str, ...]):
    """Cada fichero ``.py`` bajo ``capa/`` no importa ningún módulo prohibido."""
    violaciones: list[str] = []
    for fichero in _ficheros_bajo(capa):
        for lineno, mod in _violaciones(fichero, prohibidos):
            violaciones.append(f"  {_ruta_relativa(fichero)}:{lineno} importa '{mod}'")

    if violaciones:
        msg = (
            f"Capa '{capa}' cruza fronteras prohibidas {list(prohibidos)}:\n"
            + "\n".join(violaciones)
            + "\n\nSi es intencional, mueve el fichero a la capa correcta o añade una "
            "excepción explícita en tests/test_fronteras_capas.py::_EXCEPCIONES "
            "con comentario justificativo."
        )
        pytest.fail(msg)


@pytest.mark.parametrize("ruta_fichero, prohibidos", _REGLAS_REGLAS)
def test_fichero_de_reglas_respeta_prohibiciones(
    ruta_fichero: str, prohibidos: tuple[str, ...],
):
    """Ficheros concretos bajo ``src/reglas/`` con sus prohibiciones específicas."""
    fichero = _REPO_ROOT / ruta_fichero
    if not fichero.exists():
        pytest.skip(f"{ruta_fichero} no existe")

    violaciones = _violaciones(fichero, prohibidos)
    if violaciones:
        msg = (
            f"{ruta_fichero} cruza frontera:\n"
            + "\n".join(f"  línea {l}: importa '{m}'" for l, m in violaciones)
            + "\n\nRevisar tests/test_fronteras_capas.py::_EXCEPCIONES si es intencional."
        )
        pytest.fail(msg)


def test_solo_alertas_clips_importa_clips():
    """Verificación positiva: exactamente 1 fichero en src/ importa ``clips``."""
    importadores: list[str] = []
    for fichero in _REPO_ROOT.joinpath("src").rglob("*.py"):
        for _, mod in _imports_top_level(fichero):
            if mod == "clips":
                importadores.append(_ruta_relativa(fichero))
                break
    assert importadores == ["src/reglas/alertas_clips.py"], (
        f"Solo 'src/reglas/alertas_clips.py' debe importar clips. Obtenido: {importadores}"
    )


def test_excepciones_documentadas_existen_realmente():
    """Cada entrada en _EXCEPCIONES corresponde a un import real (no dead config)."""
    for (ruta_rel, mod_esperado), razon in _EXCEPCIONES.items():
        assert razon, f"Excepción ({ruta_rel}, {mod_esperado}) sin razón documentada"
        fichero = _REPO_ROOT / ruta_rel
        assert fichero.exists(), f"Excepción apunta a fichero inexistente: {ruta_rel}"
        mods = {m for _, m in _imports_top_level(fichero)}
        assert mod_esperado in mods, (
            f"Excepción ({ruta_rel}, {mod_esperado}) no corresponde a un import real. "
            f"Posiblemente el fichero dejó de importarlo y la excepción es obsoleta."
        )
