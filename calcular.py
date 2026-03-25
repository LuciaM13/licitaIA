from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from datos import PCT_BI, PCT_CONTROL_CALIDAD, PCT_GG, PCT_IVA


@dataclass
class ParametrosProyecto:
    metros_aba: float
    precios_aba: Dict[str, float]
    metros_aba2: float
    precios_aba2: Dict[str, float]
    metros_san: float
    precios_san: Dict[str, float]
    metros_ovoide: float
    precio_ovoide_m: float

    ancho_zanja_aba_m: float
    profundidad_aba_m: float
    ancho_zanja_san_m: float
    profundidad_san_m: float
    pct_exc_manual_aba: float
    pct_exc_manual_san: float
    pct_entibacion_aba: float
    pct_entibacion_san: float

    espesor_arena_aba_m: float
    espesor_arena_san_m: float
    espesor_relleno_aba_m: float
    espesor_relleno_san_m: float

    dem_bordillo_aba_m: float
    precio_dem_bordillo_aba_m: float
    dem_acerado_aba_m2: float
    precio_dem_acerado_aba_m2: float
    dem_calzada_aba_m2: float
    precio_dem_calzada_aba_m2: float
    espesor_dem_calzada_aba_m: float
    rep_acerado_aba_m2: float
    precio_rep_acerado_aba_m2: float
    rep_bordillo_aba_m: float
    precio_rep_bordillo_aba_m: float
    rep_adoquin_aba_m2: float
    precio_rep_adoquin_aba_m2: float
    rep_rodadura_aba_m2: float
    precio_rodadura_m3: float
    espesor_rodadura_m: float
    rep_base_pavimento_aba_m2: float
    precio_base_pavimento_m3: float
    espesor_base_pavimento_m: float
    rep_hormigon_aba_m2: float
    precio_hormigon_m3: float
    espesor_hormigon_m: float
    rep_base_granular_aba_m2: float
    precio_base_granular_m3: float
    espesor_base_granular_m: float

    dem_bordillo_san_m: float
    precio_dem_bordillo_san_m: float
    dem_acerado_san_m2: float
    precio_dem_acerado_san_m2: float
    dem_calzada_san_m2: float
    precio_dem_calzada_san_m2: float
    espesor_dem_calzada_san_m: float
    uds_dem_arqueta_imbornal: int
    precio_dem_arqueta_imbornal_ud: float
    uds_dem_imbornal_tuberia: int
    precio_dem_imbornal_tuberia_ud: float
    rep_acerado_san_m2: float
    precio_rep_acerado_san_m2: float
    rep_bordillo_san_m: float
    precio_rep_bordillo_san_m: float
    rep_adoquin_san_m2: float
    precio_rep_adoquin_m2: float
    rep_rodadura_san_m2: float
    rep_base_pavimento_san_m2: float
    rep_hormigon_san_m2: float
    rep_base_granular_san_m2: float

    precio_exc_mecanica_hasta_25_m3: float
    precio_exc_mecanica_mas_25_m3: float
    precio_exc_manual_hasta_25_m3: float
    precio_exc_manual_mas_25_m3: float
    precio_entibacion_hasta_25_m2: float
    precio_entibacion_mas_25_m2: float
    precio_carga_m3: float
    precio_transporte_m3: float
    precio_canon_tierras_m3: float
    precio_canon_mixto_m3: float
    precio_arena_m3: float
    precio_relleno_m3: float

    uds_acometidas_aba: int
    precio_acometida_aba_ud: float
    uds_acometidas_san: int
    precio_acometida_san_ud: float
    uds_pozos: int
    precio_pozo_ud: float
    uds_imbornales: int
    precio_imbornal_ud: float
    uds_marcos: int
    precio_marco_ud: float
    uds_tapas_pozo: int
    precio_tapa_pozo_ud: float
    uds_pates_pozo: int
    precio_pate_pozo_ud: float

    pct_servicios_afectados: float
    modo_ss: str
    importe_ss: float
    pct_ss: float
    modo_ga: str
    importe_ga: float
    pct_ga: float


def _normalizar_modo(valor: str) -> str:
    valor = (valor or "fijo").strip().lower()
    return valor if valor in {"fijo", "porcentaje"} else "fijo"


def _volumen_zanja(longitud_m: float, ancho_m: float, profundidad_m: float) -> float:
    return max(longitud_m, 0.0) * max(ancho_m, 0.0) * max(profundidad_m, 0.0)


def _area_entibacion(longitud_m: float, profundidad_m: float, porcentaje: float) -> float:
    longitud_entibada = max(longitud_m, 0.0) * max(porcentaje, 0.0)
    return 2.0 * longitud_entibada * max(profundidad_m, 0.0)


