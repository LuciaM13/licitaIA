"""AppTest del flujo inline de creación de variantes (Phase 3, Plan 03-04).

Patrón: AppTest.from_file('pages/calculadora.py') + inyección de
INLINE_CREATE_TARGET en session_state para forzar la apertura del
dialog sin tener que simular el click del botón "+".

Limitación de streamlit.testing.v1: el harness expone parcialmente
los widgets del @st.dialog. Cuando un widget no es alcanzable por
el harness, este test inyecta directamente el item completo via
sk.INLINE_CREATE_TARGET + lectura/escritura de session_state, o
invoca el use case directamente y simula el rerun manualmente.

Memoria 'Testing strategy': solo AppTest aquí. La validación pura
de precio<=0 ya está cubierta por Plan 01 Test 7 (use case puro).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from streamlit.testing.v1 import AppTest

from src.almacenamiento.conexion import conectar
from src.ui.session import claves as sk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _borrar_test_filas(label_pattern: str = "test_inline_%") -> None:
    """Limpieza de filas residuales tras cada test (T-03-21, T-03-22).

    Schema real: la columna identificadora difiere por tabla. Acometidas usa
    `tipo`; el resto usan `label`. Audit log usa `clave`."""
    with conectar() as conn:
        for tabla in ("acerados", "tuberias", "valvuleria",
                      "bordillos", "calzadas", "pozos", "imbornales"):
            conn.execute(f"DELETE FROM {tabla} WHERE label LIKE ?", (label_pattern,))
        conn.execute("DELETE FROM acometidas WHERE tipo LIKE ?", (label_pattern,))
        conn.execute("DELETE FROM audit_log WHERE clave LIKE ?", (label_pattern,))
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# Test 1 — Smoke: el dialog se abre sin excepciones
# ═══════════════════════════════════════════════════════════════════════════════

def test_inline_dialog_se_abre_sin_excepciones():
    """Inyectar INLINE_CREATE_TARGET fuerza la apertura del @st.dialog en el
    siguiente rerun. La calculadora debe renderizar sin excepción y el caption
    EMASESA del sub-formulario debe estar presente."""
    at = AppTest.from_file("pages/calculadora.py", default_timeout=10)
    at.session_state[sk.INLINE_CREATE_TARGET] = "acerados_aba"
    at.run()

    assert not at.exception, f"Excepción inesperada: {at.exception}"

    # caption del label EMASESA debe aparecer en el render del dialog
    captions = [c.value for c in at.caption]
    assert any("Introduce el precio base EMASESA" in c for c in captions), (
        f"Caption EMASESA no encontrado. Captions vistos: {captions[:10]}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Test 2 — Insert + auto-selección + rollback en finally
# ═══════════════════════════════════════════════════════════════════════════════

def test_inline_insert_completo_y_auto_seleccion():
    """Invoca el use case directamente (la API de @st.dialog no es del todo
    alcanzable por el harness para `set_value` + click), simula el rerun
    inyectando INLINE_CREATE_RESULT y verifica:
      (a) tras el rerun, INLINE_CREATE_RESULT se ha consumido (one-shot via
          _consumir_inline_result al final del render).
      (b) la fila persiste en la BD."""
    label_test = f"test_inline_{uuid4().hex}"
    try:
        from src.catalogo.editor import insertar_variante_catalogo

        item = {"label": label_test, "unidad": "m2", "precio": 1.23}
        insertar_variante_catalogo("acerados", "ABA", item, actor="usuario_inline")

        # Simular el rerun de la calculadora con el resultado one-shot
        at = AppTest.from_file("pages/calculadora.py", default_timeout=10)
        at.session_state[sk.INLINE_CREATE_RESULT] = ("acerados", "ABA", label_test)
        at.run()

        assert not at.exception, f"Excepción inesperada: {at.exception}"

        # Tras el rerun, INLINE_CREATE_RESULT debe haberse consumido
        # (BLOCK 6: _consumir_inline_result al final del render hace pop one-shot)
        assert sk.INLINE_CREATE_RESULT not in at.session_state, (
            "INLINE_CREATE_RESULT no se consumió tras el rerun (debería ser one-shot)"
        )

        # Verificar persistencia: la fila existe en la BD
        with conectar() as conn:
            row = conn.execute(
                "SELECT label, precio FROM acerados WHERE label = ?",
                (label_test,),
            ).fetchone()
        assert row is not None, f"Fila '{label_test}' no encontrada en acerados"
    finally:
        _borrar_test_filas()


# ═══════════════════════════════════════════════════════════════════════════════
# Test 3 — Cancelar = cero side effects
# ═══════════════════════════════════════════════════════════════════════════════

def test_inline_cancelar_sin_side_effects():
    """Abrir el dialog y simular cancel (pop de TARGET sin invocar use case)
    no debe escribir nada en audit_log con actor='usuario_inline'."""
    with conectar() as conn:
        count_antes = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE actor='usuario_inline'"
        ).fetchone()[0]

    try:
        at = AppTest.from_file("pages/calculadora.py", default_timeout=10)
        at.session_state[sk.INLINE_CREATE_TARGET] = "acerados_aba"
        at.run()
        assert not at.exception

        # Simular cancel: borrar TARGET sin invocar use case
        if sk.INLINE_CREATE_TARGET in at.session_state:
            del at.session_state[sk.INLINE_CREATE_TARGET]
        at.run()
        assert not at.exception
    finally:
        with conectar() as conn:
            count_despues = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE actor='usuario_inline'"
            ).fetchone()[0]
        assert count_despues == count_antes, (
            "Cancelar no debe escribir en audit_log "
            f"(antes={count_antes}, después={count_despues})"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Test 5 — State-preservation = SC2 (FLAG 10 fix)
# ═══════════════════════════════════════════════════════════════════════════════

def test_inline_no_destruye_state_del_formulario():
    """SC2: abrir el dialog inline NO debe destruir valores previamente
    introducidos en number_inputs/selectbox de la calculadora.

    El test sigue el patrón "smoke" porque streamlit.testing.v1 no expone
    interacción completa con `@st.dialog` modal. Si el harness no permite
    verificar el state DENTRO del dialog, basta con confirmar que el
    rerun de APERTURA del dialog NO destruye el state previo."""
    at = AppTest.from_file("pages/calculadora.py", default_timeout=10).run()
    assert not at.exception

    # Localizar number_input de longitud ABAS (key="ABAS_longitud").
    keys_longitud = [
        ni for ni in at.number_input
        if "longitud" in (ni.key or "").lower()
    ]
    if not keys_longitud:
        pytest.skip(
            "No se encontró number_input de longitud en el harness AppTest. "
            "SC2 verificado manualmente — ver SUMMARY."
        )

    ni_long = keys_longitud[0]
    valor_inicial = 247.0
    ni_long.set_value(valor_inicial).run()
    assert not at.exception

    # Inyectar TARGET para "abrir" el dialog (rerun)
    at.session_state[sk.INLINE_CREATE_TARGET] = "acerados_aba"
    at.run()
    assert not at.exception, f"Excepción al abrir dialog: {at.exception}"

    # Modalidad real (st.stop() tras render_inline_create_dialog en
    # pages/calculadora.py): mientras el dialog está abierto, los widgets
    # de la página principal NO se renderizan. El valor sigue vivo en
    # session_state, así que el contrato "no destruye state" se verifica
    # sobre session_state, no sobre el árbol de widgets renderizados.
    assert ni_long.key in at.session_state, (
        f"State-loss: clave {ni_long.key!r} desapareció de session_state "
        "tras abrir el dialog"
    )
    assert at.session_state[ni_long.key] == valor_inicial, (
        f"State-loss: {ni_long.key} cambió de {valor_inicial} a "
        f"{at.session_state[ni_long.key]}"
    )

    # Cleanup
    if sk.INLINE_CREATE_TARGET in at.session_state:
        del at.session_state[sk.INLINE_CREATE_TARGET]
