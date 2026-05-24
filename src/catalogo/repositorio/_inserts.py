"""Mutadores SQL de bajo nivel para ``guardar_todo``.

Helpers privados al subpaquete: reciben una ``conn`` abierta dentro de la
transacción del orquestador y hacen DELETE/INSERT sin commit. La conversión
EUR→céntimos se aplica aquí con ``_eur_a_cents``; el commit/rollback queda
en el caller (``guardar_todo``).
"""

from __future__ import annotations

from src.almacenamiento import _TABLAS_PERMITIDAS
from src.almacenamiento.conversion_centimos import _eur_a_cents


# Orden de DELETE: dependientes primero. Respeta la única FK declarada
# (espesores_calzada → calzadas).
_TABLAS_BORRADO_EN_ORDEN = (
    "espesores_calzada", "acometida_defecto", "acometidas",
    "defaults_ui", "excavacion", "demolicion", "bordillos", "calzadas",
    "acerados", "pozos", "entibacion", "valvuleria",
    "tuberias", "config",
    "subbases", "desmontaje", "imbornales", "pozos_existentes_precios",
)


def _borrar_todo(conn) -> None:
    """DELETE de todas las tablas en orden FK-seguro (sin commit)."""
    for tabla in _TABLAS_BORRADO_EN_ORDEN:
        if tabla not in _TABLAS_PERMITIDAS:
            raise ValueError(f"Tabla no permitida: {tabla!r}")
        conn.execute(f"DELETE FROM {tabla}")


def _insertar_todos(conn, precios: dict) -> None:
    """INSERTs del dict ``precios`` en orden FK-seguro (sin commit).

    Padres antes que hijos: tuberias/calzadas antes que sus dependientes.
    Convierte monetarios a céntimos con ``_eur_a_cents``.
    """
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
