"""Inserción atómica calzada (m³) + espesor.

`espesores_calzada` es PK FK que apunta a `calzadas.id`. Si el motor de
la calculadora encuentra una calzada en m³ sin espesor, hace `st.stop()`
(ver ``pages/calculadora.py``). Por eso ambas filas deben crearse
atómicamente: si falla cualquiera de los dos INSERT, no debe quedar la
calzada huérfana en BD.
"""

from __future__ import annotations

import json
import logging

from src.almacenamiento.conexion import conectar
from src.catalogo.repositorio import escribir_audit_evento
from src.almacenamiento.conversion_centimos import _eur_a_cents

logger = logging.getLogger(__name__)


def insertar_calzada_con_espesor(
    item: dict,
    espesor_m: float,
    actor: str = "usuario_inline",
) -> int:
    """Inserta UNA calzada en m³ + su espesor en una transacción atómica.

    Validaciones:
      - label no vacío.
      - unidad debe ser exactamente 'm3' (la función no aplica a 'm2'; en
        ese caso usar `insertar_variante_catalogo("calzadas", ...)` directo).
      - precio > 0.
      - espesor_m > 0.
      - duplicado de label en `calzadas` (UNIQUE de schema).

    Audit log: 1 evento INSERT con categoria='calzadas' y despues_json
    ampliado con `espesor_m` para trazabilidad.

    Returns:
        ``lastrowid`` de la fila INSERTed en `calzadas`.
    """
    label = str(item.get("label", "")).strip()
    if not label:
        raise ValueError("label es obligatorio para calzadas (no puede estar vacío)")
    unidad = item.get("unidad")
    if unidad != "m3":
        raise ValueError(
            f"insertar_calzada_con_espesor solo aplica a unidad='m3'; "
            f"recibido {unidad!r}. Para 'm2' usa insertar_variante_catalogo."
        )
    precio = item.get("precio")
    try:
        precio_num = float(precio) if precio is not None else None
    except (TypeError, ValueError):
        raise ValueError(f"precio debe ser numérico; recibido {precio!r}")
    if precio_num is None or precio_num <= 0:
        raise ValueError(f"precio debe ser > 0; recibido {precio!r}")
    try:
        espesor_num = float(espesor_m)
    except (TypeError, ValueError):
        raise ValueError(f"espesor_m debe ser numérico; recibido {espesor_m!r}")
    if espesor_num <= 0:
        raise ValueError(f"espesor_m debe ser > 0; recibido {espesor_m!r}")

    with conectar() as conn:
        existe = conn.execute(
            "SELECT 1 FROM calzadas WHERE label = ? LIMIT 1", (label,)
        ).fetchone()
        if existe is not None:
            raise ValueError(f"ya existe variante en calzadas con label={label!r}")

        try:
            cursor = conn.execute(
                "INSERT INTO calzadas (label, unidad, precio) VALUES (?, ?, ?)",
                (label, unidad, _eur_a_cents(precio_num)),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("INSERT en calzadas no devolvió lastrowid")
            calzada_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO espesores_calzada (calzada_id, espesor_m) VALUES (?, ?)",
                (calzada_id, espesor_num),
            )
            despues_json = json.dumps(
                {
                    "label": label,
                    "unidad": unidad,
                    "precio": precio_num,
                    "espesor_m": espesor_num,
                },
                ensure_ascii=False,
            )
            escribir_audit_evento(
                conn,
                categoria="calzadas",
                clave=label,
                operacion="INSERT",
                antes_json=None,
                despues_json=despues_json,
                actor=actor,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    logger.info(
        "insertar_calzada_con_espesor -> label=%s, espesor_m=%.3f, actor=%s",
        label, espesor_num, actor,
    )
    return int(calzada_id)
