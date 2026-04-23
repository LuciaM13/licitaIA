"""Test de no-regresión: un presupuesto guardado es inmutable.

Excepción a la regla "solo AppTest": este test verifica un invariante de la
capa de persistencia (garantía legal TFG) sin pasar por Streamlit. Se ejecuta
con `pytest` puro.

Invariante verificado:
    Un presupuesto guardado en `data/precios.db` mantiene exactamente los
    mismos importes y totales al consultarlo, aunque entre tanto se hayan
    modificado los precios unitarios en las tablas de catálogo (tuberías,
    acometidas, etc.). El historial es un snapshot, no un recálculo en vivo.

Cómo se implementa:
  1. Copia de `data/precios.db` a `tmp_path/precios.db` (aislada).
  2. Conexión A: `guardar_presupuesto()` escribe un presupuesto con un
     resultado conocido.
  3. Conexión B: UPDATE directo en tabla `tuberias` duplicando un precio.
  4. Conexión C: `obtener_presupuesto()` devuelve el presupuesto frozen.
  5. Se verifica que todos los importes y totales son idénticos al guardado.

Si este test falla, significa que el historial está recalculando en vivo
con los precios actuales, lo que sería un bug legal grave.
"""

from __future__ import annotations

import shutil
import sqlite3

import pytest

from src.infraestructura.db import DB_PATH
from src.aplicacion.historial import (
    guardar_presupuesto, obtener_presupuesto, eliminar_presupuesto,
)
from tests.helpers import _resultado_minimal


@pytest.fixture
def bd_aislada(tmp_path):
    """Copia data/precios.db a tmp_path y devuelve la ruta. Evita contaminar prod."""
    destino = tmp_path / "precios.db"
    shutil.copy(DB_PATH, destino)
    return destino


def test_presupuesto_historico_inmune_a_cambio_precios(bd_aislada):
    """Guardar presupuesto → mutar precios BD → leer historial: importes congelados."""

    # (1) Guardar el presupuesto en la BD aislada.
    resultado = _resultado_minimal()
    parametros = {
        "aba_longitud_m": "100",
        "aba_profundidad_m": "2.0",
        "aba_diametro_mm": "150",
    }
    id_p = guardar_presupuesto(
        resultado, parametros,
        descripcion="snapshot test",
        pct_ci=1.05,
        path=bd_aislada,
    )
    assert id_p > 0

    try:
        # (2) Mutar directamente un precio de tubería usando una conexión separada.
        with sqlite3.connect(str(bd_aislada)) as conn_mut:
            antes = conn_mut.execute(
                "SELECT precio_m FROM tuberias WHERE red='ABA' AND tipo='FD' AND diametro_mm=150"
            ).fetchone()
            assert antes is not None, "BD aislada incompleta: falta tubería FD DN150"
            nuevo_precio_cents = antes[0] * 10  # ×10 es suficientemente agresivo
            conn_mut.execute(
                "UPDATE tuberias SET precio_m=? "
                "WHERE red='ABA' AND tipo='FD' AND diametro_mm=150",
                (nuevo_precio_cents,),
            )
            conn_mut.commit()
            despues = conn_mut.execute(
                "SELECT precio_m FROM tuberias WHERE red='ABA' AND tipo='FD' AND diametro_mm=150"
            ).fetchone()[0]
            assert despues == nuevo_precio_cents, "El UPDATE de precio no persistió"

        # (3) Tercera conexión: cargar el presupuesto del historial.
        detalle = obtener_presupuesto(id_p, path=bd_aislada)
        assert detalle is not None, "El presupuesto recién guardado no se recupera"

        # (4) Asertos: los totales coinciden exactamente con los de guardado.
        for campo in ("pem", "gg", "bi", "pbl_sin_iva", "iva", "total"):
            assert detalle[campo] == pytest.approx(resultado[campo], abs=0.01), (
                f"{campo} cambió tras mutar precios: "
                f"guardado={resultado[campo]}, historial={detalle[campo]}"
            )

        # Capítulos / partidas frozen
        for cap_nombre, cap_info_esperado in resultado["capitulos"].items():
            cap_info_real = detalle["capitulos"].get(cap_nombre)
            assert cap_info_real is not None, f"Falta capítulo '{cap_nombre}' en historial"
            assert cap_info_real["subtotal"] == pytest.approx(cap_info_esperado["subtotal"], abs=0.01)
            for desc, importe in cap_info_esperado["partidas"].items():
                assert cap_info_real["partidas"].get(desc) == pytest.approx(importe, abs=0.01), (
                    f"Partida '{desc}' cambió tras mutar precios."
                )
    finally:
        eliminar_presupuesto(id_p, path=bd_aislada)