def _precio_excavacion(depth_m: float, manual: bool, p: ParametrosProyecto) -> float:
    if manual:
        return p.precio_exc_manual_hasta_25_m3 if depth_m <= 2.5 else p.precio_exc_manual_mas_25_m3
    return p.precio_exc_mecanica_hasta_25_m3 if depth_m <= 2.5 else p.precio_exc_mecanica_mas_25_m3


def _precio_entibacion(depth_m: float, p: ParametrosProyecto) -> float:
    return p.precio_entibacion_hasta_25_m2 if depth_m <= 2.5 else p.precio_entibacion_mas_25_m2


def calcular_presupuesto(parametros: ParametrosProyecto) -> dict:
    metros_aba_total = parametros.metros_aba + parametros.metros_aba2

    cap_tuberia_aba = parametros.metros_aba * parametros.precios_aba["tuberia_m"]
    cap_tuberia_aba2 = parametros.metros_aba2 * parametros.precios_aba2["tuberia_m"]
    cap_tuberia_san = parametros.metros_san * parametros.precios_san["tuberia_m"]
    cap_tuberia_ovoide = parametros.metros_ovoide * parametros.precio_ovoide_m

    vol_zanja_aba = _volumen_zanja(metros_aba_total, parametros.ancho_zanja_aba_m, parametros.profundidad_aba_m)
    vol_zanja_san = _volumen_zanja(parametros.metros_san, parametros.ancho_zanja_san_m, parametros.profundidad_san_m)

    vol_manual_aba = vol_zanja_aba * parametros.pct_exc_manual_aba
    vol_mecanica_aba = vol_zanja_aba - vol_manual_aba
    vol_manual_san = vol_zanja_san * parametros.pct_exc_manual_san
    vol_mecanica_san = vol_zanja_san - vol_manual_san

    cap_exc_mecanica_aba = vol_mecanica_aba * _precio_excavacion(parametros.profundidad_aba_m, False, parametros)
    cap_exc_manual_aba = vol_manual_aba * _precio_excavacion(parametros.profundidad_aba_m, True, parametros)
    cap_exc_mecanica_san = vol_mecanica_san * _precio_excavacion(parametros.profundidad_san_m, False, parametros)
    cap_exc_manual_san = vol_manual_san * _precio_excavacion(parametros.profundidad_san_m, True, parametros)

    area_ent_aba = _area_entibacion(metros_aba_total, parametros.profundidad_aba_m, parametros.pct_entibacion_aba)
    area_ent_san = _area_entibacion(parametros.metros_san, parametros.profundidad_san_m, parametros.pct_entibacion_san)
    cap_entibacion_aba = area_ent_aba * _precio_entibacion(parametros.profundidad_aba_m, parametros)
    cap_entibacion_san = area_ent_san * _precio_entibacion(parametros.profundidad_san_m, parametros)

    vol_arena_aba = metros_aba_total * parametros.ancho_zanja_aba_m * parametros.espesor_arena_aba_m
    vol_arena_san = parametros.metros_san * parametros.ancho_zanja_san_m * parametros.espesor_arena_san_m
    cap_arena_aba = vol_arena_aba * parametros.precio_arena_m3
    cap_arena_san = vol_arena_san * parametros.precio_arena_m3

    vol_relleno_aba = metros_aba_total * parametros.ancho_zanja_aba_m * parametros.espesor_relleno_aba_m
    vol_relleno_san = parametros.metros_san * parametros.ancho_zanja_san_m * parametros.espesor_relleno_san_m
    cap_relleno_aba = vol_relleno_aba * parametros.precio_relleno_m3
    cap_relleno_san = vol_relleno_san * parametros.precio_relleno_m3

    vol_total_tierras_aba = max(vol_zanja_aba - (vol_arena_aba + vol_relleno_aba), 0.0)
    vol_total_tierras_san = max(vol_zanja_san - (vol_arena_san + vol_relleno_san), 0.0)
    cap_carga_tierras_aba = vol_total_tierras_aba * parametros.precio_carga_m3
    cap_transporte_tierras_aba = vol_total_tierras_aba * parametros.precio_transporte_m3
    cap_canon_tierras_aba = vol_total_tierras_aba * parametros.precio_canon_tierras_m3
    cap_carga_tierras_san = vol_total_tierras_san * parametros.precio_carga_m3
    cap_transporte_tierras_san = vol_total_tierras_san * parametros.precio_transporte_m3
    cap_canon_tierras_san = vol_total_tierras_san * parametros.precio_canon_tierras_m3

    cap_dem_bordillo_aba = parametros.dem_bordillo_aba_m * parametros.precio_dem_bordillo_aba_m
    cap_dem_acerado_aba = parametros.dem_acerado_aba_m2 * parametros.precio_dem_acerado_aba_m2
    cap_dem_calzada_aba = parametros.dem_calzada_aba_m2 * parametros.precio_dem_calzada_aba_m2
    vol_rcd_calzada_aba = parametros.dem_calzada_aba_m2 * max(parametros.espesor_dem_calzada_aba_m, 0.0)
    cap_canon_mixto_aba = vol_rcd_calzada_aba * parametros.precio_canon_mixto_m3
    cap_rep_acerado_aba = parametros.rep_acerado_aba_m2 * parametros.precio_rep_acerado_aba_m2
    cap_rep_bordillo_aba = parametros.rep_bordillo_aba_m * parametros.precio_rep_bordillo_aba_m
    cap_rep_adoquin_aba = parametros.rep_adoquin_aba_m2 * parametros.precio_rep_adoquin_aba_m2
    cap_rep_rodadura_aba = parametros.rep_rodadura_aba_m2 * parametros.espesor_rodadura_m * parametros.precio_rodadura_m3
    cap_rep_base_pavimento_aba = parametros.rep_base_pavimento_aba_m2 * parametros.espesor_base_pavimento_m * parametros.precio_base_pavimento_m3
    cap_rep_hormigon_aba = parametros.rep_hormigon_aba_m2 * parametros.espesor_hormigon_m * parametros.precio_hormigon_m3
    cap_rep_base_granular_aba = parametros.rep_base_granular_aba_m2 * parametros.espesor_base_granular_m * parametros.precio_base_granular_m3

    cap_dem_bordillo_san = parametros.dem_bordillo_san_m * parametros.precio_dem_bordillo_san_m
    cap_dem_acerado_san = parametros.dem_acerado_san_m2 * parametros.precio_dem_acerado_san_m2
    cap_dem_calzada_san = parametros.dem_calzada_san_m2 * parametros.precio_dem_calzada_san_m2
    cap_dem_arqueta_imbornal = parametros.uds_dem_arqueta_imbornal * parametros.precio_dem_arqueta_imbornal_ud
    cap_dem_imbornal_tuberia = parametros.uds_dem_imbornal_tuberia * parametros.precio_dem_imbornal_tuberia_ud
    vol_rcd_calzada_san = parametros.dem_calzada_san_m2 * max(parametros.espesor_dem_calzada_san_m, 0.0)
    cap_canon_mixto_san = vol_rcd_calzada_san * parametros.precio_canon_mixto_m3
    cap_rep_acerado_san = parametros.rep_acerado_san_m2 * parametros.precio_rep_acerado_san_m2
    cap_rep_bordillo_san = parametros.rep_bordillo_san_m * parametros.precio_rep_bordillo_san_m
    cap_rep_adoquin_san = parametros.rep_adoquin_san_m2 * parametros.precio_rep_adoquin_m2
    cap_rep_rodadura_san = parametros.rep_rodadura_san_m2 * parametros.espesor_rodadura_m * parametros.precio_rodadura_m3
    cap_rep_base_pavimento_san = parametros.rep_base_pavimento_san_m2 * parametros.espesor_base_pavimento_m * parametros.precio_base_pavimento_m3
    cap_rep_hormigon_san = parametros.rep_hormigon_san_m2 * parametros.espesor_hormigon_m * parametros.precio_hormigon_m3
    cap_rep_base_granular_san = parametros.rep_base_granular_san_m2 * parametros.espesor_base_granular_m * parametros.precio_base_granular_m3

    cap_acometidas_aba = parametros.uds_acometidas_aba * parametros.precio_acometida_aba_ud
    cap_acometidas_san = parametros.uds_acometidas_san * parametros.precio_acometida_san_ud
    cap_pozos = parametros.uds_pozos * parametros.precio_pozo_ud
    cap_imbornales = parametros.uds_imbornales * parametros.precio_imbornal_ud
    cap_marcos = parametros.uds_marcos * parametros.precio_marco_ud
    cap_tapas_pozo = parametros.uds_tapas_pozo * parametros.precio_tapa_pozo_ud
    cap_pates_pozo = parametros.uds_pates_pozo * parametros.precio_pate_pozo_ud

    capitulo_01 = sum([
        cap_tuberia_aba, cap_tuberia_aba2,
        cap_exc_mecanica_aba, cap_exc_manual_aba, cap_entibacion_aba,
        cap_carga_tierras_aba, cap_transporte_tierras_aba, cap_canon_tierras_aba,
        cap_arena_aba, cap_relleno_aba,
    ])
    capitulo_02 = sum([
        cap_tuberia_san, cap_tuberia_ovoide,
        cap_exc_mecanica_san, cap_exc_manual_san, cap_entibacion_san,
        cap_carga_tierras_san, cap_transporte_tierras_san, cap_canon_tierras_san,
        cap_arena_san, cap_relleno_san,
        cap_pozos, cap_imbornales, cap_marcos, cap_tapas_pozo, cap_pates_pozo,
    ])
    capitulo_03 = sum([
        cap_dem_bordillo_aba, cap_dem_acerado_aba, cap_dem_calzada_aba, cap_canon_mixto_aba,
        cap_rep_acerado_aba, cap_rep_bordillo_aba, cap_rep_adoquin_aba,
        cap_rep_rodadura_aba, cap_rep_base_pavimento_aba, cap_rep_hormigon_aba, cap_rep_base_granular_aba,
    ])
    capitulo_04 = sum([
        cap_dem_bordillo_san, cap_dem_acerado_san, cap_dem_calzada_san,
        cap_dem_arqueta_imbornal, cap_dem_imbornal_tuberia, cap_canon_mixto_san,
        cap_rep_acerado_san, cap_rep_bordillo_san, cap_rep_adoquin_san,
        cap_rep_rodadura_san, cap_rep_base_pavimento_san, cap_rep_hormigon_san, cap_rep_base_granular_san,
    ])
    capitulo_05 = cap_acometidas_aba
    capitulo_06 = cap_acometidas_san

    parcial_directo = capitulo_01 + capitulo_02 + capitulo_03 + capitulo_04 + capitulo_05 + capitulo_06
    cap_servicios_afectados = parcial_directo * parametros.pct_servicios_afectados

    modo_ss = _normalizar_modo(parametros.modo_ss)
    modo_ga = _normalizar_modo(parametros.modo_ga)
    capitulo_07 = parametros.importe_ss if modo_ss == "fijo" else parcial_directo * parametros.pct_ss
    capitulo_08 = parametros.importe_ga if modo_ga == "fijo" else parcial_directo * parametros.pct_ga

    pem = parcial_directo + cap_servicios_afectados + capitulo_07 + capitulo_08
    gastos_generales = pem * PCT_GG
    beneficio_industrial = pem * PCT_BI
    pbl_sin_iva = pem + gastos_generales + beneficio_industrial
    iva = pbl_sin_iva * PCT_IVA
    total = pbl_sin_iva + iva

    texto_word = "\n".join([
        f"Capítulo 01 OBRA CIVIL ABASTECIMIENTO: {capitulo_01:,.2f} €",
        f"Capítulo 02 OBRA CIVIL SANEAMIENTO: {capitulo_02:,.2f} €",
        f"Capítulo 03 PAVIMENTACIÓN ABASTECIMIENTO: {capitulo_03:,.2f} €",
        f"Capítulo 04 PAVIMENTACIÓN SANEAMIENTO: {capitulo_04:,.2f} €",
        f"Capítulo 05 ACOMETIDAS ABASTECIMIENTO: {capitulo_05:,.2f} €",
        f"Capítulo 06 ACOMETIDAS SANEAMIENTO: {capitulo_06:,.2f} €",
        f"Capítulo 07 SEGURIDAD Y SALUD: {capitulo_07:,.2f} €",
        f"Capítulo 08 GESTIÓN AMBIENTAL: {capitulo_08:,.2f} €",
        f"Presupuesto de Ejecución Material: {pem:,.2f} €",
        f"13 % Gastos Generales: {gastos_generales:,.2f} €",
        f"6 % Beneficio Industrial: {beneficio_industrial:,.2f} €",
        f"Presupuesto Base de Licitación excluido IVA: {pbl_sin_iva:,.2f} €",
        f"21 % IVA: {iva:,.2f} €",
        f"Presupuesto Base de Licitación incluido IVA: {total:,.2f} €",
    ])

    return {
        "capitulo_01": capitulo_01,
        "capitulo_02": capitulo_02,
        "capitulo_03": capitulo_03,
        "capitulo_04": capitulo_04,
        "capitulo_05": capitulo_05,
        "capitulo_06": capitulo_06,
        "capitulo_07": capitulo_07,
        "capitulo_08": capitulo_08,
        "parcial_directo": parcial_directo,
        "servicios_afectados": cap_servicios_afectados,
        "pem": pem,
        "control_calidad_referencia": pem * PCT_CONTROL_CALIDAD,
        "gastos_generales": gastos_generales,
        "beneficio_industrial": beneficio_industrial,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
        "texto_word": texto_word,
        "vol_zanja_aba": vol_zanja_aba,
        "vol_zanja_san": vol_zanja_san,
        "vol_total_tierras": vol_total_tierras_aba + vol_total_tierras_san,
        "vol_arena_total": vol_arena_aba + vol_arena_san,
        "vol_relleno_total": vol_relleno_aba + vol_relleno_san,
        "vol_rcd_calzada": vol_rcd_calzada_aba + vol_rcd_calzada_san,
        "area_entibacion_aba": area_ent_aba,
        "area_entibacion_san": area_ent_san,
    }
