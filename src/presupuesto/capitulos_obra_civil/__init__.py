"""Capítulos de obra civil.

Cada función recibe cantidades y precios ya resueltos y devuelve
``(subtotal, partidas)`` o ``(subtotal, partidas, auxiliares)`` cuando
aplica. Las decisiones de elegibilidad y desempate viven en
``src.sistema_experto`` (el motor ya las resolvió cuando se llama aquí).

Frontera de capas:
  - SÍ importa de ``src.modelo`` (geometría, tipos).
  - NO importa de ``src.sistema_experto`` ni de ``streamlit``.
"""

from __future__ import annotations

from src.presupuesto.capitulos_obra_civil._helpers import _importe
from src.presupuesto.capitulos_obra_civil.accesorios import (
    capitulo_desmontaje,
    capitulo_imbornales,
    capitulo_valvuleria,
)
from src.presupuesto.capitulos_obra_civil.excavacion import capitulo_obra_civil
from src.presupuesto.capitulos_obra_civil.pozos_y_canones import (
    capitulo_canones,
    capitulo_pozos_existentes,
    capitulo_pozos_registro,
)

__all__ = [
    "_importe",
    "capitulo_canones",
    "capitulo_desmontaje",
    "capitulo_imbornales",
    "capitulo_obra_civil",
    "capitulo_pozos_existentes",
    "capitulo_pozos_registro",
    "capitulo_valvuleria",
]
