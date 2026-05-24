"""``ejecutar_guardado``: persiste los precios editados tras la confirmación.

Es la fase final del workflow admin: ``preparar_guardado`` → diálogo de
confirmación en UI → ``ejecutar_guardado`` (si confirma).
"""

from __future__ import annotations

import logging

from src.catalogo.guardado import guardar_precios
from src.modelo.tipos import Precios

logger = logging.getLogger(__name__)


def ejecutar_guardado(precios_editados: Precios) -> None:
    """Persiste los precios editados. Propaga ``ValueError`` si falla.

    La UI debe invalidar su caché (``cargar_precios.clear()``) tras un
    guardado exitoso.
    """
    logger.info("ejecutar_guardado → persistiendo precios editados")
    guardar_precios(precios_editados)
