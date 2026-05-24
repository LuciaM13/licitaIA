"""Carga del dict de precios desde BD + aplicación del CI.

API pública:
  - ``cargar_precios() -> dict`` — lee BD, valida y devuelve dict BASE (sin CI).
  - ``aplicar_ci(dict) -> None`` — multiplica precios por ``pct_ci`` in-place.

Esta función es pura (sin cache). El cache para la UI Streamlit vive en
``src/ui/precios_cache.py``; la UI debe importar desde allí si quiere
invalidación manual vía ``cargar_precios.clear()``.
"""

from __future__ import annotations

import logging
import sqlite3

from src.catalogo.guardado import _CLAVES_REQUERIDAS, _validar_precios
from src.catalogo.repositorio import cargar_todo

logger = logging.getLogger(__name__)


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


def aplicar_ci(precios: dict) -> None:
    """Multiplica todos los precios unitarios por el factor de Costes Indirectos.

    Modifica el dict in-place. Si pct_ci es 1.0 o no existe, no hace nada.
    Uso interno - llamar desde calcular_presupuesto() sobre una copia local.

    ``_CI_CAMPOS``, ``_CI_DICTS`` y ``_CI_ESCALARES`` son la única fuente de
    verdad sobre qué campos escalan con CI.

    Convención del CI (invariante del sistema)
    -------------------------------------------
    La BD almacena precios **base sin margen de seguridad**. ``pct_ci`` es el
    margen configurable por el licitador (default ``PCT_CI_DEFAULT`` = 1.05,
    definido en ``src.modelo.constantes``). Con el default, el resultado es
    equivalente al Excel oficial EMASESA, que ya incorpora ese 5 % de margen
    estándar ("prefiero pasarse a quedarse corto").

    Invariante: ``BD.precio × pct_ci(1.05) == precio_oficial_EMASESA_Excel``.

    Implicación operacional: al añadir un precio nuevo desde la UI admin hay
    que introducir ``valor_Excel / 1.05`` (el precio BASE), no el valor Excel
    directo. Si se guarda el valor Excel tal cual, el runtime aplica otro 1.05
    y queda ``valor_Excel × 1.05`` (sobrevaloración).

    Migraciones históricas que corrigieron violaciones de esta invariante:
    M6 (entibación, factor 1.406→1.05), M8 (18 precios Patrón A ratio 1.05²
    + Gres SAN DN300), M10 (5 imbornales ratio 1.05³), M11 (residuales de
    excavación carga_mec + arrinonado).

    Storage (desde M13): los precios en BD son INTEGER céntimos (ej. 12.96 €
    → 1296). `cargar_todo()` / `guardar_todo()` hacen la traducción al dict
    Python (floats €). Esta función opera siempre en floats €.
    """
    pct_ci = float(precios.get("pct_ci", 1.0))
    if pct_ci == 1.0:
        logger.debug("[CI] pct_ci=1.0 → nada que aplicar")
        return

    logger.debug("[CI] APLICAR CI factor=%.4f sobre todos los precios", pct_ci)

    # Catálogos (lista de dicts)
    for clave, campo in _CI_CAMPOS:
        for item in precios.get(clave, []):
            val = item.get(campo)
            if val:  # None, 0, 0.0 → no escalar
                item[campo] = val * pct_ci

    # Dicts planos
    for clave_dict, excluir in _CI_DICTS:
        d = precios.get(clave_dict, {})
        excluir = excluir or set()
        for k in list(d.keys()):
            if k not in excluir:
                d[k] = d[k] * pct_ci

    # Escalares sueltos
    for clave_esc in _CI_ESCALARES:
        if clave_esc in precios:
            precios[clave_esc] = precios[clave_esc] * pct_ci


def cargar_precios() -> dict:
    """Carga precios BASE desde SQLite.

    Devuelve precios SIN CI aplicado. El CI se aplica una única vez en
    calcular_presupuesto() sobre una copia local, evitando transformaciones
    en el flujo de carga/guardado y eliminando la posibilidad de deflación
    o inflación acumulativa por round-trips admin → BD.
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
