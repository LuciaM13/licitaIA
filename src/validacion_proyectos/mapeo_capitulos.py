"""Mapeo entre numeracion de capitulos EMASESA y nombres canonicos LicitaIA.

Los nombres canonicos se obtienen del codigo real de los bloques en
src/presupuesto/bloques/ (verificado al implementar). El orquestador numera
los capitulos por orden de insercion y prefija con "NN " (ej. "01 OBRA CIVIL
ABASTECIMIENTO"); aqui trabajamos sin ese prefijo y por nombre canonico.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# Nombres canonicos verificados contra src/presupuesto/bloques/*.py:
#   obra_civil.py:       "OBRA CIVIL ABASTECIMIENTO", "OBRA CIVIL SANEAMIENTO"
#   pavimentacion.py:    "PAVIMENTACION ABASTECIMIENTO", "PAVIMENTACION SANEAMIENTO"
#   acometidas_y_ss.py:  "ACOMETIDAS ABASTECIMIENTO", "ACOMETIDAS SANEAMIENTO",
#                        "SEGURIDAD Y SALUD", "GESTION AMBIENTAL"
# Nota: los strings reales en los bloques usan "PAVIMENTACION" con tilde
# ("PAVIMENTACIÓN") y "GESTION AMBIENTAL" con tilde ("GESTIÓN AMBIENTAL").
MAPEO_EMASESA_LICITAIA: dict[str, str] = {
    "01": "OBRA CIVIL ABASTECIMIENTO",
    "02": "OBRA CIVIL SANEAMIENTO",
    "03": "PAVIMENTACIÓN ABASTECIMIENTO",
    "04": "PAVIMENTACIÓN SANEAMIENTO",
    "05": "ACOMETIDAS ABASTECIMIENTO",
    "06": "ACOMETIDAS SANEAMIENTO",
    "07": "SEGURIDAD Y SALUD",
    "08": "GESTIÓN AMBIENTAL",
}

CAPITULOS_FUERA_ALCANCE: frozenset[str] = frozenset({"11"})


def normalizar_capitulos_licitaia(resultado: dict[str, Any]) -> dict[str, float]:
    """Quita el prefijo 'NN ' del nombre del capitulo y devuelve {nombre: subtotal}."""
    capitulos = resultado.get("capitulos", {})
    out: dict[str, float] = {}
    for nombre_completo, datos in capitulos.items():
        partes = nombre_completo.split(" ", 1)
        nombre_canonico = partes[1] if len(partes) == 2 and partes[0].isdigit() else nombre_completo
        out[nombre_canonico] = float(datos.get("subtotal", 0.0))
    logger.info("normalizar_capitulos_licitaia -> %d capitulos", len(out))
    return out
