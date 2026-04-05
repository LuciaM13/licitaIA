"""Carga, persistencia y formateo de precios.

Interfaz pública:
    cargar_precios() -> dict
    guardar_precios(dict) -> None
    euro(float) -> str

Internamente usa SQLite (src/db.py). La interfaz dict se mantiene
para backward compatibility con calcular.py y presupuesto.py.
"""

from __future__ import annotations

import sqlite3

import streamlit as st

from src.db import cargar_todo, guardar_todo

# ---------------------------------------------------------------------------
# Validación (intencionalmente redundante con los FK constraints de SQLite)
#
# La validación Python produce mensajes de error legibles en español para el
# usuario (ej: "Calzada 'X' tiene unidad m3 pero no tiene espesor definido").
# Los FK constraints de SQLite son la red de seguridad silenciosa que impide
# datos inconsistentes aunque la validación Python tenga un bug.
# ---------------------------------------------------------------------------

_CLAVES_REQUERIDAS = {
    "pct_gg", "pct_bi", "pct_iva",
    "factor_esponjamiento", "pct_manual_defecto",
    "pct_ci", "conduccion_provisional_precio_m",
    "catalogo_aba", "catalogo_san",
    "acerados_aba", "acerados_san",
    "bordillos_reposicion", "calzadas_reposicion",
    "espesores_calzada", "excavacion",
    # anchos_zanja y espesores_arrinonado ya no son necesarios para el cálculo
    # (se usan fórmulas del Excel directamente), pero las tablas siguen en la BD.
    "catalogo_entibacion", "catalogo_pozos", "catalogo_valvuleria",
    "demolicion_aba", "demolicion_san",
    "acometidas_aba_tipos", "acometidas_san_tipos",
    "acometida_aba_defecto", "acometida_san_defecto",
    "defaults_ui",
}

_CLAVES_EXCAVACION = {
    "mec_hasta_25", "mec_mas_25", "manual_hasta_25", "manual_mas_25",
    "arrinonado", "relleno",
    "carga_mec", "transporte", "canon_tierras", "canon_mixto",
    "umbral_profundidad_m",
}

_CLAVES_DEFAULTS_UI = {
    "aba_longitud_m", "aba_profundidad_m",
    "san_longitud_m", "san_profundidad_m",
    "pav_aba_acerado_m2", "pav_aba_bordillo_m",
    "pav_san_calzada_m2", "pav_san_acera_m2",
    "acometidas_n", "pct_seguridad", "pct_gestion",
}


def _validar_precios(precios: dict) -> list[str]:
    """Valida estructura del dict de precios. Retorna lista de errores."""
    errores = []
    faltantes = _CLAVES_REQUERIDAS - precios.keys()
    if faltantes:
        errores.append(f"Faltan claves: {', '.join(sorted(faltantes))}")
    exc_faltantes = _CLAVES_EXCAVACION - precios.get("excavacion", {}).keys()
    if exc_faltantes:
        errores.append(f"Seccion 'excavacion' incompleta, faltan: {', '.join(sorted(exc_faltantes))}")
    dui_faltantes = _CLAVES_DEFAULTS_UI - precios.get("defaults_ui", {}).keys()
    if dui_faltantes:
        errores.append(f"Seccion 'defaults_ui' incompleta, faltan: {', '.join(sorted(dui_faltantes))}")
    for clave in _CLAVES_REQUERIDAS:
        val = precios.get(clave)
        if isinstance(val, (list, dict)) and not val:
            errores.append(f"El catalogo '{clave}' esta vacio")

    # Validación de rangos de porcentajes financieros
    _RANGOS_PCT = {
        "pct_gg": (0.0, 1.0), "pct_bi": (0.0, 1.0), "pct_iva": (0.0, 1.0),
        "pct_ci": (1.0, 1.20),
    }
    for clave_pct, (minimo, maximo) in _RANGOS_PCT.items():
        val_pct = precios.get(clave_pct)
        if val_pct is not None:
            try:
                v = float(val_pct)
                if v < minimo or v > maximo:
                    errores.append(
                        f"'{clave_pct}' = {v} fuera del rango permitido [{minimo}, {maximo}]."
                    )
            except (TypeError, ValueError):
                errores.append(f"'{clave_pct}' no es un valor numérico válido.")

    # Validación cross-catalog: calzadas m3 deben tener espesor
    calzadas = precios.get("calzadas_reposicion", [])
    espesores = precios.get("espesores_calzada", {})
    labels_calzadas = {e.get("label", "") for e in calzadas if isinstance(e, dict)}
    for entrada in calzadas:
        if isinstance(entrada, dict) and entrada.get("unidad") == "m3":
            label = entrada.get("label", "")
            if label and label not in espesores:
                errores.append(
                    f"Calzada '{label}' tiene unidad m3 pero no tiene espesor "
                    "definido en 'espesores_calzada'."
                )
    # Validación inversa: espesores sin calzada correspondiente
    for label_esp in espesores:
        if label_esp not in labels_calzadas:
            errores.append(
                f"Espesor definido para '{label_esp}' pero no existe "
                "esa calzada en 'calzadas_reposicion'."
            )
    return errores


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

