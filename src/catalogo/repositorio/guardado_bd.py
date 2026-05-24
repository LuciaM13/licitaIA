"""``guardar_todo``: DELETE+INSERT atómico del catálogo completo (admin).

Orquestador de la transacción: snapshot pre-cambio → DELETE de todas las
tablas → INSERTs (delegados a ``_inserts``) → diff lógico → escritura de
eventos en ``audit_log`` → commit. La SQL en sí vive en ``_inserts.py``;
aquí queda solo la orquestación.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from src.almacenamiento import conectar
from src.catalogo.repositorio._inserts import _borrar_todo, _insertar_todos
from src.catalogo.repositorio.audit import (
    _categorias_a_auditar,
    _diff_categoria,
    _escribir_audit_log,
)
from src.catalogo.repositorio.carga_bd import cargar_todo

logger = logging.getLogger(__name__)


def guardar_todo(precios: dict, path: str | Path | None = None, actor: str | None = None) -> None:
    """Escribe el dict completo a la BD dentro de una transacción atómica.

    Con autocommit=False (PEP 249), commit() y rollback() funcionan
    correctamente. El orden de DELETE (dependientes primero) e INSERT
    (padres primero) respeta la única FK: espesores_calzada → calzadas.

    Audit log: antes del DELETE hace snapshot de `cargar_todo()`; tras los
    INSERTs calcula el diff lógico y escribe una fila en `audit_log` por
    cada cambio. `actor` por defecto es el valor de la env var
    LICITAIA_AUDIT_ACTOR o "admin_ui" como fallback.

    Limitación conocida (seguro para uso monoutuario actual): el snapshot
    `antes` se toma FUERA de la transacción de escritura. Esto significa que
    dos escrituras concurrentes desde distintas pestañas del admin podrían
    capturar snapshots solapados. Para el uso solo-dev actual no hay riesgo;
    si algún día la app se multiusuario habrá que mover el snapshot dentro
    de la misma conexión con `BEGIN EXCLUSIVE`.
    """
    logger.info("guardar_todo() - escritura atómica a BD")
    if actor is None:
        actor = os.environ.get("LICITAIA_AUDIT_ACTOR", "admin_ui")

    # Snapshot pre-cambio para diff de audit. Si la BD está vacía (primer
    # arranque) cargar_todo puede fallar; tratamos cada INSERT como alta.
    try:
        snapshot_antes = cargar_todo(path)
    except Exception:
        snapshot_antes = {cat: [] for cat in _categorias_a_auditar()}

    with conectar(path) as conn:
        try:
            _borrar_todo(conn)
            _insertar_todos(conn, precios)

            # Diff snapshot antes ↔ nuevo estado (precios del caller) → audit_log
            eventos_audit = []
            for categoria in _categorias_a_auditar():
                antes = snapshot_antes.get(categoria, [] if isinstance(precios.get(categoria), list) else {})
                despues = precios.get(categoria, antes)
                eventos_audit.extend(_diff_categoria(categoria, antes, despues))
            _escribir_audit_log(conn, eventos_audit, actor)

            conn.commit()
            if eventos_audit:
                logger.info("audit_log: %d evento(s) registrado(s) por actor=%s",
                            len(eventos_audit), actor)

        except Exception as e:
            logger.error("Error en guardar_todo: %s", e, exc_info=True)
            conn.rollback()
            raise
