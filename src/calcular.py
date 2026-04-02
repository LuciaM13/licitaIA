"""
Funciones de cálculo de partidas y capítulos.

Modelo simplificado (rectangular): volumen = largo × ancho × profundidad.
No accede a UI ni a ficheros. No define modelos ni formatea salida.
"""

from __future__ import annotations

from typing import Any, Dict

from src import config as dc


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (privadas)
# ═══════════════════════════════════════════════════════════════════════════════

# Calcula importe = cantidad × precio, forzando mínimo 0 en ambos
def _importe(cantidad: float, precio: float) -> float:
    return max(float(cantidad or 0), 0.0) * max(float(precio or 0), 0.0)


# Devuelve el ancho de zanja (m) según diámetro de tubería y tipo de red (saneamiento o abastecimiento)
# Si el diámetro no está tabulado, lanza ValueError.
def _ancho_zanja(diametro_mm: int, es_san: bool) -> float:
    tabla = dc.ANCHO_ZANJA_SAN if es_san else dc.ANCHO_ZANJA_ABA
    tipo = "saneamiento" if es_san else "abastecimiento"
    if diametro_mm not in tabla:
        validos = sorted(tabla.keys())
        raise ValueError(
            f"Diámetro {diametro_mm} mm no válido para {tipo}. "
            f"Diámetros disponibles: {validos}"
        )
    return tabla[diametro_mm]


# Elige precio de excavación según si la profundidad supera el umbral (2.5 m)
def _precio_excavacion(profundidad: float, exc: dict) -> float:
    umbral = dc.PROFUNDIDAD_EXCAVACION_UMBRAL_M
    return exc["mec_hasta_25"] if profundidad <= umbral else exc["mec_mas_25"]


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO DE OBRA CIVIL — Modelo rectangular de zanja
# ═══════════════════════════════════════════════════════════════════════════════
# Calcula el capítulo 1 o el 2
# Dependiendo de si hay abastecimiento, saneamiento o ambos

def _capitulo_obra_civil_red(
    longitud: float,
    profundidad: float,
    precio_tuberia: float,
    nombre_tuberia: str,
    exc: dict,
    diametro_mm: int = 0,
    es_san: bool = False,
):
    ancho = _ancho_zanja(diametro_mm, es_san)
    espesor_relleno = dc.ESPESOR_RELLENO_SAN if es_san else dc.ESPESOR_RELLENO_ABA

    # Volúmenes (m³)
    vol_zanja = max(longitud, 0.0) * max(profundidad, 0.0) * max(ancho, 0.0)
    vol_arena = max(longitud, 0.0) * max(ancho, 0.0) * dc.ESPESOR_ARENA
    vol_relleno = max(longitud, 0.0) * max(ancho, 0.0) * espesor_relleno
    vol_transporte = max(vol_zanja - vol_arena - vol_relleno, 0.0)

    # Partidas: cantidad × precio unitario
    partidas = {
        nombre_tuberia: _importe(longitud, precio_tuberia),
        "Excavación mecánica": _importe(vol_zanja, _precio_excavacion(profundidad, exc)),
        "Suministro de arena": _importe(vol_arena, exc["arena"]),
        "Relleno de albero": _importe(vol_relleno, exc["relleno"]),
        "Carga de tierras": _importe(vol_transporte, exc["carga"]),
        "Transporte a vertedero": _importe(vol_transporte, exc["transporte"]),
        "Canon vertido tierras": _importe(vol_transporte, exc["canon_tierras"]),
    }

    subtotal = sum(partidas.values())
    auxiliares = {
        "ancho_zanja_m": round(ancho, 3),
        "vol_zanja_m3": round(vol_zanja, 3),
        "vol_arena_m3": round(vol_arena, 3),
        "vol_relleno_m3": round(vol_relleno, 3),
        "vol_transporte_m3": round(vol_transporte, 3),
    }
    return subtotal, partidas, auxiliares


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSIÓN DE UNIDADES — Calzada (m² → m³)
# ═══════════════════════════════════════════════════════════════════════════════
# Si el item está en m² se usa directo; si está en m³ se convierte
# multiplicando superficie × espesor.

def _importe_calzada_desde_m2(item: Dict[str, Any], superficie_m2: float,
                               espesores: dict) -> float:
    if item.get("unidad") == "m2":
        return _importe(superficie_m2, item["precio"])
    espesor = espesores.get(item["label"], 0.15)
    return _importe(superficie_m2 * espesor, item["precio"])


# ═══════════════════════════════════════════════════════════════════════════════
# GENERADORES DE CAPÍTULOS
# ═══════════════════════════════════════════════════════════════════════════════
# Cada función devuelve (subtotal, partidas) o None si no aplica.

# Pavimentación: reposición de superficie tras abrir y cerrar la zanja
def _capitulo_pavimentacion(
    qty1: float, item1: Dict[str, Any],
    qty2: float, item2: Dict[str, Any],
    *,
    calzada_conversion: bool = False,
    espesores: dict | None = None,
) -> tuple[float, dict] | None:
    if qty1 <= 0 and qty2 <= 0:
        return None
    partidas = {}
    if item1:
        partidas[item1["label"]] = (
            _importe_calzada_desde_m2(item1, qty1, espesores or {}) if calzada_conversion
            else _importe(qty1, item1["precio"]))
    if item2:
        partidas[item2["label"]] = _importe(qty2, item2["precio"])
    return sum(partidas.values()), partidas


#Calcula el coste de las conexiones domiciliarias
def _capitulo_acometidas(n: int, precio: float, label: str) -> tuple[float, dict] | None:
    if n <= 0:
        return None
    importe = _importe(n, precio)
    return importe, {label: importe}


# Importes fijos
# Se usa en seguridad, gestión ambiental
def _capitulo_importe_fijo(importe: float, label: str) -> tuple[float, dict] | None:
    if importe <= 0:
        return None
    return importe, {label: importe}