_CI_CATALOGOS = {
    # (clave_catalogo, campo_precio_a_escalar)
    # factor_piezas y precio_material NO se escalan con CI — son coeficientes/precios base
    "catalogo_valvuleria": "precio",
    "catalogo_pozos": "precio",
    "acerados_aba": "precio",
    "acerados_san": "precio",
    "bordillos_reposicion": "precio",
    "calzadas_reposicion": "precio",
    "demolicion_aba": "precio",
    "demolicion_san": "precio",
    "catalogo_aba": "precio_m",
    "catalogo_san": "precio_m",
    "catalogo_entibacion": "precio_m2",
    "catalogo_subbases": "precio_m3",
}


def _aplicar_ci(precios: dict) -> None:
    """Multiplica todos los precios unitarios por el factor de Costes Indirectos.

    El factor pct_ci se almacena como multiplicador (ej: 1.05 = +5% CI).
    Si no existe o es 1.0, no hace nada. Modifica el dict in-place.
    factor_piezas NO se escala (es un multiplicador dimensional, no un precio).
    """
    pct_ci = float(precios.get("pct_ci", 1.0))
    if pct_ci == 1.0:
        return

    # Catálogos (lista de dicts con campo de precio variable)
    for clave, campo in _CI_CATALOGOS.items():
        for item in precios.get(clave, []):
            if campo in item:
                item[campo] = item[campo] * pct_ci

    # Desmontaje, imbornales y pozos existentes también escalan con CI
    for item in precios.get("catalogo_desmontaje", []):
        if "precio_m" in item:
            item["precio_m"] = item["precio_m"] * pct_ci
    for item in precios.get("catalogo_imbornales", []):
        if "precio" in item:
            item["precio"] = item["precio"] * pct_ci
    for item in precios.get("catalogo_pozos_existentes", []):
        if "precio" in item:
            item["precio"] = item["precio"] * pct_ci

    # Precios de material también escalan con CI
    for item in precios.get("catalogo_aba", []):
        if "precio_material_m" in item and item["precio_material_m"]:
            item["precio_material_m"] = item["precio_material_m"] * pct_ci
    for item in precios.get("catalogo_valvuleria", []):
        if "precio_material" in item and item["precio_material"]:
            item["precio_material"] = item["precio_material"] * pct_ci
    for item in precios.get("catalogo_pozos", []):
        if "precio_tapa" in item and item.get("precio_tapa"):
            item["precio_tapa"] = item["precio_tapa"] * pct_ci
        if "precio_tapa_material" in item and item.get("precio_tapa_material"):
            item["precio_tapa_material"] = item["precio_tapa_material"] * pct_ci

    # Dict excavación (todas las claves excepto umbral)
    for clave, valor in precios.get("excavacion", {}).items():
        if clave != "umbral_profundidad_m":
            precios["excavacion"][clave] = valor * pct_ci

    # Dicts acometidas
    for clave_acom in ("acometidas_aba_tipos", "acometidas_san_tipos"):
        for tipo in precios.get(clave_acom, {}):
            precios[clave_acom][tipo] = precios[clave_acom][tipo] * pct_ci

    # Escalar conducción provisional
    if "conduccion_provisional_precio_m" in precios:
        precios["conduccion_provisional_precio_m"] = (
            precios["conduccion_provisional_precio_m"] * pct_ci)


@st.cache_data(ttl=60)
def cargar_precios() -> dict:
    """Carga precios desde SQLite con cache de 60s.

    La cache se invalida automáticamente tras TTL o manualmente con
    cargar_precios.clear() (llamar tras guardar en admin).
    """
    try:
        precios = cargar_todo()
    except sqlite3.Error as e:
        raise ValueError(f"Error leyendo la base de datos de precios: {e}")

    _aplicar_ci(precios)

    errores = _validar_precios(precios)
    if errores:
        raise ValueError("BD de precios invalida:\n" + "\n".join(f"- {e}" for e in errores))

    return precios


def guardar_precios(precios: dict) -> None:
    """Guarda el dict completo de precios en SQLite con transacción atómica."""
    errores = _validar_precios(precios)
    if errores:
        raise ValueError("No se puede guardar:\n" + "\n".join(f"- {e}" for e in errores))
    try:
        guardar_todo(precios)
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "UNIQUE" in msg:
            raise ValueError("Error: hay elementos duplicados en los datos.") from e
        if "FOREIGN KEY" in msg or "foreign_key" in msg.lower():
            raise ValueError("Error de integridad: hay referencias cruzadas rotas entre tablas.") from e
        raise ValueError(f"Error de integridad en la base de datos: {e}") from e
    except sqlite3.Error as e:
        raise ValueError(f"Error escribiendo en la base de datos: {e}") from e


# Re-export euro desde utils para backward compatibility
from src.utils import euro  # noqa: F401
