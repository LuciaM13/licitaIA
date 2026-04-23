"""CRUD de catálogos de precios - cargar_todo() y guardar_todo().

Separado de db.py para mantener el fichero principal por debajo de 500 líneas.

Convención storage (desde Migración 13):
  - BD almacena precios como INTEGER céntimos (ej. 12.96 € → 1296).
  - cargar_todo() divide por 100 al leer → floats €.
  - guardar_todo() multiplica por 100 con round() al guardar → INTEGER céntimos.
  - El resto del código (dominio, UI) opera en floats €.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path

from src.infraestructura.db import conectar, _TABLAS_PERMITIDAS, _rows_to_dicts, _cargar_por_red

logger = logging.getLogger(__name__)


# Campos de precio monetario que se almacenan como INTEGER céntimos en BD.
# Se dividen por 100 al leer, se multiplican por 100 con round() al escribir.
_CAMPOS_MONETARIOS = {
    "tuberias": ("precio_m", "precio_material_m"),
    "valvuleria": ("precio", "precio_material"),
    "pozos": ("precio", "precio_tapa", "precio_tapa_material", "precio_pate_material"),
    "acerados": ("precio",),
    "bordillos": ("precio",),
    "calzadas": ("precio",),
    "demolicion": ("precio",),
    "entibacion": ("precio_m2",),
    "acometidas": ("precio",),
    "subbases": ("precio_m3",),
    "desmontaje": ("precio_m",),
    "imbornales": ("precio",),
    "pozos_existentes_precios": ("precio",),
}


def _cents_a_eur(val):
    """Convierte INTEGER céntimos → float €. None → None."""
    return val / 100.0 if val is not None else None


def _eur_a_cents(val):
    """Convierte float € → INTEGER céntimos con redondeo bancario (round())."""
    return round(float(val) * 100) if val is not None else 0


def _convertir_filas(filas, campos):
    """Aplica _cents_a_eur a los campos indicados en cada fila (list of dicts)."""
    for fila in filas:
        for campo in campos:
            if campo in fila:
                fila[campo] = _cents_a_eur(fila[campo])
    return filas


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


def _clave_audit(categoria: str, item) -> str:
    """Deriva una clave estable para identificar un ítem dentro de su categoría."""
    if isinstance(item, dict):
        # Listas de dicts: usar campos identificativos habituales
        for campo in ("label", "tipo", "clave"):
            if campo in item:
                return str(item[campo])
        return json.dumps(item, sort_keys=True, ensure_ascii=False)[:120]
    return str(item)


def _diff_categoria(categoria: str, antes, despues):
    """Devuelve lista de (clave, operacion, antes_json, despues_json).

    Compara dos colecciones (lista de dicts o dict plano) y emite un evento
    INSERT/UPDATE/DELETE por cada cambio lógico detectado.
    """
    eventos = []
    # Dict plano (excavacion, acometidas_*_tipos, espesores_calzada, defaults_ui)
    if isinstance(antes, dict) and not (antes and isinstance(next(iter(antes.values()), None), list)):
        claves = set(antes) | set(despues)
        for k in sorted(claves):
            a = antes.get(k)
            d = despues.get(k)
            if a == d:
                continue
            if k not in antes:
                eventos.append((categoria, str(k), "INSERT", None, json.dumps(d, ensure_ascii=False)))
            elif k not in despues:
                eventos.append((categoria, str(k), "DELETE", json.dumps(a, ensure_ascii=False), None))
            else:
                eventos.append((categoria, str(k), "UPDATE",
                                json.dumps(a, ensure_ascii=False),
                                json.dumps(d, ensure_ascii=False)))
        return eventos
    # Lista de dicts
    if isinstance(antes, list) and isinstance(despues, list):
        por_clave_antes = {_clave_audit(categoria, it): it for it in antes}
        por_clave_despues = {_clave_audit(categoria, it): it for it in despues}
        claves = set(por_clave_antes) | set(por_clave_despues)
        for k in sorted(claves):
            a = por_clave_antes.get(k)
            d = por_clave_despues.get(k)
            if a == d:
                continue
            if a is None:
                eventos.append((categoria, k, "INSERT", None, json.dumps(d, ensure_ascii=False)))
            elif d is None:
                eventos.append((categoria, k, "DELETE", json.dumps(a, ensure_ascii=False), None))
            else:
                eventos.append((categoria, k, "UPDATE",
                                json.dumps(a, ensure_ascii=False),
                                json.dumps(d, ensure_ascii=False)))
    return eventos


def _categorias_a_auditar():
    """Listas/dicts del dict `precios` que se auditan en audit_log."""
    return [
        "catalogo_aba", "catalogo_san", "catalogo_valvuleria",
        "catalogo_entibacion", "catalogo_pozos",
        "demolicion_aba", "demolicion_san",
        "acerados_aba", "acerados_san",
        "bordillos_reposicion", "calzadas_reposicion", "espesores_calzada",
        "excavacion", "acometidas_aba_tipos", "acometidas_san_tipos",
        "catalogo_subbases", "catalogo_desmontaje",
        "catalogo_imbornales", "catalogo_pozos_existentes",
    ]


def _escribir_audit_log(conn, eventos, actor):
    for categoria, clave, operacion, antes_json, despues_json in eventos:
        conn.execute(
            "INSERT INTO audit_log (categoria, clave, operacion, antes_json, despues_json, actor) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (categoria, clave, operacion, antes_json, despues_json, actor),
        )


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
    # Snapshot antes de los cambios (para diff audit)
    try:
        snapshot_antes = cargar_todo(path)
    except Exception:
        # BD vacía o primer arranque: no hay snapshot previo, cada INSERT es un alta.
        snapshot_antes = {cat: [] for cat in _categorias_a_auditar()}
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

            # Tuberías (con factor_piezas y precio_material_m) - precios a céntimos
            for red, clave in [("ABA", "catalogo_aba"), ("SAN", "catalogo_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO tuberias (red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m) VALUES (?,?,?,?,?,?,?)",
                        (red, item["label"], item["tipo"], int(item["diametro_mm"]),
                         _eur_a_cents(item["precio_m"]),
                         float(item.get("factor_piezas", 1.0)),
                         _eur_a_cents(item.get("precio_material_m", 0.0))))

            # Valvulería (con factor_piezas, precio_material e instalacion nullable)
            for item in precios["catalogo_valvuleria"]:
                inst = item.get("instalacion")
                conn.execute(
                    "INSERT INTO valvuleria (label, tipo, dn_min, dn_max, precio, intervalo_m, instalacion, factor_piezas, precio_material) VALUES (?,?,?,?,?,?,?,?,?)",
                    (item["label"], item["tipo"], int(item["dn_min"]), int(item["dn_max"]),
                     _eur_a_cents(item["precio"]), float(item["intervalo_m"]), inst,
                     float(item.get("factor_piezas", 1.2)),
                     _eur_a_cents(item.get("precio_material", 0.0))))

            # Entibación (con columna red nullable)
            for item in precios["catalogo_entibacion"]:
                red = item.get("red")
                conn.execute(
                    "INSERT INTO entibacion (label, precio_m2, umbral_m, red) VALUES (?,?,?,?)",
                    (item["label"], _eur_a_cents(item["precio_m2"]),
                     float(item["umbral_m"]), red))

            # Pozos (con columnas opcionales + precio_tapa + precio_pate_material SAN)
            for item in precios["catalogo_pozos"]:
                prof_max = item.get("profundidad_max")
                dn_max = item.get("dn_max")
                conn.execute(
                    "INSERT INTO pozos (label, precio, intervalo, red, profundidad_max, dn_max, precio_tapa, precio_tapa_material, precio_pate_material) VALUES (?,?,?,?,?,?,?,?,?)",
                    (item["label"], _eur_a_cents(item["precio"]),
                     float(item["intervalo"]),
                     item.get("red"),
                     float(prof_max) if prof_max is not None else None,
                     int(dn_max) if dn_max is not None else None,
                     _eur_a_cents(item.get("precio_tapa", 0.0) or 0.0),
                     _eur_a_cents(item.get("precio_tapa_material", 0.0) or 0.0),
                     _eur_a_cents(item.get("precio_pate_material", 0.0) or 0.0)))

            # Demolición (con variantes de material; 'generico' default para legacy)
            for red, clave in [("ABA", "demolicion_aba"), ("SAN", "demolicion_san")]:
                for item in precios.get(clave, []):
                    conn.execute(
                        "INSERT INTO demolicion (red, label, unidad, material, precio) "
                        "VALUES (?,?,?,?,?)",
                        (red, item["label"], item["unidad"],
                         item.get("material", "generico"),
                         _eur_a_cents(item["precio"])))

            # Acerados
            for red, clave in [("ABA", "acerados_aba"), ("SAN", "acerados_san")]:
                for item in precios[clave]:
                    conn.execute(
                        "INSERT INTO acerados (red, label, unidad, precio) VALUES (?,?,?,?)",
                        (red, item["label"], item["unidad"], _eur_a_cents(item["precio"])))

            # Bordillos
            for item in precios["bordillos_reposicion"]:
                conn.execute(
                    "INSERT INTO bordillos (label, unidad, precio) VALUES (?,?,?)",
                    (item["label"], item["unidad"], _eur_a_cents(item["precio"])))

            # Calzadas
            for item in precios["calzadas_reposicion"]:
                conn.execute(
                    "INSERT INTO calzadas (label, unidad, precio) VALUES (?,?,?)",
                    (item["label"], item["unidad"], _eur_a_cents(item["precio"])))

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
                    factor = float(factores.get(tipo, 1.0))
                    conn.execute(
                        "INSERT INTO acometidas (red, tipo, precio, factor_piezas) VALUES (?,?,?,?)",
                        (red, tipo, _eur_a_cents(precio), factor))

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
                    (item["label"], _eur_a_cents(item["precio_m3"])))

            # Desmontaje
            for item in precios.get("catalogo_desmontaje", []):
                conn.execute(
                    "INSERT INTO desmontaje (label, dn_max, precio_m, es_fibrocemento) VALUES (?,?,?,?)",
                    (item["label"], int(item["dn_max"]),
                     _eur_a_cents(item["precio_m"]),
                     int(item.get("es_fibrocemento", 0) or 0)))

            # Imbornales
            for item in precios.get("catalogo_imbornales", []):
                conn.execute(
                    "INSERT INTO imbornales (label, precio, tipo) VALUES (?,?,?)",
                    (item["label"], _eur_a_cents(item["precio"]), item["tipo"]))

            # Pozos existentes
            for item in precios.get("catalogo_pozos_existentes", []):
                conn.execute(
                    "INSERT INTO pozos_existentes_precios (red, accion, precio, intervalo_m) VALUES (?,?,?,?)",
                    (item["red"], item["accion"],
                     _eur_a_cents(item["precio"]),
                     float(item.get("intervalo_m", 100))))

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
