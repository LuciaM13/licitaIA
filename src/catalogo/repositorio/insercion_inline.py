"""``insertar_fila_catalogo``: INSERT quirúrgico de UNA variante (Phase 3).

A diferencia de ``guardar_todo`` (DELETE+INSERT masivo del catálogo entero),
esta operación es quirúrgica: preserva los IDs existentes y por tanto no
altera la invariante CI 141/141 del catálogo certificado contra Excel
EMASESA.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.almacenamiento import conectar
from src.catalogo.repositorio.audit import escribir_audit_evento
from src.almacenamiento.conversion_centimos import _CAMPOS_MONETARIOS, _eur_a_cents

logger = logging.getLogger(__name__)


# Subconjunto de tablas autorizadas para edición inline (Phase 3 / Plan 03-01,
# ampliado en Plan 03-03 con los 5 catálogos restantes que aún se seleccionaban
# en la calculadora sin botón "+").
# Más restrictivo que `_TABLAS_PERMITIDAS`: solo catálogos de partidas que la
# UI de la calculadora permite ampliar al vuelo. Excluye tablas estructurales
# (config, defaults_ui, audit_log, presupuestos*, etc.) y `entibacion`, que no
# se selecciona desde la calculadora (la elige el motor por umbral de profundidad).
_TABLAS_INLINE_EDITABLES = frozenset({
    "tuberias", "valvuleria", "acometidas", "acerados",
    "bordillos", "calzadas", "pozos", "imbornales",
    "demolicion", "subbases", "desmontaje", "pozos_existentes_precios",
})


# Columnas permitidas por tabla para el INSERT inline. Defensa en profundidad:
# `tabla` ya esta protegida por `_TABLAS_INLINE_EDITABLES`, pero los nombres de
# columnas en el f-string del INSERT vienen de `item.keys()` (input externo).
# Esta whitelist evita que un nombre de columna malicioso se interpole en SQL.
# Se omite `id` (AUTOINCREMENT, lo asigna SQLite). Las columnas reales se
# extraen del DDL en ``src/almacenamiento/schema.py``.
_COLUMNAS_PERMITIDAS: dict[str, frozenset[str]] = {
    "tuberias": frozenset({
        "red", "label", "tipo", "diametro_mm",
        "precio_m", "factor_piezas", "precio_material_m",
    }),
    "valvuleria": frozenset({
        "label", "tipo", "dn_min", "dn_max", "precio",
        "intervalo_m", "instalacion", "factor_piezas", "precio_material",
    }),
    "acometidas": frozenset({"red", "tipo", "precio", "factor_piezas"}),
    "acerados": frozenset({"red", "label", "unidad", "precio"}),
    "bordillos": frozenset({"label", "unidad", "precio"}),
    "calzadas": frozenset({"label", "unidad", "precio"}),
    "pozos": frozenset({
        "label", "precio", "intervalo", "red",
        "profundidad_max", "dn_max",
        "precio_tapa", "precio_tapa_material", "precio_pate_material",
    }),
    "imbornales": frozenset({"label", "precio", "tipo"}),
    "demolicion": frozenset({
        "red", "label", "unidad", "material", "precio",
    }),
    "subbases": frozenset({"label", "precio_m3"}),
    "desmontaje": frozenset({
        "label", "dn_max", "precio_m", "es_fibrocemento",
    }),
    "pozos_existentes_precios": frozenset({
        "red", "accion", "precio", "intervalo_m",
    }),
}


def insertar_fila_catalogo(
    tabla: str,
    item: dict,
    actor: str = "usuario_inline",
    path: str | Path | None = None,
    conn=None,
) -> int:
    """Inserta UNA fila en ``tabla`` y registra UN evento en ``audit_log``.

    Diferencias frente a ``guardar_todo``:
      - Es una operación quirúrgica: NO hace DELETE+INSERT masivo del
        catálogo entero. Preserva los IDs existentes y por tanto NO altera
        la invariante CI 141/141 del catálogo certificado.
      - Trabaja sobre el subconjunto ``_TABLAS_INLINE_EDITABLES`` (whitelist
        restrictiva). Cualquier tabla fuera de ese set produce ``ValueError``.

    Conversión de monetarios:
      Los campos listados en ``_CAMPOS_MONETARIOS[tabla]`` se convierten de
      EUR (float) a céntimos (int) con ``_eur_a_cents`` (round bancario).
      Esta función persiste el precio BASE EMASESA: NO multiplica por
      ``pct_ci`` (1.05). El cargador aplica el CI en runtime.

    Args:
        tabla: nombre de la tabla destino (debe estar en
            ``_TABLAS_INLINE_EDITABLES``).
        item: dict con las columnas a insertar. La función NO valida la
            forma del item más allá del whitelist de tabla y la conversión
            de monetarios; las validaciones de negocio (red obligatoria,
            duplicado por clave, precio>0) viven en el use case
            ``src.catalogo.editor.insertar_variante_catalogo``.
        actor: identificador para ``audit_log`` (default ``"usuario_inline"``).
        path: ruta a una BD alternativa (sólo tests). ``None`` usa la
            ``DB_PATH`` real. Ignorado si ``conn`` viene dado.
        conn: conexión SQLite ya abierta (opcional). Si se pasa, el INSERT
            y el evento de audit se ejecutan sobre ella y NO se hace commit
            ni cierre (responsabilidad del caller). Permite al use case
            ``insertar_variante_catalogo`` cerrar la ventana TOCTOU entre
            el SELECT de duplicado y el INSERT bajo una única conexión. Si
            ``conn`` es ``None``, se abre una conexión nueva con ``conectar(path)``
            y se hace commit al final como en el flujo standalone.

    Returns:
        ``cursor.lastrowid`` del INSERT (int > 0).

    Raises:
        ValueError: si ``tabla`` no está en ``_TABLAS_INLINE_EDITABLES``,
            o si ``item`` contiene claves fuera de
            ``_COLUMNAS_PERMITIDAS[tabla]`` (defensa SQL injection).
    """
    if tabla not in _TABLAS_INLINE_EDITABLES:
        raise ValueError(
            f"tabla '{tabla}' no editable inline; "
            f"permitidas: {sorted(_TABLAS_INLINE_EDITABLES)}"
        )

    # Whitelist de columnas: defensa en profundidad frente a SQL injection
    # a traves de las claves del item (que se interpolan en el f-string del
    # INSERT). Sin esta validacion, un nombre de columna como
    # "precio); DROP TABLE x;--" se inyectaria literal en la query.
    cols_no_permitidas = set(item.keys()) - _COLUMNAS_PERMITIDAS[tabla]
    if cols_no_permitidas:
        raise ValueError(
            f"columnas no permitidas para tabla '{tabla}': "
            f"{sorted(cols_no_permitidas)}"
        )

    logger.info(
        "insertar_fila_catalogo -> tabla=%s, label=%s, actor=%s",
        tabla, item.get("label", item.get("tipo", "?")), actor,
    )

    # Convertir monetarios a céntimos (sólo los campos listados como
    # monetarios para esta tabla; los no-monetarios pasan tal cual).
    campos_monetarios = _CAMPOS_MONETARIOS.get(tabla, ())
    item_persistible: dict = {}
    for col, val in item.items():
        if col in campos_monetarios:
            item_persistible[col] = _eur_a_cents(val)
        else:
            item_persistible[col] = val

    # INSERT parametrizado dinámico: las columnas vienen de las claves del
    # item (whitelisted vía _TABLAS_INLINE_EDITABLES y validadas aguas
    # arriba por el use case). Los valores van por placeholders ?.
    cols = list(item_persistible.keys())
    placeholders = ", ".join(["?"] * len(cols))
    columnas_sql = ", ".join(cols)
    valores = tuple(item_persistible[c] for c in cols)

    despues_json = json.dumps(item, ensure_ascii=False)
    clave_audit = str(item.get("label") or item.get("tipo") or "")

    def _ejecutar(c) -> int | None:
        cursor = c.execute(
            f"INSERT INTO {tabla} ({columnas_sql}) VALUES ({placeholders})",
            valores,
        )
        escribir_audit_evento(
            c,
            categoria=tabla,
            clave=clave_audit,
            operacion="INSERT",
            antes_json=None,
            despues_json=despues_json,
            actor=actor,
        )
        return cursor.lastrowid

    if conn is not None:
        # Conexión gestionada por el caller (e.g. use case que ya abrió
        # un context manager para cerrar la ventana TOCTOU SELECT->INSERT).
        # NO se hace commit ni cierre aquí.
        nuevo_id = _ejecutar(conn)
    else:
        with conectar(path) as conn_local:
            nuevo_id = _ejecutar(conn_local)
            conn_local.commit()

    return int(nuevo_id) if nuevo_id is not None else 0
