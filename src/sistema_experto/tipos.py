"""Tipos compartidos del sistema experto.

`CadenaItem` modela un item de la cadena de inferencia que `explicar_alerta`
produce y que la UI / el historial consumen. Vive aquí (no en
`src.catalogo.editor.contratos`) porque es vocabulario propio del SE; la
ubicación previa creaba un acoplamiento inverso SE → catálogo.editor.
"""

from __future__ import annotations

from typing import Literal, TypedDict


class CadenaItem(TypedDict):
    """Un item de la cadena de inferencia del SE CLIPS, listo para mostrar/persistir."""
    capa: Literal[1, 2, 3]
    rule_id: str
    nivel: Literal["alerta", "etiqueta"]
    texto: str                    # texto multilinea pre-formateado para markdown
    fuente: str                   # cita normativa o "regla interna" / "provisional"
