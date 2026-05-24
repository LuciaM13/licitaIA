"""Use case: editar el catálogo de precios desde la UI admin.

APIs públicas:
  - ``preparar_guardado(editados, originales)`` — valida y calcula diff sin
    escribir. La UI usa el resultado para mostrar el diálogo de confirmación
    y bloquear el guardado si hay errores.
  - ``ejecutar_guardado(editados)`` — persiste tras confirmación. Propaga
    ``ValueError`` si la validación final falla o la BD rechaza los datos.
  - ``insertar_variante_catalogo(tabla, red, item, actor)`` — inserta UNA
    variante nueva en un catálogo desde la calculadora con validaciones de
    negocio (Phase 3, plan inline).
  - ``insertar_calzada_con_espesor(item, espesor_m, actor)`` — inserta una
    calzada en m³ + su espesor en una transacción atómica.

No importa Streamlit. Los widgets de ``pages/configuracion_catalogo.py`` y
``pages/calculadora.py`` invocan estos use cases y consumen el shape
``ResultadoPreparacion`` declarado en ``src.catalogo.editor.contratos``.
"""

from __future__ import annotations

from src.catalogo.editor.insercion_calzada import insertar_calzada_con_espesor
from src.catalogo.editor.insercion_variante import insertar_variante_catalogo
from src.catalogo.editor.persistencia import ejecutar_guardado
from src.catalogo.editor.preparacion import preparar_guardado

__all__ = [
    "ejecutar_guardado",
    "insertar_calzada_con_espesor",
    "insertar_variante_catalogo",
    "preparar_guardado",
]
