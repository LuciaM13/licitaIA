"""Bloques de ensamblaje del presupuesto.

Cada función ``ensamblar_*`` construye un capítulo del presupuesto
llamando a las funciones de cálculo de ``capitulos_obra_civil`` y
``capitulos_superficie``, y acumula los resultados en el dict ``caps``
compartido por ``calcular_presupuesto``.

El orquestador (``src.presupuesto.orquestador``) decide el orden
de invocación; este subpaquete solo expone los bloques.
"""

from __future__ import annotations

from src.presupuesto.bloques.acometidas_y_ss import (
    ensamblar_acometidas,
    ensamblar_seguridad_gestion,
)
from src.presupuesto.bloques.obra_civil import (
    ensamblar_obra_civil_aba,
    ensamblar_obra_civil_san,
)
from src.presupuesto.bloques.pavimentacion import (
    ensamblar_pavimentacion_aba,
    ensamblar_pavimentacion_san,
)

__all__ = [
    "ensamblar_acometidas",
    "ensamblar_obra_civil_aba",
    "ensamblar_obra_civil_san",
    "ensamblar_pavimentacion_aba",
    "ensamblar_pavimentacion_san",
    "ensamblar_seguridad_gestion",
]
