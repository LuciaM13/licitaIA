"""Tests de la capa ``src.aplicacion`` tras la Fase 3.

Verifica:
  - Los 3 use cases están accesibles bajo ``src.aplicacion``.
  - ``contratos.py`` expone ``ResultadoPreparacion`` con el shape acordado.
  - ``preparar_guardado()`` devuelve un dict con las 4 claves del contrato.
  - Los módulos de aplicación no importan Streamlit.

Excepción a la regla "solo AppTest": tests de contrato puros.
"""
from __future__ import annotations

import ast
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Los 3 use cases son importables
# ---------------------------------------------------------------------------

def test_calcular_presupuesto_vive_en_aplicacion():
    from src.aplicacion.calcular_presupuesto import calcular_presupuesto
    assert callable(calcular_presupuesto)


def test_historial_expone_api_completa():
    from src.aplicacion.historial import (
        guardar_presupuesto, listar_presupuestos,
        obtener_presupuesto, eliminar_presupuesto, contar_presupuestos,
    )
    for fn in (guardar_presupuesto, listar_presupuestos,
               obtener_presupuesto, eliminar_presupuesto, contar_presupuestos):
        assert callable(fn)


def test_editar_catalogo_expone_use_case():
    from src.aplicacion.editar_catalogo import preparar_guardado, ejecutar_guardado
    assert callable(preparar_guardado)
    assert callable(ejecutar_guardado)


# ---------------------------------------------------------------------------
# Contrato ResultadoPreparacion
# ---------------------------------------------------------------------------

def test_resultado_preparacion_contrato_estable():
    from src.aplicacion.contratos import (
        ResultadoPreparacion, ErrorValidacion, CambioPrecio, DriftOficial,
    )
    # Claves del contrato de caso de uso.
    claves = set(ResultadoPreparacion.__annotations__)
    assert claves == {"errores", "diff", "drifts", "puede_guardar"}, claves

    # Los 3 TypedDict anidados existen con sus campos.
    assert "campo" in ErrorValidacion.__annotations__
    assert "mensaje" in ErrorValidacion.__annotations__
    assert "categoria" in CambioPrecio.__annotations__
    assert "categoria" in DriftOficial.__annotations__


def test_preparar_guardado_sin_cambios_devuelve_shape_correcto():
    """Llamar ``preparar_guardado`` con dos dicts iguales devuelve un
    ``ResultadoPreparacion`` válido: sin errores, sin diff, puede_guardar=True."""
    from src.aplicacion.editar_catalogo import preparar_guardado
    from src.infraestructura.precios import cargar_precios

    precios = cargar_precios()
    resultado = preparar_guardado(precios, precios)

    assert isinstance(resultado, dict)
    assert set(resultado.keys()) == {"errores", "diff", "drifts", "puede_guardar"}
    assert resultado["errores"] == []
    assert resultado["diff"] == []
    assert isinstance(resultado["drifts"], list)
    assert resultado["puede_guardar"] is True


# ---------------------------------------------------------------------------
# Pureza: no importa Streamlit
# ---------------------------------------------------------------------------

def _importa(fichero: Path, modulo: str) -> bool:
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


def test_editar_catalogo_no_importa_streamlit():
    fichero = _REPO_ROOT / "src" / "aplicacion" / "editar_catalogo.py"
    assert not _importa(fichero, "streamlit"), (
        "editar_catalogo.py es un use case; Streamlit pertenece a la UI."
    )


def test_calcular_presupuesto_no_importa_streamlit():
    fichero = _REPO_ROOT / "src" / "aplicacion" / "calcular_presupuesto.py"
    assert not _importa(fichero, "streamlit")


def test_contratos_no_importa_streamlit_ni_sqlite():
    fichero = _REPO_ROOT / "src" / "aplicacion" / "contratos.py"
    assert not _importa(fichero, "streamlit")
    assert not _importa(fichero, "sqlite3")
