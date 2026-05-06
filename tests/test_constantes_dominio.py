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

from src.modelo.constantes import PCT_CI_DEFAULT, TOLERANCIA_INVARIANTE_CI


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

def test_precios_py_no_tiene_1_05_literal_en_codigo_vivo():
    """``1.05`` debe aparecer solo en comentarios/docstrings, no en
    expresiones ejecutables, en los módulos de ``src/catalogo/``.

    Tras el rediseño, lo que era ``src/infraestructura/precios.py`` vive
    partido en ``src/catalogo/carga.py`` + ``src/catalogo/guardado.py``.
    El valor real lo aporta ``PCT_CI_DEFAULT`` (via import) y el dict de
    config en runtime.
    """
    paquete = _REPO_ROOT / "src" / "catalogo"
    ficheros = sorted(paquete.glob("*.py"))
    assert ficheros, f"paquete vacío: {paquete}"
    literales_encontrados: list[tuple[str, int, float]] = []
    for fichero in ficheros:
        arbol = ast.parse(fichero.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and nodo.value == 1.05:
                literales_encontrados.append((fichero.name, nodo.lineno, nodo.value))
    assert not literales_encontrados, (
        f"Literal 1.05 en código vivo de catálogo: {literales_encontrados}. "
        "Usar PCT_CI_DEFAULT de src.modelo.constantes."
    )
