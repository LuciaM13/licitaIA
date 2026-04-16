"""Carga, persistencia y formateo de precios.

Interfaz pública:
    cargar_precios() -> dict
    guardar_precios(dict) -> None
    euro(float) -> str

Internamente usa SQLite (src/db.py). La interfaz dict se mantiene
para backward compatibility con calcular.py y presupuesto.py.
"""

from __future__ import annotations

import logging
import sqlite3

import streamlit as st

from src.infraestructura.db import cargar_todo, guardar_todo

logger = logging.getLogger(__name__)

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
        "pct_gg": (0.0, 1.0), "pct_bi": (0.0, 1.0), "pct_iva": (0.001, 1.0),
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

    # Validación: unidades duplicadas en catálogos de demolición
    for clave_demo in ("demolicion_aba", "demolicion_san"):
        demo = precios.get(clave_demo, [])
        unidades_vistas: set[str] = set()
        for item in demo:
            u = item.get("unidad", "")
            if u in unidades_vistas:
                errores.append(
                    f"El catálogo '{clave_demo}' tiene unidad duplicada '{u}'. "
                    "Cada unidad (m2, m) debe aparecer una sola vez."
                )
            unidades_vistas.add(u)

    return errores


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Registro único de todos los campos que escalan con CI.
#
# Cada tupla = (clave_catalogo, campo_precio). Este registro es la ÚNICA
# fuente de verdad para aplicar y revertir CI - nunca duplicar lógica fuera.
# factor_piezas y campos dimensionales NO se incluyen (no son precios).
# ---------------------------------------------------------------------------

_CI_CAMPOS: list[tuple[str, str]] = [
    # Catálogos principales
    ("catalogo_valvuleria", "precio"),
    ("catalogo_valvuleria", "precio_material"),
    ("catalogo_pozos", "precio"),
    ("catalogo_pozos", "precio_tapa"),
    ("catalogo_pozos", "precio_tapa_material"),
    ("catalogo_pozos", "precio_pate_material"),
    ("acerados_aba", "precio"),
    ("acerados_san", "precio"),
    ("bordillos_reposicion", "precio"),
    ("calzadas_reposicion", "precio"),
    ("demolicion_aba", "precio"),
    ("demolicion_san", "precio"),
    ("catalogo_aba", "precio_m"),
    ("catalogo_aba", "precio_material_m"),
    ("catalogo_san", "precio_m"),
    ("catalogo_san", "precio_material_m"),
    ("catalogo_entibacion", "precio_m2"),
    ("catalogo_subbases", "precio_m3"),
    ("catalogo_desmontaje", "precio_m"),
    ("catalogo_imbornales", "precio"),
    ("catalogo_pozos_existentes", "precio"),
]

# Claves de tipo dict (no lista de dicts) que escalan con CI
_CI_DICTS: list[tuple[str, set[str] | None]] = [
    # (clave_dict, claves_a_excluir | None = escalar todas)
    ("excavacion", {"umbral_profundidad_m"}),
    ("acometidas_aba_tipos", None),
    ("acometidas_san_tipos", None),
]

# Escalares sueltos que escalan con CI
_CI_ESCALARES: list[str] = [
    "conduccion_provisional_precio_m",
]


def _transformar_ci(precios: dict, multiplicar: bool) -> None:
    """Aplica o revierte el factor CI sobre todos los campos de precio.

    Si ``multiplicar`` es True, multiplica (para cargar). Si es False, divide
    (para persistir). Usa ``_CI_CAMPOS``, ``_CI_DICTS`` y ``_CI_ESCALARES``
    como única fuente de verdad - no hay lógica de CI fuera de esta función.
    """
    pct_ci = float(precios.get("pct_ci", 1.0))
    accion = "aplicar" if multiplicar else "revertir"
    if pct_ci == 1.0:
        logger.debug("[CI] pct_ci=1.0 → nada que %s", accion)
        return

    logger.debug("[CI] %s CI factor=%.4f sobre todos los precios", accion.upper(), pct_ci)
    op = (lambda v: v * pct_ci) if multiplicar else (lambda v: round(v / pct_ci, 6))

    # Catálogos (lista de dicts)
    for clave, campo in _CI_CAMPOS:
        for item in precios.get(clave, []):
            val = item.get(campo)
            if val:  # None, 0, 0.0 → no escalar
                item[campo] = op(val)

    # Dicts planos
    for clave_dict, excluir in _CI_DICTS:
        d = precios.get(clave_dict, {})
        excluir = excluir or set()
        for k in list(d.keys()):
            if k not in excluir:
                d[k] = op(d[k])

    # Escalares sueltos
    for clave_esc in _CI_ESCALARES:
        if clave_esc in precios:
            precios[clave_esc] = op(precios[clave_esc])


