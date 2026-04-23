"""Validación de precios vs `data/catalogo_oficial.json` (Excel EMASESA).

Detecta desviaciones del invariante `BD.precio × pct_ci ≈ precio_oficial_Excel`
cuando el admin va a guardar precios desde la UI. No bloquea: produce warnings
para que el admin confirme si la desviación es intencional.

Lógica canónica (NO confundir con comparar BD vs Excel directamente):
    Se detecta drift si  `|bd_precio * pct_ci - precio_oficial| / precio_oficial > umbral`.
    Con la convención del sistema (BD almacena precio base sin margen),
    esta comparación corresponde a "el precio con CI se desvía del oficial".
"""
from __future__ import annotations

import json
import logging
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

_CATALOGO_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "catalogo_oficial.json"

# Umbral de warning: se avisa si la desviación supera este porcentaje.
_UMBRAL_DRIFT_DEFAULT = 0.05  # 5 %


def _norm(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


def _cargar_catalogo_oficial() -> dict | None:
    """Lee el catálogo oficial si existe. None si no está disponible."""
    if not _CATALOGO_JSON.is_file():
        return None
    try:
        return json.loads(_CATALOGO_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("No se pudo leer %s: %s", _CATALOGO_JSON, e)
        return None


def detectar_drifts(precios: dict, pct_ci: float | None = None,
                    umbral: float = _UMBRAL_DRIFT_DEFAULT) -> list[dict]:
    """Devuelve lista de drifts detectados en los precios a guardar.

    Cada drift es un dict:
      {
        "categoria": str,           # ej. "tuberia_aba"
        "concepto": str,            # ej. "FD DN150"
        "bd_precio": float,         # el precio base que el admin va a guardar
        "precio_con_ci": float,     # bd_precio * pct_ci
        "precio_oficial": float,    # del Excel
        "drift_pct": float,         # porcentaje (positivo si con_ci > oficial)
      }

    Solo reporta drifts > `umbral` (por defecto 5 %).

    Si no hay catálogo oficial disponible, devuelve [] silenciosamente.
    """
    cat = _cargar_catalogo_oficial()
    if cat is None:
        return []
    if pct_ci is None:
        pct_ci = float(precios.get("pct_ci", 1.05))

    drifts = []

    def _add(categoria, concepto, bd_precio, precio_oficial):
        if bd_precio is None or precio_oficial is None or precio_oficial == 0:
            return
        precio_con_ci = bd_precio * pct_ci
        desvio_rel = abs(precio_con_ci - precio_oficial) / precio_oficial
        if desvio_rel > umbral:
            drift_pct = (precio_con_ci - precio_oficial) / precio_oficial * 100
            drifts.append({
                "categoria": categoria,
                "concepto": concepto,
                "bd_precio": round(bd_precio, 4),
                "precio_con_ci": round(precio_con_ci, 4),
                "precio_oficial": round(precio_oficial, 4),
                "drift_pct": round(drift_pct, 2),
            })

    # Excavación
    for clave, precio_oficial in cat.get("excavacion", {}).items():
        _add("excavacion", clave, precios.get("excavacion", {}).get(clave), precio_oficial)

    # Tubería ABA
    for item in cat.get("tuberia_aba", []):
        bd = _buscar_tuberia_bd(precios, "catalogo_aba", item["tipo"], item["dn"])
        _add("tuberia_aba", f"{item['tipo']} DN{item['dn']}", bd, item["precio"])

    # Tubería SAN
    for item in cat.get("tuberia_san", []):
        bd = _buscar_tuberia_bd(precios, "catalogo_san", item["tipo"], item["dn"])
        _add("tuberia_san", f"{item['tipo']} DN{item['dn']}", bd, item["precio"])

    # Valvulería conexión (rango)
    for item in cat.get("valvuleria_conexion", []):
        bd = _buscar_valvuleria_conexion_bd(precios, item["dn"])
        _add("valvuleria_conexion", f"DN{item['dn']}", bd, item["precio"])

    # Imbornales
    for item in cat.get("imbornales", []):
        bd = _buscar_imbornal_bd(precios, item["label"])
        _add("imbornales", item["label"], bd, item["precio"])

    # Pozos existentes (BD separa ABA/SAN — comprobar ambos precios contra
    # la referencia agregada del Excel para detectar cualquier drift real).
    for item in cat.get("pozos_existentes", []):
        accion = item["accion"]
        # Excel usa "acondicionamiento" para el pozo existente mantenido en
        # servicio; la BD no lo modela hoy (acondicionamiento no aparece en
        # `catalogo_pozos_existentes`). Se salta silenciosamente.
        if accion == "acondicionamiento":
            continue
        for red in ("ABA", "SAN"):
            bd = _buscar_pozo_existente_bd(precios, red, accion)
            _add("pozos_existentes", f"{red} {accion}", bd, item["precio"])

    # Entibación blindada (Excel único precio para ABA/SAN).
    for item in cat.get("entibacion_blindada", []):
        for red in ("ABA", "SAN"):
            bd = _buscar_entibacion_blindada_bd(precios, red)
            _add("entibacion_blindada", f"blindada {red}", bd, item["precio"])

    # Conducción provisional PE (escalar en config).
    precio_cp_oficial = cat.get("conduccion_provisional_pe")
    if precio_cp_oficial:
        _add("conduccion_provisional_pe", "PE",
             precios.get("conduccion_provisional_precio_m"),
             precio_cp_oficial)

    return drifts


def _buscar_tuberia_bd(precios, clave_catalogo, tipo, dn):
    for it in precios.get(clave_catalogo, []):
        if it.get("tipo") == tipo and int(it.get("diametro_mm", -1)) == dn:
            return it.get("precio_m")
    return None


def _buscar_valvuleria_conexion_bd(precios, dn):
    for it in precios.get("catalogo_valvuleria", []):
        if (it.get("tipo") == "conexion"
                and int(it.get("dn_min", 0)) <= dn <= int(it.get("dn_max", 0))):
            return it.get("precio")
    return None


def _buscar_imbornal_bd(precios, label):
    for it in precios.get("catalogo_imbornales", []):
        if it.get("label") == label:
            return it.get("precio")
    return None


def _buscar_pozo_existente_bd(precios, red, accion):
    """Pozos existentes: BD separa por `red` y `accion` (ABA/SAN × demol/anul)."""
    for it in precios.get("catalogo_pozos_existentes", []):
        if it.get("red") == red and it.get("accion") == accion:
            return it.get("precio")
    return None


def _buscar_entibacion_blindada_bd(precios, red):
    """Entibación: ignora variantes 'profunda' (enriquecimiento sin Excel)."""
    for it in precios.get("catalogo_entibacion", []):
        label = str(it.get("label", "")).lower()
        if "profunda" in label:
            continue
        if it.get("red") in (red, None):
            return it.get("precio_m2")
    return None
