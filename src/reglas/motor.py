"""
Shim de compatibilidad del antiguo ``src.reglas.motor``.

El contenido real se dividió en dos módulos que reflejan los dos roles que
antes convivían aquí con nombre engañoso:

- ``src.reglas.decisor.resolver_decisiones`` → selección determinista de
  materiales (Python puro, sin CLIPS).
- ``src.reglas.alertas_clips.generar_alertas_tecnicas`` → motor CLIPS que
  emite alertas técnicas (antiguo ``evaluar_sistema_experto``).

Este fichero se conserva solo para que imports externos legacy sigan
funcionando. En código nuevo, importa desde los módulos nuevos directamente.
"""

from __future__ import annotations

from src.reglas.decisor import resolver_decisiones
from src.reglas.alertas_clips import (
    generar_alertas_tecnicas,
    generar_alertas_tecnicas as evaluar_sistema_experto,
)

__all__ = [
    "resolver_decisiones",
    "generar_alertas_tecnicas",
    "evaluar_sistema_experto",
]
