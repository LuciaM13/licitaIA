from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from datos import PCT_BI, PCT_CONTROL_CALIDAD, PCT_GG, PCT_IVA

@dataclass
class ParametrosProyecto:
    # Cap 01: solo partidas con precio en Excel que el usuario asigna a ABA
    qty_exc_mecanica_aba: float
    precio_exc_mecanica_aba: float
    qty_exc_manual_aba: float
    precio_exc_manual_aba: float
    qty_entibacion_aba: float
    precio_entibacion_aba: float
    qty_carga_tierras_aba: float
    precio_carga_tierras_aba: float
    qty_transporte_tierras_aba: float
    precio_transporte_tierras_aba: float
    qty_canon_tierras_aba: float
    precio_canon_tierras_aba: float
    qty_arena_aba: float
    precio_arena_aba: float
    qty_relleno_aba: float
    precio_relleno_aba: float

    # Cap 02: saneamiento
    qty_tuberia_san: float
    precio_tuberia_san: float
    qty_ovoide: float
    precio_ovoide: float
    qty_exc_mecanica_san: float
    precio_exc_mecanica_san: float
    qty_exc_manual_san: float
    precio_exc_manual_san: float
    qty_entibacion_san: float
    precio_entibacion_san: float
    qty_carga_tierras_san: float
    precio_carga_tierras_san: float
    qty_transporte_tierras_san: float
    precio_transporte_tierras_san: float
    qty_canon_tierras_san: float
    precio_canon_tierras_san: float
    qty_arena_san: float
    precio_arena_san: float
    qty_relleno_san: float
    precio_relleno_san: float
    qty_pozos: int
    precio_pozo: float
    qty_imbornales: int
    precio_imbornal: float
    qty_marcos: int
    precio_marco: float
    qty_tapas_pozo: int
    precio_tapa_pozo: float
    qty_pates_pozo: int
    precio_pate_pozo: float

    # Cap 03: pavimentación ABA
    qty_dem_bordillo_aba: float
    precio_dem_bordillo_aba: float
    qty_dem_acerado_aba: float
    precio_dem_acerado_aba: float
    qty_dem_calzada_aba: float
    precio_dem_calzada_aba: float
    qty_canon_mixto_aba: float
    precio_canon_mixto_aba: float
    qty_rep_acerado_aba: float
    precio_rep_acerado_aba: float
    qty_rep_bordillo_aba: float
    precio_rep_bordillo_aba: float
    qty_rep_adoquin_aba: float
    precio_rep_adoquin_aba: float
    qty_rep_rodadura_aba: float
    precio_rep_rodadura_aba: float
    qty_rep_base_pavimento_aba: float
    precio_rep_base_pavimento_aba: float
    qty_rep_hormigon_aba: float
    precio_rep_hormigon_aba: float
    qty_rep_base_granular_aba: float
    precio_rep_base_granular_aba: float

    # Cap 04: pavimentación SAN
    qty_dem_bordillo_san: float
    precio_dem_bordillo_san: float
    qty_dem_acerado_san: float
    precio_dem_acerado_san: float
    qty_dem_calzada_san: float
    precio_dem_calzada_san: float
    qty_dem_arqueta_imbornal: int
    precio_dem_arqueta_imbornal: float
    qty_dem_imbornal_tuberia: int
    precio_dem_imbornal_tuberia: float
    qty_canon_mixto_san: float
    precio_canon_mixto_san: float
    qty_rep_acerado_san: float
    precio_rep_acerado_san: float
    qty_rep_bordillo_san: float
    precio_rep_bordillo_san: float
    qty_rep_adoquin_san: float
    precio_rep_adoquin_san: float
    qty_rep_rodadura_san: float
    precio_rep_rodadura_san: float
    qty_rep_base_pavimento_san: float
    precio_rep_base_pavimento_san: float
    qty_rep_hormigon_san: float
    precio_rep_hormigon_san: float
    qty_rep_base_granular_san: float
    precio_rep_base_granular_san: float

    # Cap 05 y 06: acometidas
    qty_acometidas_aba: int
    precio_acometidas_aba: float
    qty_acometidas_san: int
    precio_acometidas_san: float

    # SS, GA y afecciones
    pct_servicios_afectados: float
    importe_ss: float
    importe_ga: float


def _imp(qty: float | int, price: float) -> float:
    return float(qty) * float(price)


