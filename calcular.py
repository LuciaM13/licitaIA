
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from datos import PCT_GG, PCT_BI, PCT_IVA, EXCAVACION, IMPORTE_GA_DEFAULT, IMPORTE_SS_DEFAULT

@dataclass
class ParametrosProyecto:
    cap01: Dict[str, float]
    san_item: Dict[str, Any]
    metros_san: float
    cap02: Dict[str, float]
    pozo_item: Dict[str, Any]
    uds_pozos: int
    imbornal_item: Dict[str, Any]
    uds_imbornales: int
    marco_item: Dict[str, Any]
    uds_marcos: int
    uds_tapas: int
    uds_pates: int
    uds_dem_pozo: int
    dem_pozo_item: Dict[str, Any]
    cap03: Dict[str, Any]
    cap04: Dict[str, Any]
    acom_aba_item: Dict[str, Any]
    uds_acom_aba: int
    acom_san_item: Dict[str, Any]
    uds_acom_san: int
    importe_ss: float
    importe_ga: float

def _importe(cantidad: float, precio: float) -> float:
    return max(float(cantidad or 0), 0.0) * max(float(precio or 0), 0.0)

def _calc_exc(cap: Dict[str, float]) -> Dict[str, float]:
    return {EXCAVACION[k]["label"]: _importe(cap.get(k, 0), EXCAVACION[k]["precio"]) for k in EXCAVACION}

def _calc_pav(cap: Dict[str, Any]) -> Dict[str, float]:
    out = {}
    if cap["dem_bordillo_qty"]:
        out[cap["dem_bordillo_item"]["label"]] = _importe(cap["dem_bordillo_qty"], cap["dem_bordillo_item"]["precio"])
    if cap["dem_acerado_qty"]:
        out[cap["dem_acerado_item"]["label"]] = _importe(cap["dem_acerado_qty"], cap["dem_acerado_item"]["precio"])
    if cap["dem_calzada_qty"]:
        out[cap["dem_calzada_item"]["label"]] = _importe(cap["dem_calzada_qty"], cap["dem_calzada_item"]["precio"])
    if cap["dem_arqueta_qty"]:
        out["Demolición arqueta de imbornal"] = _importe(cap["dem_arqueta_qty"], cap["dem_arqueta_precio"])
    if cap["dem_imb_tub_qty"]:
        out["Demolición imbornal y tubería"] = _importe(cap["dem_imb_tub_qty"], cap["dem_imb_tub_precio"])
    if cap["canon_mixto_qty"]:
        out["Canon vertido mixto"] = _importe(cap["canon_mixto_qty"], cap["canon_mixto_precio"])
    if cap["rep_bordillo_qty"]:
        out[cap["rep_bordillo_item"]["label"]] = _importe(cap["rep_bordillo_qty"], cap["rep_bordillo_item"]["precio"])
    if cap["rep_acerado_qty"]:
        out[cap["rep_acerado_item"]["label"]] = _importe(cap["rep_acerado_qty"], cap["rep_acerado_item"]["precio"])
    if cap["adoquin_qty"]:
        out["Reposición adoquín"] = _importe(cap["adoquin_qty"], cap["adoquin_precio"])
    if cap["rodadura_qty"]:
        out["Capa de rodadura"] = _importe(cap["rodadura_qty"], cap["rodadura_precio"])
    if cap["base_pav_qty"]:
        out["Base de pavimento"] = _importe(cap["base_pav_qty"], cap["base_pav_precio"])
    if cap["hormigon_qty"]:
        out["Hormigón"] = _importe(cap["hormigon_qty"], cap["hormigon_precio"])
    if cap["base_gran_qty"]:
        out["Base granular"] = _importe(cap["base_gran_qty"], cap["base_gran_precio"])
    return out

