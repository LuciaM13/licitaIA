"""Re-export para retrocompatibilidad.

La función `euro()` se ha movido a `src.soporte.formato` para desacoplarla
de la capa UI (es función pura sin Streamlit). Este módulo re-exporta el
nombre para no romper importadores existentes.
"""

from __future__ import annotations

from src.soporte.formato import euro  # noqa: F401

__all__ = ["euro"]
