"""Tests de la página Admin Precios - streamlit.testing.v1.AppTest."""

from __future__ import annotations

import pytest

from streamlit.testing.v1 import AppTest
from src.infraestructura.db import cargar_todo, guardar_todo


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Precios
# ═══════════════════════════════════════════════════════════════════════════════


def test_admin_carga():
    """La pagina de admin carga sin excepciones y tiene 19 number_inputs."""
    at = AppTest.from_file("pages/admin_precios.py").run()
    assert not at.exception
    assert len(at.number_input) == 19, (
        f"Esperados 19 number_input, encontrados {len(at.number_input)}"
    )


def test_admin_valor_invalido():
    """pct_gg=999 pasa el widget pero falla la validacion al guardar."""
    at = AppTest.from_file("pages/admin_precios.py").run()
    assert not at.exception

    # number_input[0] es "Gastos Generales (%)" - ponerlo a 999
    at.number_input[0].set_value(999.0).run()
    assert not at.exception

    # Clickar "Guardar cambios" → entra en modo confirmacion (st.rerun interno)
    at.button[0].click().run()

    # Ahora estamos en modo confirmacion.
    # at.button[0] = "Si, guardar" o "Guardar sin revisar"
    # Clickar para intentar guardar → guardar_precios() valida → ValueError → st.error
    at.button[0].click().run()

    # Debe haber al menos un mensaje de error (pct_gg=9.99 fuera de rango [0, 1])
    assert len(at.error) > 0, "Esperado error de validacion al guardar pct_gg=999"

    # Verificar que la DB NO fue modificada
    precios_db = cargar_todo()
    assert precios_db["pct_gg"] == pytest.approx(0.13, abs=0.001), (
        f"DB no deberia haber cambiado: pct_gg={precios_db['pct_gg']}"
    )


def test_admin_guardar_valido():
    """Cambiar GG de 13→14%, guardar, verificar en DB y restaurar."""
    # Leer valor original para restaurar despues
    precios_original = cargar_todo()
    gg_original = precios_original["pct_gg"]
    assert gg_original == pytest.approx(0.13, abs=0.001)

    try:
        at = AppTest.from_file("pages/admin_precios.py").run()
        assert not at.exception

        # Cambiar GG a 14%
        at.number_input[0].set_value(14.0).run()
        assert not at.exception

        # Clickar "Guardar cambios" → modo confirmacion
        at.button[0].click().run()

        # Clickar "Si, guardar"
        at.button[0].click().run()

        # Verificar en DB que se guardo correctamente
        precios_guardado = cargar_todo()
        assert precios_guardado["pct_gg"] == pytest.approx(0.14, abs=0.001), (
            f"Esperado pct_gg=0.14, encontrado {precios_guardado['pct_gg']}"
        )
    finally:
        # Restaurar valor original pase lo que pase
        precios_restore = cargar_todo()
        precios_restore["pct_gg"] = gg_original
        guardar_todo(precios_restore)

        # Verificar restauracion
        precios_check = cargar_todo()
        assert precios_check["pct_gg"] == pytest.approx(gg_original, abs=0.001)


def test_admin_expanders_y_subheaders():
    """La pagina de admin renderiza todas las secciones principales."""
    at = AppTest.from_file("pages/admin_precios.py").run()
    assert not at.exception

    # Verificar que los subheaders principales estan presentes
    subheaders_texto = " ".join(s.value for s in at.subheader).lower()
    secciones_esperadas = [
        "tuber",      # Tuberias ABA/SAN
        "entibaci",   # Entibacion
        "pozos",      # Pozos de registro
        "demolici",   # Demolicion ABA/SAN
        "acerado",    # Acerados
        "acometida",  # Acometidas
    ]
    for seccion in secciones_esperadas:
        assert seccion in subheaders_texto, (
            f"Seccion '{seccion}' no encontrada en subheaders: {subheaders_texto[:200]}"
        )


def test_admin_cancelar_no_guarda():
    """Cancelar en la pantalla de confirmacion no persiste cambios en DB."""
    precios_antes = cargar_todo()
    gg_antes = precios_antes["pct_gg"]

    at = AppTest.from_file("pages/admin_precios.py").run()
    assert not at.exception

    # Cambiar pct_gg a 14%
    at.number_input[0].set_value(14.0).run()
    assert not at.exception

    # Click "Guardar cambios" → entra en modo confirmacion (st.rerun interno)
    at.button[0].click().run()

    # En modo confirmacion: button[0]="Si, guardar", button[1]="Cancelar"
    # Clickar Cancelar → _reset_confirmacion() + rerun
    at.button[1].click().run()

    # Verificar que la DB NO cambio
    precios_despues = cargar_todo()
    assert precios_despues["pct_gg"] == pytest.approx(gg_antes, abs=0.001), (
        f"DB no deberia haber cambiado: antes={gg_antes}, despues={precios_despues['pct_gg']}"
    )


def test_admin_diff_muestra_cambios():
    """Modificar un precio y verificar que el dialogo de confirmacion muestra cambios."""
    precios_antes = cargar_todo()
    gg_antes = precios_antes["pct_gg"]

    try:
        at = AppTest.from_file("pages/admin_precios.py").run()
        assert not at.exception

        # Cambiar GG de 13% a 15%
        at.number_input[0].set_value(15.0).run()
        assert not at.exception

        # Click "Guardar cambios" → modo confirmacion con diff
        at.button[0].click().run()
        assert not at.exception

        # En modo confirmacion debe haber expanders (detalle de cambios)
        # y botones "Si, guardar" + "Cancelar"
        assert len(at.button) >= 2, \
            f"En confirmacion se esperan al menos 2 botones, encontrados {len(at.button)}"

        # Cancelar para no modificar DB
        at.button[1].click().run()
    finally:
        # Asegurar que DB no cambio
        precios_check = cargar_todo()
        if precios_check["pct_gg"] != pytest.approx(gg_antes, abs=0.001):
            precios_check["pct_gg"] = gg_antes
            guardar_todo(precios_check)
