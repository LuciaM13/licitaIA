from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import datos as d

@dataclass
class ParametrosProyecto:
    aba_item: Dict[str, Any]
    aba_longitud_m: float
    aba_profundidad_m: float
    san_item: Dict[str, Any]
    san_longitud_m: float
    san_profundidad_m: float
    pav_aba_acerado_m2: float
    pav_aba_acerado_item: Dict[str, Any]
    pav_aba_bordillo_m: float
    pav_aba_bordillo_item: Dict[str, Any]
    pav_san_calzada_m2: float
    pav_san_calzada_item: Dict[str, Any]
    pav_san_acera_m2: float
    pav_san_acera_item: Dict[str, Any]
    acometidas_aba_n: int
    acometidas_san_n: int
    pct_seguridad: float
    pct_gestion: float

def _importe(cantidad: float, precio: float) -> float:
    return max(float(cantidad or 0), 0.0) * max(float(precio or 0), 0.0)

def _ancho_zanja_aba(diametro: int) -> float:
    return d.ANCHO_ZANJA_ABA.get(int(diametro), 0.90)

def _ancho_zanja_san(diametro: int) -> float:
    return d.ANCHO_ZANJA_SAN.get(int(diametro), 1.20)

def _precio_excavacion(profundidad: float) -> float:
    return d.EXCAVACION["mec_hasta_25"] if profundidad <= 2.5 else d.EXCAVACION["mec_mas_25"]

def _capitulo_obra_civil_red(longitud: float, profundidad: float, ancho: float, precio_tuberia: float, espesor_relleno: float, nombre_tuberia: str):
    vol_zanja = max(longitud, 0.0) * max(profundidad, 0.0) * max(ancho, 0.0)
    vol_arena = max(longitud, 0.0) * max(ancho, 0.0) * d.ESPESOR_ARENA
    vol_relleno = max(longitud, 0.0) * max(ancho, 0.0) * espesor_relleno
    vol_transporte = max(vol_zanja - vol_arena - vol_relleno, 0.0)

    partidas = {
        nombre_tuberia: _importe(longitud, precio_tuberia),
        "Excavación mecánica": _importe(vol_zanja, _precio_excavacion(profundidad)),
        "Carga de tierras": _importe(vol_transporte, d.EXCAVACION["carga"]),
        "Transporte a vertedero": _importe(vol_transporte, d.EXCAVACION["transporte"]),
        "Canon vertido tierras": _importe(vol_transporte, d.EXCAVACION["canon_tierras"]),
        "Suministro de arena": _importe(vol_arena, d.EXCAVACION["arena"]),
        "Relleno de albero": _importe(vol_relleno, d.EXCAVACION["relleno"]),
    }
    subtotal = sum(partidas.values())
    auxiliares = {
        "ancho_zanja_m": ancho,
        "vol_zanja_m3": vol_zanja,
        "vol_arena_m3": vol_arena,
        "vol_relleno_m3": vol_relleno,
        "vol_transporte_m3": vol_transporte,
    }
    return subtotal, partidas, auxiliares

def _importe_calzada_desde_m2(item: Dict[str, Any], superficie_m2: float) -> float:
    if item["unidad"] == "m2":
    }