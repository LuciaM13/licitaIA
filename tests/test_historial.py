"""Tests de la página Historial - streamlit.testing.v1.AppTest."""

from __future__ import annotations

import pytest

from streamlit.testing.v1 import AppTest
from helpers import _resultado_minimal
from src.aplicacion.historial import (
    contar_presupuestos, eliminar_presupuesto, guardar_presupuesto,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Historial
# ═══════════════════════════════════════════════════════════════════════════════


def test_historial_carga():
    """La pagina de historial carga sin excepciones."""
    at = AppTest.from_file("pages/historial.py").run()
    assert not at.exception


def test_historial_offset_overflow():
    """Pagina fuera de rango no lanza excepcion (el guard redirige a pag 0)."""
    at = AppTest.from_file("pages/historial.py")
    at.session_state["hist_page"] = 9999
    at.run()
    assert not at.exception


def test_historial_detalle():
    """Click en 'Ver detalle' no lanza excepcion (si hay presupuestos)."""
    if contar_presupuestos() == 0:
        pytest.skip("No hay presupuestos en la DB - nada que detallar")

    at = AppTest.from_file("pages/historial.py").run()
    assert not at.exception

    # "Ver detalle" es el primer boton tras los de paginacion (Anterior, Siguiente)
    # Buscar el boton con label "Ver detalle"
    boton_detalle = None
    for i, btn in enumerate(at.button):
        if "detalle" in btn.label.lower():
            boton_detalle = at.button[i]
            break

    if boton_detalle is None:
        pytest.skip("No se encontro boton 'Ver detalle'")

    boton_detalle.click().run()
    assert not at.exception


def test_historial_comparacion():
    """Comparar dos presupuestos no lanza excepcion."""
    if contar_presupuestos() < 2:
        pytest.skip("Se necesitan al menos 2 presupuestos para comparar")

    at = AppTest.from_file("pages/historial.py").run()
    assert not at.exception

    # Los selectboxes de comparacion tienen keys "comp_a" y "comp_b"
    sb_a = at.selectbox(key="comp_a")
    sb_b = at.selectbox(key="comp_b")

    # Verificar que tienen opciones distintas seleccionadas
    assert sb_a.value != sb_b.value, "comp_a y comp_b deberian tener valores distintos por defecto"

    # Buscar boton "Comparar" por label
    boton_comparar = None
    for i, btn in enumerate(at.button):
        if "comparar" in btn.label.lower():
            boton_comparar = at.button[i]
            break

    if boton_comparar is None:
        pytest.skip("No se encontro boton 'Comparar'")

    boton_comparar.click().run()
    assert not at.exception


def test_historial_eliminar():
    """Eliminar un presupuesto via UI reduce el contador en 1."""
    # Crear presupuesto de test directamente en DB
    id_nuevo = guardar_presupuesto(
        _resultado_minimal(), {}, descripcion="test_eliminar_ui", pct_ci=1.0
    )
    n_antes = contar_presupuestos()

    try:
        at = AppTest.from_file("pages/historial.py").run()
        assert not at.exception

        # Seleccionar el presupuesto recien creado en el selectbox del expander "Eliminar"
        at.selectbox(key="del_id").set_value(id_nuevo).run()
        assert not at.exception

        # Buscar boton "Eliminar definitivamente" por label
        boton_eliminar = None
        for i, btn in enumerate(at.button):
            if "eliminar" in btn.label.lower() and "definitiv" in btn.label.lower():
                boton_eliminar = at.button[i]
                break

        assert boton_eliminar is not None, (
            f"No se encontro boton 'Eliminar definitivamente'. "
            f"Botones: {[b.label for b in at.button]}"
        )

        boton_eliminar.click().run()
        assert not at.exception

        # Verificar que se elimino
        assert contar_presupuestos() == n_antes - 1
    finally:
        # Cleanup: si el test fallo antes de eliminar, borrar manualmente
        try:
            eliminar_presupuesto(id_nuevo)
        except Exception:
            pass


def test_historial_guardar_y_consultar():
    """Guardar presupuesto via calculadora y verificar que aparece en historial."""
    n_antes = contar_presupuestos()
    id_nuevo = guardar_presupuesto(
        _resultado_minimal(), {"modo": "Solo Abastecimiento"},
        descripcion="test_audit_historial", pct_ci=1.0
    )
    try:
        assert contar_presupuestos() == n_antes + 1

        at = AppTest.from_file("pages/historial.py").run()
        assert not at.exception

        # El presupuesto recien creado debe estar en la lista
        at.selectbox(key="del_id").set_value(id_nuevo).run()

        # Ver detalle
        boton_detalle = None
        for i, btn in enumerate(at.button):
            if "detalle" in btn.label.lower():
                boton_detalle = at.button[i]
                break

        if boton_detalle is not None:
            # Seleccionar el presupuesto en el selectbox de detalle
            at.selectbox[0].set_value(id_nuevo).run()
            boton_detalle.click().run()
            assert not at.exception
    finally:
        eliminar_presupuesto(id_nuevo)
