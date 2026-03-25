from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from datos import PCT_BI, PCT_GG, PCT_IVA


@dataclass
class ParametrosProyecto:
    # Capítulo 01 · Obra civil ABA (solo familias presentes en la base)
    exc_mec_aba_hasta: float
    exc_mec_aba_mas: float
    exc_man_aba_hasta: float
    exc_man_aba_mas: float
    ent_aba_hasta: float
    ent_aba_mas: float
    carga_aba: float
    transporte_aba: float
    canon_tierras_aba: float
    arena_aba: float
    relleno_aba: float

    # Capítulo 02 · Obra civil SAN
    tipo_san: Dict[str, float]
    metros_san: float
    tipo_ovoide: Dict[str, float]
    metros_ovoide: float
    exc_mec_san_hasta: float
    exc_mec_san_mas: float
    exc_man_san_hasta: float
    exc_man_san_mas: float
    ent_san_hasta: float
    ent_san_mas: float
    carga_san: float
    transporte_san: float
    canon_tierras_san: float
    canon_mixto_san: float
    arena_san: float
    relleno_san: float
    tipo_pozo: Dict[str, float]
    uds_pozos: int
    tipo_imbornal: Dict[str, float]
    uds_imbornales: int
    tipo_marco: Dict[str, float]
    uds_marcos: int
    tipo_tapa: Dict[str, float]
    uds_tapas: int
    tipo_pate: Dict[str, float]
    uds_pates: int
    uds_dem_pozo: int
    tipo_dem_pozo: Dict[str, float]

    # Capítulos 03 y 04 · Pavimentación ABA/SAN
    pav_aba: Dict[str, float]
    pav_san: Dict[str, float]

    # Capítulos 05 y 06 · Acometidas
    tipo_acom_aba: Dict[str, float]
    uds_acom_aba: int
    tipo_acom_san: Dict[str, float]
    uds_acom_san: int

    # Capítulos 07 y 08
    importe_ss: float
    importe_ga: float


def _importe(cantidad: float, precio: float) -> float:
    return max(cantidad, 0.0) * max(precio, 0.0)


def calcular_capitulo_pav(p: Dict[str, float]) -> Dict[str, float]:
    partidas = {
        "Demolición bordillo": _importe(p["dem_bordillo_m"], p["precio_dem_bordillo"]),
        "Demolición acerado": _importe(p["dem_acerado_m2"], p["precio_dem_acerado"]),
        "Demolición calzada": _importe(p["dem_calzada_m2"], p["precio_dem_calzada"]),
        "Demolición arqueta de imbornal": _importe(p["uds_dem_arqueta_imbornal"], p["precio_dem_arqueta_imbornal"]),
        "Demolición imbornal y tubería": _importe(p["uds_dem_imbornal_tuberia"], p["precio_dem_imbornal_tuberia"]),
        "Reposición bordillo": _importe(p["rep_bordillo_m"], p["precio_rep_bordillo"]),
        "Reposición acerado": _importe(p["rep_acerado_m2"], p["precio_rep_acerado"]),
        "Reposición adoquín": _importe(p["rep_adoquin_m2"], p["precio_rep_adoquin"]),
        "Capa de rodadura": _importe(p["rep_rodadura_m3"], p["precio_rep_rodadura"]),
        "Base de pavimento": _importe(p["rep_base_pavimento_m3"], p["precio_rep_base_pavimento"]),
        "Hormigón": _importe(p["rep_hormigon_m3"], p["precio_rep_hormigon"]),
        "Base granular": _importe(p["rep_base_granular_m3"], p["precio_rep_base_granular"]),
        "Canon vertido mixto": _importe(p["canon_mixto_m3"], p["precio_canon_mixto"]),
    }
    return {"partidas": partidas, "subtotal": sum(partidas.values())}