def calcular_presupuesto(p: ParametrosProyecto) -> dict:
    cap1_partidas = _calc_exc(p.cap01)
    cap1 = sum(cap1_partidas.values())

    cap2_partidas = {}
    if p.metros_san:
        cap2_partidas[p.san_item["label"]] = _importe(p.metros_san, p.san_item["precio"])
    cap2_partidas.update(_calc_exc(p.cap02))
    if p.uds_pozos:
        cap2_partidas[p.pozo_item["label"]] = _importe(p.uds_pozos, p.pozo_item["precio"])
    if p.uds_imbornales:
        cap2_partidas[p.imbornal_item["label"]] = _importe(p.uds_imbornales, p.imbornal_item["precio"])
    if p.uds_marcos:
        cap2_partidas[p.marco_item["label"]] = _importe(p.uds_marcos, p.marco_item["precio"])
    if p.uds_tapas:
        cap2_partidas["Tapa de pozo de registro"] = _importe(p.uds_tapas, 160.37)
    if p.uds_pates:
        cap2_partidas["Pate para pozos"] = _importe(p.uds_pates, 1.94)
    if p.uds_dem_pozo:
        cap2_partidas[p.dem_pozo_item["label"]] = _importe(p.uds_dem_pozo, p.dem_pozo_item["precio"])
    cap2 = sum(cap2_partidas.values())

    cap3_partidas = _calc_pav(p.cap03)
    cap3 = sum(cap3_partidas.values())
    cap4_partidas = _calc_pav(p.cap04)
    cap4 = sum(cap4_partidas.values())

    cap5_partidas = {}
    if p.uds_acom_aba:
        cap5_partidas[p.acom_aba_item["label"]] = _importe(p.uds_acom_aba, p.acom_aba_item["precio"])
    cap5 = sum(cap5_partidas.values())
    cap6_partidas = {}
    if p.uds_acom_san:
        cap6_partidas[p.acom_san_item["label"]] = _importe(p.uds_acom_san, p.acom_san_item["precio"])
    cap6 = sum(cap6_partidas.values())

    cap7 = max(float(p.importe_ss or IMPORTE_SS_DEFAULT), 0.0)
    cap8 = max(float(p.importe_ga or IMPORTE_GA_DEFAULT), 0.0)

    pem = cap1 + cap2 + cap3 + cap4 + cap5 + cap6 + cap7 + cap8
    gg = pem * PCT_GG
    bi = pem * PCT_BI
    pbl_sin_iva = pem + gg + bi
    iva = pbl_sin_iva * PCT_IVA
    total = pbl_sin_iva + iva

    capitulos = {
        "01 OBRA CIVIL ABASTECIMIENTO": {"subtotal": cap1, "partidas": cap1_partidas},
        "02 OBRA CIVIL SANEAMIENTO": {"subtotal": cap2, "partidas": cap2_partidas},
        "03 PAVIMENTACIÓN ABASTECIMIENTO": {"subtotal": cap3, "partidas": cap3_partidas},
        "04 PAVIMENTACIÓN SANEAMIENTO": {"subtotal": cap4, "partidas": cap4_partidas},
        "05 ACOMETIDAS ABASTECIMIENTO": {"subtotal": cap5, "partidas": cap5_partidas},
        "06 ACOMETIDAS SANEAMIENTO": {"subtotal": cap6, "partidas": cap6_partidas},
        "07 SEGURIDAD Y SALUD": {"subtotal": cap7, "partidas": {"Seguridad y Salud": cap7}},
        "08 GESTIÓN AMBIENTAL": {"subtotal": cap8, "partidas": {"Gestión ambiental": cap8}},
    }

    fmt = lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    lines = [f"{k}: {fmt(v['subtotal'])}" for k, v in capitulos.items()]
    lines += [
        f"Presupuesto de Ejecución Material: {fmt(pem)}",
        f"13 % Gastos Generales: {fmt(gg)}",
        f"6 % Beneficio Industrial: {fmt(bi)}",
        f"Presupuesto Base de Licitación excluido IVA: {fmt(pbl_sin_iva)}",
        f"21 % IVA: {fmt(iva)}",
        f"Presupuesto Base de Licitación incluido IVA: {fmt(total)}",
    ]
    return {"capitulos": capitulos, "pem": pem, "gg": gg, "bi": bi, "pbl_sin_iva": pbl_sin_iva, "iva": iva, "total": total, "texto_word": "\n".join(lines)}
