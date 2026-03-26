
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
        "ancho_zanja_m": round(ancho, 3),
        "vol_zanja_m3": round(vol_zanja, 3),
        "vol_arena_m3": round(vol_arena, 3),
        "vol_relleno_m3": round(vol_relleno, 3),
        "vol_transporte_m3": round(vol_transporte, 3),
    }
    return subtotal, partidas, auxiliares

def _importe_calzada_desde_m2(item: Dict[str, Any], superficie_m2: float) -> float:
    if item["unidad"] == "m2":
        return _importe(superficie_m2, item["precio"])
    espesor = d.ESPESORES_CALZADA.get(item["label"], 0.15)
    return _importe(superficie_m2 * espesor, item["precio"])

def calcular_presupuesto(p: ParametrosProyecto) -> Dict[str, Any]:
    cap01, cap01_partidas, aux_aba = _capitulo_obra_civil_red(
        p.aba_longitud_m, p.aba_profundidad_m, _ancho_zanja_aba(p.aba_item["diametro_mm"]),
        p.aba_item["precio_m"], d.ESPESOR_RELLENO_ABA, p.aba_item["label"]
    )
    cap02, cap02_partidas, aux_san = _capitulo_obra_civil_red(
        p.san_longitud_m, p.san_profundidad_m, _ancho_zanja_san(p.san_item["diametro_mm"]),
        p.san_item["precio_m"], d.ESPESOR_RELLENO_SAN, p.san_item["label"]
    )
    cap03_partidas = {
        p.pav_aba_acerado_item["label"]: _importe(p.pav_aba_acerado_m2, p.pav_aba_acerado_item["precio_m2"]),
        p.pav_aba_bordillo_item["label"]: _importe(p.pav_aba_bordillo_m, p.pav_aba_bordillo_item["precio_m"]),
    }
    cap03 = sum(cap03_partidas.values())
    cap04_partidas = {
        p.pav_san_calzada_item["label"]: _importe_calzada_desde_m2(p.pav_san_calzada_item, p.pav_san_calzada_m2),
        p.pav_san_acera_item["label"]: _importe(p.pav_san_acera_m2, p.pav_san_acera_item["precio_m2"]),
    }
    cap04 = sum(cap04_partidas.values())
    cap05_partidas = {"Acometidas ABA": _importe(p.acometidas_aba_n, d.PRECIO_ACOMETIDA_ABA)}
    cap05 = sum(cap05_partidas.values())
    cap06_partidas = {"Acometidas SAN": _importe(p.acometidas_san_n, d.PRECIO_ACOMETIDA_SAN)}
    cap06 = sum(cap06_partidas.values())
    subtotal_1_6 = cap01 + cap02 + cap03 + cap04 + cap05 + cap06
    cap07 = subtotal_1_6 * max(float(p.pct_seguridad or 0), 0.0)
    cap08 = subtotal_1_6 * max(float(p.pct_gestion or 0), 0.0)
    pem = subtotal_1_6 + cap07 + cap08
    gg = pem * d.PCT_GG
    bi = pem * d.PCT_BI
    pbl_sin_iva = pem + gg + bi
    iva = pbl_sin_iva * d.PCT_IVA
    total = pbl_sin_iva + iva
    capitulos = {
        "01 OBRA CIVIL ABASTECIMIENTO": {"subtotal": cap01, "partidas": cap01_partidas},
        "02 OBRA CIVIL SANEAMIENTO": {"subtotal": cap02, "partidas": cap02_partidas},
        "03 PAVIMENTACIÓN ABASTECIMIENTO": {"subtotal": cap03, "partidas": cap03_partidas},
        "04 PAVIMENTACIÓN SANEAMIENTO": {"subtotal": cap04, "partidas": cap04_partidas},
        "05 ACOMETIDAS ABASTECIMIENTO": {"subtotal": cap05, "partidas": cap05_partidas},
        "06 ACOMETIDAS SANEAMIENTO": {"subtotal": cap06, "partidas": cap06_partidas},
        "07 SEGURIDAD Y SALUD": {"subtotal": cap07, "partidas": {"Seguridad y Salud": cap07}},
        "08 GESTIÓN AMBIENTAL": {"subtotal": cap08, "partidas": {"Gestión ambiental": cap08}},
    }
    fmt = lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    texto_word = "\n".join([
        *[f"{k}: {fmt(v['subtotal'])}" for k, v in capitulos.items()],
        f"Presupuesto de Ejecución Material: {fmt(pem)}",
        f"13 % Gastos Generales: {fmt(gg)}",
        f"6 % Beneficio Industrial: {fmt(bi)}",
        f"Presupuesto Base de Licitación excluido IVA: {fmt(pbl_sin_iva)}",
        f"21 % IVA: {fmt(iva)}",
        f"Presupuesto Base de Licitación incluido IVA: {fmt(total)}",
    ])
    return {
        "capitulos": capitulos,
        "pem": pem,
        "gg": gg,
        "bi": bi,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
        "texto_word": texto_word,
        "auxiliares": {"aba": aux_aba, "san": aux_san},
    }