def calcular_presupuesto(p: ParametrosProyecto) -> dict:
    capitulo_01 = sum([
        _imp(p.qty_exc_mecanica_aba, p.precio_exc_mecanica_aba),
        _imp(p.qty_exc_manual_aba, p.precio_exc_manual_aba),
        _imp(p.qty_entibacion_aba, p.precio_entibacion_aba),
        _imp(p.qty_carga_tierras_aba, p.precio_carga_tierras_aba),
        _imp(p.qty_transporte_tierras_aba, p.precio_transporte_tierras_aba),
        _imp(p.qty_canon_tierras_aba, p.precio_canon_tierras_aba),
        _imp(p.qty_arena_aba, p.precio_arena_aba),
        _imp(p.qty_relleno_aba, p.precio_relleno_aba),
    ])
    capitulo_02 = sum([
        _imp(p.qty_tuberia_san, p.precio_tuberia_san),
        _imp(p.qty_ovoide, p.precio_ovoide),
        _imp(p.qty_exc_mecanica_san, p.precio_exc_mecanica_san),
        _imp(p.qty_exc_manual_san, p.precio_exc_manual_san),
        _imp(p.qty_entibacion_san, p.precio_entibacion_san),
        _imp(p.qty_carga_tierras_san, p.precio_carga_tierras_san),
        _imp(p.qty_transporte_tierras_san, p.precio_transporte_tierras_san),
        _imp(p.qty_canon_tierras_san, p.precio_canon_tierras_san),
        _imp(p.qty_arena_san, p.precio_arena_san),
        _imp(p.qty_relleno_san, p.precio_relleno_san),
        _imp(p.qty_pozos, p.precio_pozo),
        _imp(p.qty_imbornales, p.precio_imbornal),
        _imp(p.qty_marcos, p.precio_marco),
        _imp(p.qty_tapas_pozo, p.precio_tapa_pozo),
        _imp(p.qty_pates_pozo, p.precio_pate_pozo),
    ])
    capitulo_03 = sum([
        _imp(p.qty_dem_bordillo_aba, p.precio_dem_bordillo_aba),
        _imp(p.qty_dem_acerado_aba, p.precio_dem_acerado_aba),
        _imp(p.qty_dem_calzada_aba, p.precio_dem_calzada_aba),
        _imp(p.qty_canon_mixto_aba, p.precio_canon_mixto_aba),
        _imp(p.qty_rep_acerado_aba, p.precio_rep_acerado_aba),
        _imp(p.qty_rep_bordillo_aba, p.precio_rep_bordillo_aba),
        _imp(p.qty_rep_adoquin_aba, p.precio_rep_adoquin_aba),
        _imp(p.qty_rep_rodadura_aba, p.precio_rep_rodadura_aba),
        _imp(p.qty_rep_base_pavimento_aba, p.precio_rep_base_pavimento_aba),
        _imp(p.qty_rep_hormigon_aba, p.precio_rep_hormigon_aba),
        _imp(p.qty_rep_base_granular_aba, p.precio_rep_base_granular_aba),
    ])
    capitulo_04 = sum([
        _imp(p.qty_dem_bordillo_san, p.precio_dem_bordillo_san),
        _imp(p.qty_dem_acerado_san, p.precio_dem_acerado_san),
        _imp(p.qty_dem_calzada_san, p.precio_dem_calzada_san),
        _imp(p.qty_dem_arqueta_imbornal, p.precio_dem_arqueta_imbornal),
        _imp(p.qty_dem_imbornal_tuberia, p.precio_dem_imbornal_tuberia),
        _imp(p.qty_canon_mixto_san, p.precio_canon_mixto_san),
        _imp(p.qty_rep_acerado_san, p.precio_rep_acerado_san),
        _imp(p.qty_rep_bordillo_san, p.precio_rep_bordillo_san),
        _imp(p.qty_rep_adoquin_san, p.precio_rep_adoquin_san),
        _imp(p.qty_rep_rodadura_san, p.precio_rep_rodadura_san),
        _imp(p.qty_rep_base_pavimento_san, p.precio_rep_base_pavimento_san),
        _imp(p.qty_rep_hormigon_san, p.precio_rep_hormigon_san),
        _imp(p.qty_rep_base_granular_san, p.precio_rep_base_granular_san),
    ])
    capitulo_05 = _imp(p.qty_acometidas_aba, p.precio_acometidas_aba)
    capitulo_06 = _imp(p.qty_acometidas_san, p.precio_acometidas_san)

    parcial_directo = capitulo_01 + capitulo_02 + capitulo_03 + capitulo_04 + capitulo_05 + capitulo_06
    servicios_afectados = parcial_directo * p.pct_servicios_afectados
    capitulo_07 = p.importe_ss
    capitulo_08 = p.importe_ga
    pem = parcial_directo + servicios_afectados + capitulo_07 + capitulo_08
    gg = pem * PCT_GG
    bi = pem * PCT_BI
    pbl_sin_iva = pem + gg + bi
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
        f"13 % Gastos Generales: {gg:,.2f} €",
        f"6 % Beneficio Industrial: {bi:,.2f} €",
        f"Presupuesto Base de Licitación excluido IVA: {pbl_sin_iva:,.2f} €",
        f"21 % IVA: {iva:,.2f} €",
        f"Presupuesto Base de Licitación incluido IVA: {total:,.2f} €",
    ])
    return {
        'capitulo_01': capitulo_01,
        'capitulo_02': capitulo_02,
        'capitulo_03': capitulo_03,
        'capitulo_04': capitulo_04,
        'capitulo_05': capitulo_05,
        'capitulo_06': capitulo_06,
        'capitulo_07': capitulo_07,
        'capitulo_08': capitulo_08,
        'servicios_afectados': servicios_afectados,
        'pem': pem,
        'control_calidad_referencia': pem * PCT_CONTROL_CALIDAD,
        'gastos_generales': gg,
        'beneficio_industrial': bi,
        'pbl_sin_iva': pbl_sin_iva,
        'iva': iva,
        'total': total,
        'texto_word': texto_word,
    }
