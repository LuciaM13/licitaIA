"""Tests de la ancla canónica de constantes del dominio (Paso 1 de Fase 3).

Verifica que:
  - ``PCT_CI_DEFAULT`` tiene el valor canónico de EMASESA (1.05).
  - Las migraciones que corrigen drifts del CI y la lógica runtime
    **importan la constante**, no duplican el literal.

Excepción documentada: ``src/infraestructura/precios.py:225`` conserva el
literal ``1.0`` como *fallback neutral* cuando el dict de precios no
incluye la clave ``pct_ci``. Ese 1.0 significa "no aplicar CI", no es el
valor por defecto de EMASESA, y por tanto no debe sustituirse por
``PCT_CI_DEFAULT``.
"""
from __future__ import annotations

import ast
from pathlib import Path

from src.domain.constantes import PCT_CI_DEFAULT, TOLERANCIA_INVARIANTE_CI


_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Valores canónicos
# ---------------------------------------------------------------------------

def test_pct_ci_default_vale_1_05():
    assert PCT_CI_DEFAULT == 1.05, (
        f"PCT_CI_DEFAULT debe ser 1.05 (invariante EMASESA). "
        f"Obtenido: {PCT_CI_DEFAULT}"
    )


def test_tolerancia_invariante_ci_razonable():
    # 0.005 € = medio céntimo. Coincide con la guarda histórica de M8/M10.
    assert 0.001 <= TOLERANCIA_INVARIANTE_CI <= 0.01


# ---------------------------------------------------------------------------
# La constante se usa (no se duplica el literal) en callers clave
# ---------------------------------------------------------------------------

def _fichero_usa_constante(ruta: Path, nombre_constante: str) -> bool:
    """Verifica que el fichero importa la constante por su nombre."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            if (nodo.module or "").startswith("src.domain.constantes"):
                for alias in nodo.names:
                    if alias.name == nombre_constante:
                        return True
    return False


def test_m15_usa_pct_ci_default():
    fichero = (_REPO_ROOT / "src" / "infraestructura" / "db"
               / "migrations" / "m15_demolicion_material.py")
    assert _fichero_usa_constante(fichero, "PCT_CI_DEFAULT"), (
        "M15 debe importar PCT_CI_DEFAULT en vez de usar el literal 1.05 "
        "al dividir precios Excel. El literal duplica la fuente de verdad."
    )


def test_precios_py_no_tiene_1_05_literal_en_codigo_vivo():
    """``1.05`` debe aparecer solo en comentarios/docstrings, no en
    expresiones ejecutables, dentro de ``src/infraestructura/precios.py``.
    El valor real lo aporta ``PCT_CI_DEFAULT`` (via import) y el dict de
    config en runtime."""
    fichero = _REPO_ROOT / "src" / "infraestructura" / "precios.py"
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    literales_encontrados: list[tuple[int, float]] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and nodo.value == 1.05:
            literales_encontrados.append((nodo.lineno, nodo.value))
    assert not literales_encontrados, (
        f"Literal 1.05 en código vivo de precios.py: {literales_encontrados}. "
        "Usar PCT_CI_DEFAULT de src.domain.constantes."
    )
