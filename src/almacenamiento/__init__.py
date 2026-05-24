"""Paquete de almacenamiento SQLite para precios EMASESA.

Plomería genérica de SQLite (no sabe qué es un precio):
  - ``conexion`` — context manager ``conectar()`` + ``DB_PATH`` + whitelist.
  - ``schema`` — DDL de las tablas (``_SCHEMA``), única fuente de verdad
    del schema; se aplica idempotentemente en cada arranque vía
    ``CREATE TABLE IF NOT EXISTS``.
  - ``inicializacion`` — ``init_db()``, que ejecuta ``_SCHEMA`` sobre la BD.
  - ``helpers`` — utilidades de lectura (_rows_to_dicts, _cargar_por_red).

Mapeo dominio↔BD del dict de precios EMASESA:
  - el subpaquete ``src.catalogo.repositorio`` expone ``cargar_todo``,
    ``guardar_todo``, ``insertar_fila_catalogo`` y ``escribir_audit_evento``,
    todos clientes de los módulos de plomería de este paquete.

Este ``__init__`` re-exporta los nombres más usados (``conectar``,
``DB_PATH``, ``init_db``, helpers) para que los call-sites no tengan que
importar de los submódulos directamente.
"""

from __future__ import annotations

from src.almacenamiento.conexion import (
    DB_PATH,
    _TABLAS_PERMITIDAS,
    conectar,
)
from src.almacenamiento.helpers import _cargar_por_red, _rows_to_dicts
from src.almacenamiento.inicializacion import init_db

__all__ = [
    "DB_PATH",
    "_TABLAS_PERMITIDAS",
    "_cargar_por_red",
    "_rows_to_dicts",
    "conectar",
    "init_db",
]
