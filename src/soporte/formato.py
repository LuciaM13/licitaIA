"""Formato de cifras para UI y exportación.

Funciones puras de presentación, sin dependencias de Streamlit. Vive aquí
(no en `src/ui/`) para que `src/exportar/` y otros módulos no-UI puedan
formatear cifras sin importar de la capa de presentación.
"""

from __future__ import annotations


def euro(valor: float) -> str:
    """Formatea un número como moneda española (1.234,56 €)."""
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
