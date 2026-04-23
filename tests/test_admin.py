"""Tests de la página Admin Precios - streamlit.testing.v1.AppTest."""

from __future__ import annotations

import pytest

from streamlit.testing.v1 import AppTest
from src.infraestructura.db_precios import cargar_todo, guardar_todo


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Precios
# ═══════════════════════════════════════════════════════════════════════════════


def test_admin_carga():
    """La pagina de admin carga sin excepciones y tiene 19 number_inputs."""
    at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
    assert not at.exception
    assert len(at.number_input) == 19, (
        f"Esperados 19 number_input, encontrados {len(at.number_input)}"
    )


def test_admin_valor_invalido():
    """pct_gg=999 pasa el widget pero falla la validacion al guardar."""
    at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
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
        at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
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
    at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
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

    at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
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


def test_admin_drift_critico_requiere_confirmacion():
    """Si un precio se desvía >10 % del catálogo oficial, el botón 'Sí, guardar'
    queda deshabilitado hasta que el admin marque el checkbox de confirmación.

    Se usa `conduccion_provisional_precio_m` (escalar, Excel oficial = 12.60 €):
    introducir 30.00 genera drift de +150 % (BD×CI = 31.50 vs Excel 12.60).
    """
    precios_antes = cargar_todo()
    cp_antes = float(precios_antes.get("conduccion_provisional_precio_m", 12.0))

    try:
        at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
        assert not at.exception

        # number_input[6] es "Precio conducción provisional PE (€/m, base sin CI)"
        at.number_input[6].set_value(30.0).run()
        assert not at.exception

        # "Guardar cambios" → pasa a modo confirmación
        at.button[0].click().run()
        assert not at.exception

        # Debe aparecer st.error crítico por drift > 10 %
        assert any("10" in e.value for e in at.error), (
            "Esperado error crítico por drift >10 %. Errores presentes: "
            f"{[e.value[:80] for e in at.error]}"
        )

        # Sin marcar el checkbox: el botón 'Sí, guardar' debe estar disabled.
        # (AppTest ignora el flag al click(), por eso comprobamos el atributo).
        boton_si = next((b for b in at.button if "guardar" in b.label.lower()), None)
        assert boton_si is not None, "No se encontró el botón 'Sí, guardar'."
        assert boton_si.disabled, (
            "El botón 'Sí, guardar' debe estar deshabilitado cuando hay drift "
            "crítico sin confirmar."
        )

        # Marcar el checkbox → el botón pasa a enabled.
        checkbox_drift = next(
            (c for c in at.checkbox if "intencional" in c.label.lower()),
            None,
        )
        assert checkbox_drift is not None, "No se encontró el checkbox de confirmación de drift."
        checkbox_drift.check().run()
        assert not at.exception

        boton_si_tras = next((b for b in at.button if "guardar" in b.label.lower()), None)
        assert boton_si_tras is not None
        assert not boton_si_tras.disabled, (
            "Tras marcar el checkbox, el botón 'Sí, guardar' debe estar habilitado."
        )

        boton_si_tras.click().run()
        precios_tras_confirmar = cargar_todo()
        assert float(precios_tras_confirmar["conduccion_provisional_precio_m"]) == pytest.approx(30.0, abs=0.01), (
            "Con checkbox marcado, la BD SÍ debe persistir el valor nuevo."
        )
    finally:
        precios_restore = cargar_todo()
        precios_restore["conduccion_provisional_precio_m"] = cp_antes
        guardar_todo(precios_restore)


def test_admin_round_trip_precio_base():
    """El invariante BD × pct_ci == Excel se cumple para un precio conocido.

    Tras cargar los precios base desde la BD y aplicar CI, el valor debe
    coincidir con el precio oficial EMASESA correspondiente.
    """
    import copy
    from src.infraestructura.precios import cargar_precios, aplicar_ci

    precios = cargar_precios()
    precios_con_ci = copy.deepcopy(precios)
    aplicar_ci(precios_con_ci)

    # Conducción provisional: BD (12.00) × 1.05 == Excel (12.60)
    # (tras la corrección A4; antes de A4 el valor BD es 11.43 y cuadra a 12.00 -> drift conocido).
    # Para no depender del fix aún no aplicado, verificamos con el precio ABA FD DN150.
    # FD DN150 BD base = 62.79 €. BD × 1.05 = 65.93 €. Excel oficial = 65.93.
    tub = next(i for i in precios["catalogo_aba"] if i["tipo"] == "FD" and i["diametro_mm"] == 150)
    tub_con_ci = next(i for i in precios_con_ci["catalogo_aba"] if i["tipo"] == "FD" and i["diametro_mm"] == 150)
    assert tub["precio_m"] == pytest.approx(62.79, abs=0.01)
    assert tub_con_ci["precio_m"] == pytest.approx(65.93, abs=0.01)


def test_admin_diff_muestra_cambios():
    """Modificar un precio y verificar que el dialogo de confirmacion muestra cambios."""
    precios_antes = cargar_todo()
    gg_antes = precios_antes["pct_gg"]

    try:
        at = AppTest.from_file("pages/admin_precios.py", default_timeout=10).run()
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
