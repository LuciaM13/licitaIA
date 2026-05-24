"""Persistencia y validación del dict de precios.

API pública:
  - ``guardar_precios(dict) -> None`` — persiste el dict completo en BD.
  - ``_validar_precios(dict) -> list[str]`` — utilidad compartida con
    ``catalogo.carga``. Valida estructura y rangos.

La BD almacena precios BASE (sin CI). El factor CI se aplica solo al
calcular, no aquí.
"""

from __future__ import annotations

import logging
import sqlite3

from src.catalogo.repositorio import guardar_todo

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

    # Validación: (unidad, material) duplicado en catálogos de demolición.
    # Desde F3 (demolición con variantes por material) múltiples filas pueden
    # compartir unidad si tienen material distinto. La clave semántica es
    # (unidad, material). Si una fila no define material, se trata como 'generico'.
    for clave_demo in ("demolicion_aba", "demolicion_san"):
        demo = precios.get(clave_demo, [])
        combinaciones_vistas: set[tuple[str, str]] = set()
        for item in demo:
            u = item.get("unidad", "")
            mat = item.get("material") or "generico"
            clave = (u, mat)
            if clave in combinaciones_vistas:
                errores.append(
                    f"El catálogo '{clave_demo}' tiene (unidad='{u}', material='{mat}') "
                    f"duplicado. Cada combinación debe aparecer una sola vez."
                )
            combinaciones_vistas.add(clave)

    return errores


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
