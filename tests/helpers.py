"""Helpers compartidos para tests de LicitaIA."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest


def _app_calculadora() -> AppTest:
    """Crea un AppTest fresco apuntando a la calculadora."""
    return AppTest.from_file("pages/calculadora.py")


def _calcular_aba(at: AppTest, *, dn: int = 100, longitud: float = 50.0,
                  profundidad: float = 1.0) -> AppTest:
    """Configura inputs ABA minimos y pulsa Calcular."""
    at.number_input(key="ABAS_longitud").set_value(longitud)
    at.number_input(key="ABAS_profundidad").set_value(profundidad)
    at.selectbox(key="ABAS_diametro").set_value(dn)
    at.run()
    at.button(key="btn_calcular").click().run()
    return at


def _calcular_san(at: AppTest, *, dn: int = 300, longitud: float = 50.0,
                  profundidad: float = 1.5) -> AppTest:
    """Configura inputs SAN minimos y pulsa Calcular."""
    at.number_input(key="SAN_longitud").set_value(longitud)
    at.number_input(key="SAN_profundidad").set_value(profundidad)
    at.selectbox(key="SAN_diametro").set_value(dn)
    at.run()
    at.button(key="btn_calcular").click().run()
    return at


def _resultado_minimal() -> dict:
    """Dict resultado minimo valido para insertar en DB sin pasar por la UI."""
    return {
        "capitulos": {
            "01 OBRA CIVIL ABASTECIMIENTO": {
                "subtotal": 1000.0,
                "partidas": {"Test partida": 1000.0},
            }
        },
        "pem": 1000.0,
        "gg": 113.4,
        "bi": 52.2,
        "pbl_sin_iva": 1170.0,
        "iva": 245.7,
        "total": 1415.7,
        "pcts": {"gg": 0.13, "bi": 0.06, "iva": 0.21},
        "pct_seguridad_info": 0.0,
        "pct_gestion_info": 0.0,
        "auxiliares": {"aba": {}, "san": {}},
        "trazabilidad": {},
    }
