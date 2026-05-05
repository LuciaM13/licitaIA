"""Use case: editar el catálogo de precios desde la UI admin.

Tres funciones públicas:
  - ``preparar_guardado(editados, originales)`` — valida, calcula diff y
    drifts sin escribir. La UI usa el resultado para mostrar el diálogo de
    confirmación y bloquear el guardado si hay errores.
  - ``ejecutar_guardado(editados)`` — persiste tras confirmación. Propaga
    ``ValueError`` si la validación final falla o la BD rechaza los datos.
  - ``insertar_variante_catalogo(tabla, red, item, actor)`` — Phase 3:
    inserta UNA variante nueva en un catálogo desde la calculadora con
    validaciones de negocio. Llama a infraestructura para el INSERT-único
    sin destruir el catálogo (a diferencia de ``ejecutar_guardado`` que
    hace DELETE+INSERT masivo).

No importa Streamlit. Los widgets de ``pages/admin_precios.py`` y
``pages/calculadora.py`` invocan estos use cases y consumen el shape
``ResultadoPreparacion`` declarado en ``src.aplicacion.contratos``.
"""

from __future__ import annotations

import logging
from typing import Mapping

from src.aplicacion.contratos import (
    CambioPrecio,
    DriftOficial,
    ErrorValidacion,
    ResultadoPreparacion,
)
from src.domain.tipos import Precios
from src.infraestructura.db.connection import conectar
from src.infraestructura.db_precios import _CAMPOS_MONETARIOS, insertar_fila_catalogo
from src.infraestructura.diff_precios import calcular_diff
from src.infraestructura.precios import _validar_precios, guardar_precios
from src.infraestructura.validacion_oficial import detectar_drifts

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes derivadas del schema real (BLOCK 2 / BLOCK 3 fix del plan)
# ---------------------------------------------------------------------------

# Tablas cuyo schema declara `red` como NOT NULL: el use case rechaza
# `red=None` para estas y rechaza `red != None` para las demás (las que
# no tienen columna `red` o la tienen como nullable y aún no la modelamos).
# Fuente: src/infraestructura/db/schema.py.
_TABLAS_CON_RED: frozenset[str] = frozenset({
    "tuberias",   # red TEXT NOT NULL
    "acerados",   # red TEXT NOT NULL
    "acometidas", # red TEXT NOT NULL
})

# Clave de unicidad lógica por catálogo, derivada del schema real. El
# duplicado se chequea con SELECT 1 ... WHERE <clave> antes del INSERT.
# Tupla vacía -> sin chequeo (e.g. pozos: el schema no declara UNIQUE).
_CLAVES_UNICIDAD: Mapping[str, tuple[str, ...]] = {
    "tuberias":   ("red", "label"),
    "acerados":   ("red", "label"),
    "acometidas": ("red", "tipo"),    # acometidas NO usa label
    "valvuleria": ("label",),
    "bordillos":  ("label",),
    "calzadas":   ("label",),
    "imbornales": ("label",),
    "pozos":      (),                  # sin UNIQUE; sin chequeo en use case
}


def preparar_guardado(
    precios_editados: Precios,
    precios_originales: Precios,
) -> ResultadoPreparacion:
    """Valida + diff + drifts sin escribir nada.

    Args:
        precios_editados: dict de precios tras las ediciones del admin.
        precios_originales: snapshot del dict antes de las ediciones.

    Returns:
        ``ResultadoPreparacion`` con errores de validación (bloquean
        guardado), diff de cambios (para el diálogo de confirmación) y
        drifts contra el catálogo oficial (alertas no bloqueantes).
    """
    mensajes_validacion = _validar_precios(precios_editados)
    errores: list[ErrorValidacion] = [
        {"campo": "precios", "mensaje": m, "severidad": "error"}
        for m in mensajes_validacion
    ]

    diff_raw = calcular_diff(precios_originales, precios_editados)
    diff: list[CambioPrecio] = [
        {
            "categoria": str(d.get("seccion", "")),
            "clave": str(d.get("campo", "")),
            "antes": _a_float_o_none(d.get("valor_anterior")),
            "despues": _a_float_o_none(d.get("valor_nuevo")),
        }
        for d in diff_raw
    ]

    drifts_raw = detectar_drifts(precios_editados)
    drifts: list[DriftOficial] = [
        {
            "categoria": str(d.get("categoria", "")),
            "clave": str(d.get("concepto", "")),
            "precio_bd": float(d.get("bd_precio", 0.0)),
            "precio_oficial": float(d.get("precio_oficial", 0.0)),
            "ratio": float(d.get("precio_con_ci", 0.0)) / float(d["precio_oficial"])
                     if d.get("precio_oficial") else 0.0,
        }
        for d in drifts_raw
    ]

    puede_guardar = not errores
    logger.info(
        "preparar_guardado → errores=%d, diff=%d, drifts=%d, puede_guardar=%s",
        len(errores), len(diff), len(drifts), puede_guardar,
    )
    return {
        "errores": errores,
        "diff": diff,
        "drifts": drifts,
        "puede_guardar": puede_guardar,
    }


def ejecutar_guardado(precios_editados: Precios) -> None:
    """Persiste los precios editados. Propaga ``ValueError`` si falla.

    La UI debe invalidar su caché (``cargar_precios.clear()``) tras un
    guardado exitoso.
    """
    logger.info("ejecutar_guardado → persistiendo precios editados")
    guardar_precios(precios_editados)


# ---------------------------------------------------------------------------
# Phase 3 — creación inline de partidas
# ---------------------------------------------------------------------------

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

    # Chequeo de duplicado (BLOCK 2): SELECT 1 ... LIMIT 1 con la clave
    # propia del catálogo. Tupla vacía -> sin chequeo (e.g. pozos).
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

    logger.info(
        "insertar_variante_catalogo -> tabla=%s, red=%s, claves=%s, actor=%s",
        tabla, red, claves, actor,
    )

    # Delegación a infraestructura: el INSERT parametrizado y el audit_log
    # los gestiona insertar_fila_catalogo. Devolvemos su lastrowid.
    return insertar_fila_catalogo(tabla, item_local, actor=actor)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _a_float_o_none(v) -> float | None:
    """Intenta convertir a float; devuelve None si no es numérico."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
