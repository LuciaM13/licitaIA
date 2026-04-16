"""CRUD de catálogos de precios - cargar_todo() y guardar_todo().

Separado de db.py para mantener el fichero principal por debajo de 500 líneas.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from src.infraestructura.db import conectar, _TABLAS_PERMITIDAS, _rows_to_dicts, _cargar_por_red

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
        precios.update(_cargar_por_red(
            conn, "tuberias",
            "label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m",
            "catalogo", order_by="diametro_mm"))
        # Valvulería (incluye factor_piezas, precio_material y instalacion nullable)
        precios["catalogo_valvuleria"] = _rows_to_dicts(
            conn.execute("SELECT label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material FROM valvuleria ORDER BY dn_min"))

        # Entibación (incluye columna red, nullable)
        precios["catalogo_entibacion"] = _rows_to_dicts(
            conn.execute("SELECT label, precio_m2, umbral_m, red FROM entibacion"))

        # Pozos (con columnas opcionales para precios graduados, tapa y pates SAN)
        precios["catalogo_pozos"] = _rows_to_dicts(
            conn.execute("SELECT label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material, precio_pate_material FROM pozos"))

        # Demolición (ABA/SAN)
        precios.update(_cargar_por_red(conn, "demolicion", "label, unidad, precio",
                                       "demolicion"))

        # Acerados
        precios.update(_cargar_por_red(conn, "acerados", "label, unidad, precio",
                                       "acerados"))

        # Bordillos
        precios["bordillos_reposicion"] = _rows_to_dicts(
            conn.execute("SELECT label, unidad, precio FROM bordillos ORDER BY label"))

        # Calzadas
        precios["calzadas_reposicion"] = _rows_to_dicts(
            conn.execute("SELECT label, unidad, precio FROM calzadas ORDER BY label"))

        # Espesores calzada (dict, no lista) - JOIN para obtener label
        precios["espesores_calzada"] = {
            row["label"]: row["espesor_m"]
            for row in conn.execute(
                "SELECT c.label, e.espesor_m "
                "FROM espesores_calzada e "
                "JOIN calzadas c ON e.calzada_id = c.id")
        }

        # Sub-bases pavimentacion
        precios["catalogo_subbases"] = _rows_to_dicts(
            conn.execute("SELECT label, precio_m3 FROM subbases ORDER BY label"))

        # Excavación (dict)
        precios["excavacion"] = {
            row["clave"]: row["valor"]
            for row in conn.execute("SELECT clave, valor FROM excavacion")
        }

        # Acometidas (tipos→precio y tipos→factor_piezas separados)
        precios["acometidas_aba_tipos"] = {
            row["tipo"]: row["precio"]
            for row in conn.execute("SELECT tipo, precio FROM acometidas WHERE red='ABA' ORDER BY tipo")
        }
        precios["acometidas_san_tipos"] = {
            row["tipo"]: row["precio"]
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
        for row in conn.execute("SELECT red, tipo FROM acometida_defecto"):
            if row["red"] == "ABA":
                precios["acometida_aba_defecto"] = row["tipo"]
            else:
                precios["acometida_san_defecto"] = row["tipo"]

        # Defaults UI
        precios["defaults_ui"] = {
            row["clave"]: row["valor"]
            for row in conn.execute("SELECT clave, valor FROM defaults_ui")
        }

        # Desmontaje tubería ABA
        precios["catalogo_desmontaje"] = _rows_to_dicts(
            conn.execute("SELECT label, dn_max, precio_m, es_fibrocemento FROM desmontaje ORDER BY dn_max"))

        # Imbornales SAN
        precios["catalogo_imbornales"] = _rows_to_dicts(
            conn.execute("SELECT label, precio, tipo FROM imbornales ORDER BY tipo, label"))

        # Pozos existentes precios
        precios["catalogo_pozos_existentes"] = _rows_to_dicts(
            conn.execute("SELECT red, accion, precio, intervalo_m FROM pozos_existentes_precios ORDER BY red, accion"))

        return precios


def guardar_todo(precios: dict, path: str | Path | None = None) -> None:
    """Escribe el dict completo a la BD dentro de una transacción atómica.

    Con autocommit=False (PEP 249), commit() y rollback() funcionan
    correctamente. El orden de DELETE (dependientes primero) e INSERT
    (padres primero) respeta la única FK: espesores_calzada → calzadas.
    """
    logger.info("guardar_todo() - escritura atómica a BD")
    with conectar(path) as conn:
        try:
            # Limpiar todas las tablas (orden respeta FK: dependientes primero)
            for tabla in [
                "espesores_calzada", "acometida_defecto", "acometidas",
                "defaults_ui", "excavacion", "demolicion", "bordillos", "calzadas",
                "acerados", "pozos", "entibacion", "valvuleria",
                "tuberias", "config",
                "subbases", "desmontaje", "imbornales", "pozos_existentes_precios",
            ]:
                if tabla not in _TABLAS_PERMITIDAS:
                    raise ValueError(f"Tabla no permitida: {tabla!r}")
                conn.execute(f"DELETE FROM {tabla}")

            # Config escalares
            for clave in ("pct_gg", "pct_bi", "pct_iva", "factor_esponjamiento",
                          "pct_manual_defecto", "conduccion_provisional_precio_m",
                          "pct_ci"):
                val = precios.get(clave)
                if val is None:
                    raise ValueError(
                        f"Falta el valor de configuración '{clave}'. "
                        "Revisa la sección Financiero y generales en Administración de precios."
                    )
                conn.execute("INSERT INTO config (clave, valor) VALUES (?, ?)",
                             (clave, float(val)))

            # Tuberías (con factor_piezas y precio_material_m)
            for red, clave in [("ABA", "catalogo_aba"), ("SAN", "catalogo_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO tuberias (red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m) VALUES (?,?,?,?,?,?,?)",
                        (red, item["label"], item["tipo"], int(item["diametro_mm"]), float(item["precio_m"]),
                         float(item.get("factor_piezas", 1.0)),
                         float(item.get("precio_material_m", 0.0))))

            # Valvulería (con factor_piezas, precio_material e instalacion nullable)
            for item in precios["catalogo_valvuleria"]:
                inst = item.get("instalacion")
                conn.execute(
                    "INSERT INTO valvuleria (label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material) VALUES (?,?,?,?,?,?,?,?,?)",
                    (item["label"], item["tipo"], int(item["dn_min"]), int(item["dn_max"]),
                     float(item["precio"]), float(item["intervalo_m"]), inst,
                     float(item.get("factor_piezas", 1.2)),
                     float(item.get("precio_material", 0.0))))

            # Entibación (con columna red nullable)
            for item in precios["catalogo_entibacion"]:
                red = item.get("red")
                conn.execute(
                    "INSERT INTO entibacion (label, precio_m2, umbral_m, red) VALUES (?,?,?,?)",
                    (item["label"], float(item["precio_m2"]), float(item["umbral_m"]), red))

            # Pozos (con columnas opcionales + precio_tapa + precio_pate_material SAN)
            for item in precios["catalogo_pozos"]:
                prof_max = item.get("profundidad_max")
                dn_max = item.get("dn_max")
                conn.execute(
                    "INSERT INTO pozos (label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material, precio_pate_material) VALUES (?,?,?,?,?,?,?,?,?)",
                    (item["label"], float(item["precio"]),
                     float(item["intervalo"]),
                     item.get("red"),
                     float(prof_max) if prof_max is not None else None,
                     int(dn_max) if dn_max is not None else None,
                     float(item.get("precio_tapa", 0.0) or 0.0),
                     float(item.get("precio_tapa_material", 0.0) or 0.0),
                     float(item.get("precio_pate_material", 0.0) or 0.0)))

            # Demolición
            for red, clave in [("ABA", "demolicion_aba"), ("SAN", "demolicion_san")]:
                for item in precios.get(clave, []):
                    conn.execute(
                        "INSERT INTO demolicion (red, label, unidad, precio) VALUES (?,?,?,?)",
                        (red, item["label"], item["unidad"], float(item["precio"])))

            # Acerados
            for red, clave in [("ABA", "acerados_aba"), ("SAN", "acerados_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO acerados (red, label, unidad, precio) VALUES (?,?,?,?)",
                        (red, item["label"], item["unidad"], float(item["precio"])))

            # Bordillos
            for item in precios["bordillos_reposicion"]:
                conn.execute(
                    "INSERT INTO bordillos (label, unidad, precio) VALUES (?,?,?)",
                    (item["label"], item["unidad"], float(item["precio"])))

            # Calzadas
            for item in precios["calzadas_reposicion"]:
                conn.execute(
                    "INSERT INTO calzadas (label, unidad, precio) VALUES (?,?,?)",
                    (item["label"], item["unidad"], float(item["precio"])))

            # Espesores calzada - lookup calzada ID por label
            calzada_ids = {
                row["label"]: row["id"]
                for row in conn.execute("SELECT id, label FROM calzadas")
            }
            for label, espesor in precios["espesores_calzada"].items():
                calzada_id = calzada_ids.get(label)
                if calzada_id is None:
                    raise ValueError(
                        f"Espesor definido para calzada '{label}' pero esa calzada "
                        "no existe en 'calzadas_reposicion'.")
                conn.execute(
                    "INSERT INTO espesores_calzada (calzada_id, espesor_m) VALUES (?,?)",
                    (calzada_id, float(espesor)))

            # Excavación
            for clave, valor in precios["excavacion"].items():
                conn.execute(
                    "INSERT INTO excavacion (clave, valor) VALUES (?,?)",
                    (clave, float(valor)))

            # Acometidas (con factor_piezas)
            for red, clave_tipo, clave_factor in [
                ("ABA", "acometidas_aba_tipos", "acometidas_aba_factores"),
                ("SAN", "acometidas_san_tipos", "acometidas_san_factores"),
            ]:
                factores = precios.get(clave_factor, {})
                for tipo, precio in precios[clave_tipo].items():
                    factor = float(factores.get(tipo, 1.2 if red == "ABA" else 1.0))
                    conn.execute(
                        "INSERT INTO acometidas (red, tipo, precio, factor_piezas) VALUES (?,?,?,?)",
                        (red, tipo, float(precio), factor))

            # Acometida por defecto
            for red, clave in [("ABA", "acometida_aba_defecto"), ("SAN", "acometida_san_defecto")]:
                conn.execute(
                    "INSERT INTO acometida_defecto (red, tipo) VALUES (?,?)",
                    (red, precios[clave]))

            # Defaults UI
            for clave, valor in precios["defaults_ui"].items():
                conn.execute(
                    "INSERT INTO defaults_ui (clave, valor) VALUES (?,?)",
                    (clave, float(valor)))

            # Sub-bases
            for item in precios.get("catalogo_subbases", []):
                conn.execute(
                    "INSERT INTO subbases (label, precio_m3) VALUES (?,?)",
                    (item["label"], float(item["precio_m3"])))

            # Desmontaje
            for item in precios.get("catalogo_desmontaje", []):
                conn.execute(
                    "INSERT INTO desmontaje (label, dn_max, precio_m, es_fibrocemento) VALUES (?,?,?,?)",
                    (item["label"], int(item["dn_max"]), float(item["precio_m"]),
                     int(item.get("es_fibrocemento", 0) or 0)))

            # Imbornales
            for item in precios.get("catalogo_imbornales", []):
                conn.execute(
                    "INSERT INTO imbornales (label, precio, tipo) VALUES (?,?,?)",
                    (item["label"], float(item["precio"]), item["tipo"]))

            # Pozos existentes
            for item in precios.get("catalogo_pozos_existentes", []):
                conn.execute(
                    "INSERT INTO pozos_existentes_precios (red, accion, precio, intervalo_m) VALUES (?,?,?,?)",
                    (item["red"], item["accion"], float(item["precio"]),
                     float(item.get("intervalo_m", 100))))

            conn.commit()

        except Exception as e:
            logger.error("Error en guardar_todo: %s", e, exc_info=True)
            conn.rollback()
            raise
