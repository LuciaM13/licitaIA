"""Phase 3 — creación inline de UNA variante de catálogo desde la calculadora.

Función pública: ``insertar_variante_catalogo``. Validaciones bloqueantes
de negocio antes de delegar el INSERT a infraestructura.
"""

from __future__ import annotations

import logging

import re

from src.catalogo.editor.schema_constants import (
    _ACCIONES_POZOS_EXISTENTES,
    _CLAVES_UNICIDAD,
    _TABLAS_CON_RED,
)
from src.almacenamiento.conexion import conectar
from src.catalogo.repositorio import insertar_fila_catalogo
from src.almacenamiento.conversion_centimos import _CAMPOS_MONETARIOS

logger = logging.getLogger(__name__)


def insertar_variante_catalogo(
    tabla: str,
    red: str | None,
    item: dict,
    actor: str = "usuario_inline",
) -> int:
    """Inserta UNA variante nueva en el catálogo ``tabla``. Devuelve el id.

    Validaciones bloqueantes (cada una propaga ``ValueError`` con mensaje
    legible en español; el caller las muestra en el diálogo de la UI):

      1. ``tabla`` debe estar en ``_CLAVES_UNICIDAD`` (derivado del schema).
      2. Regla de ``red`` por tabla (BLOCK 3 del plan):
         - Si ``tabla in _TABLAS_CON_RED`` y ``red`` es falsy: error.
         - Si ``tabla not in _TABLAS_CON_RED`` y ``red is not None``: error
           (la columna no existe; pasarla rompería el INSERT con
           ``OperationalError: no column named red``).
      3. Campos clave no vacíos:
         - Si ``"label" in _CLAVES_UNICIDAD[tabla]``: ``item["label"]`` no vacío.
         - Si ``tabla == "acometidas"``: ``item["tipo"]`` no vacío.
      4. Precio > 0. El nombre del campo de precio depende del catálogo
         (primera entrada de ``_CAMPOS_MONETARIOS[tabla]``).
      5. Duplicado por clave de unicidad propia del catálogo (BLOCK 2):
         si ``_CLAVES_UNICIDAD[tabla]`` no es vacía, se hace
         ``SELECT 1 ... WHERE <clave>``; si existe, error.

    Convención del CI (memoria de proyecto): el item se persiste como
    precio BASE EMASESA en céntimos (``int(round(precio*100))``) vía
    ``insertar_fila_catalogo`` -> ``_eur_a_cents``. NO se pre-multiplica
    por 1.05; el cargador aplica el CI en runtime con ``aplicar_ci``.

    Args:
        tabla: nombre de la tabla destino (catálogo de partidas).
        red: ``"ABA"``, ``"SAN"`` o ``None`` (según tabla; ver _TABLAS_CON_RED).
        item: dict con las columnas a insertar (sin ``red``: el use case
            la inyecta automáticamente cuando la tabla la exige). El precio
            se pasa en EUR; se persiste como céntimos.
        actor: identificador para ``audit_log`` (default ``"usuario_inline"``).

    Returns:
        ``lastrowid`` del INSERT. La UI puede ignorarlo (el rerun
        post-INSERT identifica el nuevo item por ``(tabla, red, label)`` en
        ``INLINE_CREATE_RESULT``); se devuelve para logs/audit y assertions
        de tests.

    Notes:
        Tras invocar, la UI debe llamar a ``cargar_precios.clear()`` para
        invalidar la caché ``@st.cache_data`` y que el siguiente rerun lea
        el nuevo item desde BD.
    """
    if tabla not in _CLAVES_UNICIDAD:
        raise ValueError(
            f"tabla '{tabla}' no soportada para creación inline; "
            f"catálogos válidos: {sorted(_CLAVES_UNICIDAD)}"
        )

    # Validación de red (BLOCK 3): la regla depende del schema real.
    if tabla in _TABLAS_CON_RED:
        if not red:
            raise ValueError(f"red es obligatorio para tabla {tabla}")
    else:
        if red is not None:
            raise ValueError(
                f"tabla {tabla} no admite red (debe pasarse red=None); "
                "la columna no existe en este catálogo."
            )

    # Trabajo sobre copia para no mutar el dict del caller.
    item_local: dict = dict(item)

    # Inyección automática de red para tablas que la exigen. El form de
    # la UI NO incluye `red` (el dispatcher la pasa por argumento).
    if tabla in _TABLAS_CON_RED:
        item_local["red"] = red

    # Validación de campo clave (label / tipo).
    claves = _CLAVES_UNICIDAD[tabla]
    if "label" in claves:
        if not str(item_local.get("label", "")).strip():
            raise ValueError(
                f"label es obligatorio para tabla {tabla} (no puede estar vacío)"
            )
    if tabla == "acometidas":
        if not str(item_local.get("tipo", "")).strip():
            raise ValueError(
                "tipo es obligatorio para acometidas (no puede estar vacío)"
            )
    if tabla == "demolicion":
        if not str(item_local.get("label", "")).strip():
            raise ValueError(
                "label es obligatorio para demolicion (no puede estar vacío)"
            )
        # El usuario puede introducir slugs de material fuera del set EMASESA
        # canónico (decisión Phase 03-04). La validación se relaja a slug
        # snake_case [a-z0-9_]+ no vacío y distinto de 'generico' (sentinel
        # legacy reservado para filas heredadas, ver schema.py:117-118).
        material_raw = str(item_local.get("material", "")).strip()
        material = re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]", "", material_raw.lower().replace(" ", "_").replace("-", "_"))).strip("_")
        if not material:
            raise ValueError(
                "material es obligatorio para demolicion y debe contener "
                "letras o números (slug snake_case)"
            )
        if material == "generico":
            raise ValueError(
                "material 'generico' está reservado para filas legacy y no "
                "puede crearse desde la UI"
            )
        item_local["material"] = material
        unidad = str(item_local.get("unidad", "")).strip()
        if unidad not in {"m", "m2", "m3", "ud"}:
            raise ValueError(
                f"unidad '{unidad}' no soportada en demolicion; "
                "válidas: m, m2, m3, ud"
            )
    if tabla == "pozos_existentes_precios":
        accion = str(item_local.get("accion", "")).strip()
        if accion not in _ACCIONES_POZOS_EXISTENTES:
            raise ValueError(
                f"accion '{accion}' no soportada en pozos_existentes_precios; "
                f"válidas: {sorted(_ACCIONES_POZOS_EXISTENTES)}"
            )

    # Validación de precio > 0. El campo monetario primario es el primero
    # de _CAMPOS_MONETARIOS[tabla] (e.g. precio_m para tuberias, precio
    # para el resto).
    campos_monetarios = _CAMPOS_MONETARIOS.get(tabla, ())
    if not campos_monetarios:
        raise ValueError(
            f"tabla {tabla} no declara campos monetarios; "
            "no se puede validar precio."
        )
    campo_precio = campos_monetarios[0]
    valor_precio = item_local.get(campo_precio)
    try:
        valor_precio_num = float(valor_precio) if valor_precio is not None else None
    except (TypeError, ValueError):
        raise ValueError(
            f"precio ({campo_precio}) debe ser numérico; "
            f"recibido {valor_precio!r}"
        )
    if valor_precio_num is None or valor_precio_num <= 0:
        raise ValueError(
            f"precio ({campo_precio}) debe ser > 0; recibido {valor_precio!r}"
        )

    logger.info(
        "insertar_variante_catalogo -> tabla=%s, red=%s, claves=%s, actor=%s",
        tabla, red, claves, actor,
    )

    # Chequeo de duplicado (BLOCK 2) + INSERT bajo UNA misma conexión para
    # cerrar la ventana TOCTOU: si dos sesiones pasaran el SELECT en paralelo
    # con conexiones distintas, la segunda chocaría contra el UNIQUE en el
    # INSERT y propagaría IntegrityError en vez del ValueError esperado.
    # Delegamos el INSERT a `insertar_fila_catalogo(..., conn=conn)` para no
    # duplicar la whitelist de columnas ni la conversión a céntimos.
    if claves:
        where_sql = " AND ".join(f"{c} = ?" for c in claves)
        where_vals = tuple(item_local.get(c) for c in claves)
        with conectar() as conn:
            row = conn.execute(
                f"SELECT 1 FROM {tabla} WHERE {where_sql} LIMIT 1",
                where_vals,
            ).fetchone()
            if row is not None:
                detalles = ", ".join(f"{c}={item_local.get(c)!r}" for c in claves)
                raise ValueError(
                    f"ya existe variante en {tabla} con {detalles}"
                )
            nuevo_id = insertar_fila_catalogo(
                tabla, item_local, actor=actor, conn=conn,
            )
            conn.commit()
        return nuevo_id

    # Sin clave de unicidad declarada (e.g. pozos): no hay SELECT previo,
    # delegamos al flujo standalone de `insertar_fila_catalogo` que abre y
    # commitea su propia conexión.
    return insertar_fila_catalogo(tabla, item_local, actor=actor)