def _aplicar_ci(precios: dict) -> None:
    """Multiplica todos los precios unitarios por el factor de Costes Indirectos.

    Modifica el dict in-place. Si pct_ci es 1.0 o no existe, no hace nada.
    Uso interno - llamar desde calcular_presupuesto() sobre una copia local.
    """
    _transformar_ci(precios, multiplicar=True)


# Alias público para uso desde ensamblaje.py
aplicar_ci = _aplicar_ci


@st.cache_data(ttl=60)
def cargar_precios() -> dict:
    """Carga precios BASE desde SQLite con cache de 60s.

    Devuelve precios SIN CI aplicado. El CI se aplica una única vez en
    calcular_presupuesto() sobre una copia local, evitando transformaciones
    en el flujo de carga/guardado y eliminando la posibilidad de deflación
    o inflación acumulativa por round-trips admin → BD.

    La cache se invalida automáticamente tras TTL o manualmente con
    cargar_precios.clear() (llamar tras guardar en admin).
    """
    logger.info("cargar_precios() - leyendo BD…")
    try:
        precios = cargar_todo()
    except sqlite3.Error as e:
        logger.error("Error leyendo BD de precios: %s", e)
        raise ValueError(f"Error leyendo la base de datos de precios: {e}")

    # NO se aplica CI aquí - se aplica en calcular_presupuesto()

    errores = _validar_precios(precios)
    if errores:
        logger.error("Validación fallida: %s", errores)
        raise ValueError("BD de precios invalida:\n" + "\n".join(f"- {e}" for e in errores))

    # Log resumen de catálogos cargados
    for clave in sorted(_CLAVES_REQUERIDAS):
        val = precios.get(clave)
        if isinstance(val, list):
            logger.debug("  %s: %d items", clave, len(val))
        elif isinstance(val, dict):
            logger.debug("  %s: %d claves", clave, len(val))
        else:
            logger.debug("  %s = %s", clave, val)

    logger.info("cargar_precios() OK - pct_ci=%.4f", float(precios.get("pct_ci", 1.0)))
    return precios


def guardar_precios(precios: dict) -> None:
    """Guarda el dict completo de precios BASE en SQLite con transacción atómica.

    Recibe precios BASE (sin CI) y los persiste directamente, sin ninguna
    transformación CI. La BD siempre almacena precios base; el CI se aplica
    solo al calcular, nunca al cargar ni al guardar.
    """
    logger.info("guardar_precios() - validando y persistiendo…")
    errores = _validar_precios(precios)
    if errores:
        logger.error("Validación pre-guardado fallida: %s", errores)
        raise ValueError("No se puede guardar:\n" + "\n".join(f"- {e}" for e in errores))
    try:
        guardar_todo(precios)
        logger.info("guardar_precios() OK")
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "UNIQUE" in msg:
            raise ValueError("Error: hay elementos duplicados en los datos.") from e
        if "FOREIGN KEY" in msg or "foreign_key" in msg.lower():
            raise ValueError("Error de integridad: hay referencias cruzadas rotas entre tablas.") from e
        raise ValueError(f"Error de integridad en la base de datos: {e}") from e
    except sqlite3.Error as e:
        raise ValueError(f"Error escribiendo en la base de datos: {e}") from e
