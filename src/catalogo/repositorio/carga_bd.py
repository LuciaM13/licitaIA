"""``cargar_todo``: lee toda la BD y construye el dict de precios.

La BD guarda monetarios como INTEGER céntimos (Migración 13); aquí se
dividen por 100 con ``_convertir_filas`` y ``_cents_a_eur``. El resto del
código opera siempre en floats EUR.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.almacenamiento import conectar, _rows_to_dicts, _cargar_por_red
from src.almacenamiento.conversion_centimos import (
    _CAMPOS_MONETARIOS,
    _cents_a_eur,
    _convertir_filas,
)

logger = logging.getLogger(__name__)


def cargar_todo(path: str | Path | None = None) -> dict:
    """Lee toda la BD y construye el dict compatible con la interfaz existente."""
    logger.debug("cargar_todo() - leyendo todas las tablas")
    with conectar(path) as conn:
        precios = {}

        # Config escalares
        for row in conn.execute("SELECT clave, valor FROM config"):
            precios[row["clave"]] = row["valor"]

        # Tuberías (ABA/SAN) - incluye factor_piezas y precio_material_m
        # Tiebreaker `id` ASC garantiza orden estable cuando hay múltiples
        # variantes con el mismo `diametro_mm` (p.ej. PE-100 DN90 PN10/PN16
        # tras m19): la fila canónica certificada (id menor, insertada antes)
        # sale primero, preservando el contrato de los buscadores que retornan
        # el primer match (p.ej. _buscar_tuberia en test_bd_invariante_ci).
        precios.update(_cargar_por_red(
            conn, "tuberias",
            "label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m",
            "catalogo", order_by="diametro_mm, id"))
        _convertir_filas(precios["catalogo_aba"], _CAMPOS_MONETARIOS["tuberias"])
        _convertir_filas(precios["catalogo_san"], _CAMPOS_MONETARIOS["tuberias"])
        # Valvulería (incluye factor_piezas, precio_material y instalacion nullable)
        precios["catalogo_valvuleria"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material FROM valvuleria ORDER BY dn_min")),
            _CAMPOS_MONETARIOS["valvuleria"])

        # Entibación (incluye columna red, nullable)
        precios["catalogo_entibacion"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, precio_m2, umbral_m, red FROM entibacion")),
            _CAMPOS_MONETARIOS["entibacion"])

        # Pozos (con columnas opcionales para precios graduados, tapa y pates SAN)
        precios["catalogo_pozos"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material, precio_pate_material FROM pozos")),
            _CAMPOS_MONETARIOS["pozos"])

        # Demolición (ABA/SAN) con variantes de material
        precios.update(_cargar_por_red(conn, "demolicion", "label, unidad, material, precio",
                                       "demolicion"))
        _convertir_filas(precios["demolicion_aba"], _CAMPOS_MONETARIOS["demolicion"])
        _convertir_filas(precios["demolicion_san"], _CAMPOS_MONETARIOS["demolicion"])

        # Acerados
        precios.update(_cargar_por_red(conn, "acerados", "label, unidad, precio",
                                       "acerados"))
        _convertir_filas(precios["acerados_aba"], _CAMPOS_MONETARIOS["acerados"])
        _convertir_filas(precios["acerados_san"], _CAMPOS_MONETARIOS["acerados"])

        # Bordillos
        precios["bordillos_reposicion"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, unidad, precio FROM bordillos ORDER BY label")),
            _CAMPOS_MONETARIOS["bordillos"])

        # Calzadas
        precios["calzadas_reposicion"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, unidad, precio FROM calzadas ORDER BY label")),
            _CAMPOS_MONETARIOS["calzadas"])

        # Espesores calzada (dict, no lista) - JOIN para obtener label
        precios["espesores_calzada"] = {
            row["label"]: row["espesor_m"]
            for row in conn.execute(
                "SELECT c.label, e.espesor_m "
                "FROM espesores_calzada e "
                "JOIN calzadas c ON e.calzada_id = c.id")
        }

        # Sub-bases pavimentacion
        precios["catalogo_subbases"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, precio_m3 FROM subbases ORDER BY label")),
            _CAMPOS_MONETARIOS["subbases"])

        # Excavación (dict)
        precios["excavacion"] = {
            row["clave"]: row["valor"]
            for row in conn.execute("SELECT clave, valor FROM excavacion")
        }

        # Acometidas (tipos→precio y tipos→factor_piezas separados)
        precios["acometidas_aba_tipos"] = {
            row["tipo"]: _cents_a_eur(row["precio"])
            for row in conn.execute("SELECT tipo, precio FROM acometidas WHERE red='ABA' ORDER BY tipo")
        }
        precios["acometidas_san_tipos"] = {
            row["tipo"]: _cents_a_eur(row["precio"])
            for row in conn.execute("SELECT tipo, precio FROM acometidas WHERE red='SAN' ORDER BY tipo")
        }
        precios["acometidas_aba_factores"] = {
            row["tipo"]: row["factor_piezas"]
            for row in conn.execute("SELECT tipo, factor_piezas FROM acometidas WHERE red='ABA' ORDER BY tipo")
        }
        precios["acometidas_san_factores"] = {
            row["tipo"]: row["factor_piezas"]
            for row in conn.execute("SELECT tipo, factor_piezas FROM acometidas WHERE red='SAN' ORDER BY tipo")
        }

        # Acometida por defecto
        precios["acometida_aba_defecto"] = next(
            (row["tipo"] for row in conn.execute(
                "SELECT tipo FROM acometida_defecto WHERE red='ABA'")),
            None,
        )
        precios["acometida_san_defecto"] = next(
            (row["tipo"] for row in conn.execute(
                "SELECT tipo FROM acometida_defecto WHERE red='SAN'")),
            None,
        )

        # Defaults UI
        precios["defaults_ui"] = {
            row["clave"]: row["valor"]
            for row in conn.execute("SELECT clave, valor FROM defaults_ui")
        }

        # Desmontaje tubería ABA
        precios["catalogo_desmontaje"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, dn_max, precio_m, es_fibrocemento FROM desmontaje ORDER BY dn_max")),
            _CAMPOS_MONETARIOS["desmontaje"])

        # Imbornales SAN
        precios["catalogo_imbornales"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT label, precio, tipo FROM imbornales ORDER BY tipo, label")),
            _CAMPOS_MONETARIOS["imbornales"])

        # Pozos existentes precios
        precios["catalogo_pozos_existentes"] = _convertir_filas(_rows_to_dicts(
            conn.execute("SELECT red, accion, precio, intervalo_m FROM pozos_existentes_precios ORDER BY red, accion")),
            _CAMPOS_MONETARIOS["pozos_existentes_precios"])

        return precios