def calcular_presupuesto(p: ParametrosProyecto) -> dict:
    cap1_partidas = {
        "Excavación mecánica ≤ 2,5 m": _importe(p.exc_mec_aba_hasta, 3.07),
        "Excavación mecánica > 2,5 m": _importe(p.exc_mec_aba_mas, 5.00),
        "Excavación manual ≤ 2,5 m": _importe(p.exc_man_aba_hasta, 11.17),
        "Excavación manual > 2,5 m": _importe(p.exc_man_aba_mas, 13.99),
        "Entibación blindada ≤ 2,5 m": _importe(p.ent_aba_hasta, 4.27),
        "Entibación blindada > 2,5 m": _importe(p.ent_aba_mas, 22.73),
        "Carga de tierras": _importe(p.carga_aba, 0.34),
        "Transporte a vertedero": _importe(p.transporte_aba, 5.29),
        "Canon vertido tierras": _importe(p.canon_tierras_aba, 1.60),
        "Suministro de arena": _importe(p.arena_aba, 22.18),
        "Relleno de albero": _importe(p.relleno_aba, 19.39),
    }
    cap1 = sum(cap1_partidas.values())

    cap2_partidas = {
        f"{p.tipo_san['label']}": _importe(p.metros_san, p.tipo_san["precio"]),
        f"{p.tipo_ovoide['label']}": _importe(p.metros_ovoide, p.tipo_ovoide["precio"]),
        "Excavación mecánica ≤ 2,5 m": _importe(p.exc_mec_san_hasta, 3.07),
        "Excavación mecánica > 2,5 m": _importe(p.exc_mec_san_mas, 5.00),
        "Excavación manual ≤ 2,5 m": _importe(p.exc_man_san_hasta, 11.17),
        "Excavación manual > 2,5 m": _importe(p.exc_man_san_mas, 13.99),
        "Entibación blindada ≤ 2,5 m": _importe(p.ent_san_hasta, 4.27),
        "Entibación blindada > 2,5 m": _importe(p.ent_san_mas, 22.73),
        "Carga de tierras": _importe(p.carga_san, 0.34),
        "Transporte a vertedero": _importe(p.transporte_san, 5.29),
        "Canon vertido tierras": _importe(p.canon_tierras_san, 1.60),
        "Canon vertido mixto": _importe(p.canon_mixto_san, 13.22),
        "Suministro de arena": _importe(p.arena_san, 22.18),
        "Relleno de albero": _importe(p.relleno_san, 19.39),
        p.tipo_pozo["label"]: _importe(p.uds_pozos, p.tipo_pozo["precio"]),
        p.tipo_imbornal["label"]: _importe(p.uds_imbornales, p.tipo_imbornal["precio"]),
        p.tipo_marco["label"]: _importe(p.uds_marcos, p.tipo_marco["precio"]),
        p.tipo_tapa["label"]: _importe(p.uds_tapas, p.tipo_tapa["precio"]),
        p.tipo_pate["label"]: _importe(p.uds_pates, p.tipo_pate["precio"]),
        p.tipo_dem_pozo["label"]: _importe(p.uds_dem_pozo, p.tipo_dem_pozo["precio"]),
    }
    cap2 = sum(cap2_partidas.values())

    pav_aba = calcular_capitulo_pav(p.pav_aba)
    cap3_partidas = pav_aba["partidas"]
    cap3 = pav_aba["subtotal"]

    pav_san = calcular_capitulo_pav(p.pav_san)
    cap4_partidas = pav_san["partidas"]
    cap4 = pav_san["subtotal"]

    cap5_partidas = {p.tipo_acom_aba["label"]: _importe(p.uds_acom_aba, p.tipo_acom_aba["precio"])}
    cap5 = sum(cap5_partidas.values())
    cap6_partidas = {p.tipo_acom_san["label"]: _importe(p.uds_acom_san, p.tipo_acom_san["precio"])}
    cap6 = sum(cap6_partidas.values())

    cap7 = max(p.importe_ss, 0.0)
    cap8 = max(p.importe_ga, 0.0)

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

    word_lines = []
    for nombre, info in capitulos.items():
        word_lines.append(f"{nombre}: {info['subtotal']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    word_lines += [
        f"Presupuesto de Ejecución Material: {pem:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
        f"13 % Gastos Generales: {gg:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
        f"6 % Beneficio Industrial: {bi:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
        f"Presupuesto Base de Licitación excluido IVA: {pbl_sin_iva:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
        f"21 % IVA: {iva:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
        f"Presupuesto Base de Licitación incluido IVA: {total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
    ]

    return {
        "capitulos": capitulos,
        "pem": pem,
        "gg": gg,
        "bi": bi,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
        "texto_word": "\n".join(word_lines),
    }
