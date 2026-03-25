from __future__ import annotations

"""
calcular.py
===========
Aquí vive la lógica económica de la aplicación.

Este archivo hace tres cosas:
1. transforma los datos introducidos en cantidades económicas
2. agrupa esas cantidades por capítulos
3. calcula PEM, GG, BI, IVA y total

Está separado de la interfaz para que sea más fácil de mantener, probar
y reutilizar en el futuro.
"""

from dataclasses import dataclass
from typing import Dict

from datos import PCT_BI, PCT_CONTROL_CALIDAD, PCT_GG, PCT_IVA


@dataclass
class ParametrosProyecto:
    """
    Estructura única con todos los parámetros necesarios.

    Usar una dataclass evita pasar decenas de variables sueltas y hace
    mucho más fácil leer qué datos necesita realmente el cálculo.
    """

    # Redes principales
    metros_aba: float
    precios_aba: Dict[str, float]
    metros_san: float
    precios_san: Dict[str, float]
    metros_ovoide: float
    precio_ovoide_m: float

    # Geometría y excavación
    ancho_zanja_aba_m: float
    profundidad_aba_m: float
    ancho_zanja_san_m: float
    profundidad_san_m: float
    pct_exc_manual_aba: float
    pct_exc_manual_san: float
    pct_entibacion_aba: float
    pct_entibacion_san: float

    # Materiales auxiliares
    espesor_arena_aba_m: float
    espesor_arena_san_m: float
    espesor_relleno_aba_m: float
    espesor_relleno_san_m: float

    # Demoliciones
    dem_bordillo_m: float
    precio_dem_bordillo_m: float
    dem_acerado_m2: float
    precio_dem_acerado_m2: float
    dem_calzada_m2: float
    precio_dem_calzada_m2: float

    # Reposiciones
    rep_acerado_m2: float
    precio_rep_acerado_m2: float
    rep_bordillo_m: float
    precio_rep_bordillo_m: float
    rep_adoquin_m2: float
    precio_rep_adoquin_m2: float
    rep_rodadura_m2: float
    precio_rodadura_m3: float
    espesor_rodadura_m: float
    rep_base_pavimento_m2: float
    precio_base_pavimento_m3: float
    espesor_base_pavimento_m: float
    rep_hormigon_m2: float
    precio_hormigon_m3: float
    espesor_hormigon_m: float
    rep_base_granular_m2: float
    precio_base_granular_m3: float
    espesor_base_granular_m: float
    uds_dem_arqueta_imbornal: int
    precio_dem_arqueta_imbornal_ud: float
    uds_dem_imbornal_tuberia: int
    precio_dem_imbornal_tuberia_ud: float

    # Excavación y transporte
    precio_exc_mecanica_hasta_25_m3: float
    precio_exc_mecanica_mas_25_m3: float
    precio_exc_manual_hasta_25_m3: float
    precio_exc_manual_mas_25_m3: float
    precio_entibacion_hasta_25_m2: float
    precio_entibacion_mas_25_m2: float
    precio_carga_m3: float
    precio_transporte_m3: float
    precio_canon_tierras_m3: float
    precio_arena_m3: float
    precio_relleno_m3: float

    # Elementos singulares
    uds_valvulas: int
    precio_valvula: float
    uds_tomas_agua: int
    precio_toma_agua: float
    uds_conexiones_san: int
    precio_conexion_san: float

    # Acometidas
    uds_acometidas_aba: int
    precio_acometida_aba_ud: float
    uds_acometidas_san: int
    precio_acometida_san_ud: float

    # Pozos, imbornales, marcos y materiales
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

    # Otros costes
    pct_servicios_afectados: float
    modo_ss: str
    importe_ss: float
    pct_ss: float
    modo_ga: str
    importe_ga: float
    pct_ga: float
    activar_colchon: bool
    pct_colchon: float


def _normalizar_modo(valor: str) -> str:
    """Devuelve siempre 'fijo' o 'porcentaje'."""
    valor = (valor or "fijo").strip().lower()
    return valor if valor in {"fijo", "porcentaje"} else "fijo"


def _volumen_zanja(longitud_m: float, ancho_m: float, profundidad_m: float) -> float:
    """Volumen geométrico simplificado de la zanja."""
    return max(longitud_m, 0.0) * max(ancho_m, 0.0) * max(profundidad_m, 0.0)


def _area_entibacion(longitud_m: float, profundidad_m: float, porcentaje: float) -> float:
    """
    Superficie estimada de entibación.

    Fórmula usada:
    2 lados de zanja * longitud * profundidad * porcentaje de tramos entibados
    """
    return 2.0 * max(longitud_m, 0.0) * max(profundidad_m, 0.0) * max(porcentaje, 0.0)


def _precio_excavacion(depth_m: float, manual: bool, params: ParametrosProyecto) -> float:
    """Elige el precio unitario correcto según profundidad y método."""
    if manual:
        return (
            params.precio_exc_manual_hasta_25_m3
            if depth_m <= 2.5
            else params.precio_exc_manual_mas_25_m3
        )
    return (
        params.precio_exc_mecanica_hasta_25_m3
        if depth_m <= 2.5
        else params.precio_exc_mecanica_mas_25_m3
    )


def _precio_entibacion(depth_m: float, params: ParametrosProyecto) -> float:
    """Elige el precio de entibación según profundidad."""
    return (
        params.precio_entibacion_hasta_25_m2
        if depth_m <= 2.5
        else params.precio_entibacion_mas_25_m2
    )


def calcular_presupuesto(parametros: ParametrosProyecto) -> dict:
    """
    Calcula el presupuesto completo.

    Devuelve un diccionario plano para que la app pueda mostrar:
    - métricas
    - tablas
    - desgloses
    - cantidades auxiliares
    """

    # ======================================================
    # 1) Tuberías principales
    # ======================================================
    cap_tuberia_aba = parametros.metros_aba * parametros.precios_aba["tuberia_m"]
    cap_tuberia_san = parametros.metros_san * parametros.precios_san["tuberia_m"]
    cap_tuberia_ovoide = parametros.metros_ovoide * parametros.precio_ovoide_m

    # ======================================================
    # 2) Excavaciones y materiales auxiliares
    # ======================================================
    vol_zanja_aba = _volumen_zanja(
        parametros.metros_aba, parametros.ancho_zanja_aba_m, parametros.profundidad_aba_m
    )
    vol_zanja_san = _volumen_zanja(
        parametros.metros_san, parametros.ancho_zanja_san_m, parametros.profundidad_san_m
    )

    vol_manual_aba = vol_zanja_aba * parametros.pct_exc_manual_aba
    vol_mecanica_aba = vol_zanja_aba - vol_manual_aba
    vol_manual_san = vol_zanja_san * parametros.pct_exc_manual_san
    vol_mecanica_san = vol_zanja_san - vol_manual_san

    precio_exc_mec_aba = _precio_excavacion(parametros.profundidad_aba_m, manual=False, params=parametros)
    precio_exc_man_aba = _precio_excavacion(parametros.profundidad_aba_m, manual=True, params=parametros)
    precio_exc_mec_san = _precio_excavacion(parametros.profundidad_san_m, manual=False, params=parametros)
    precio_exc_man_san = _precio_excavacion(parametros.profundidad_san_m, manual=True, params=parametros)

    cap_exc_mecanica_aba = vol_mecanica_aba * precio_exc_mec_aba
    cap_exc_manual_aba = vol_manual_aba * precio_exc_man_aba
    cap_exc_mecanica_san = vol_mecanica_san * precio_exc_mec_san
    cap_exc_manual_san = vol_manual_san * precio_exc_man_san

    area_ent_aba = _area_entibacion(
        parametros.metros_aba, parametros.profundidad_aba_m, parametros.pct_entibacion_aba
    )
    area_ent_san = _area_entibacion(
        parametros.metros_san, parametros.profundidad_san_m, parametros.pct_entibacion_san
    )
    cap_entibacion_aba = area_ent_aba * _precio_entibacion(parametros.profundidad_aba_m, parametros)
    cap_entibacion_san = area_ent_san * _precio_entibacion(parametros.profundidad_san_m, parametros)

    vol_total_tierras = vol_zanja_aba + vol_zanja_san
    cap_carga_tierras = vol_total_tierras * parametros.precio_carga_m3
    cap_transporte_tierras = vol_total_tierras * parametros.precio_transporte_m3
    cap_canon_tierras = vol_total_tierras * parametros.precio_canon_tierras_m3

    vol_arena_aba = parametros.metros_aba * parametros.ancho_zanja_aba_m * parametros.espesor_arena_aba_m
    vol_arena_san = parametros.metros_san * parametros.ancho_zanja_san_m * parametros.espesor_arena_san_m
    vol_arena_total = vol_arena_aba + vol_arena_san
    cap_arena = vol_arena_total * parametros.precio_arena_m3

    vol_relleno_aba = parametros.metros_aba * parametros.ancho_zanja_aba_m * parametros.espesor_relleno_aba_m
    vol_relleno_san = parametros.metros_san * parametros.ancho_zanja_san_m * parametros.espesor_relleno_san_m
    vol_relleno_total = vol_relleno_aba + vol_relleno_san
    cap_relleno = vol_relleno_total * parametros.precio_relleno_m3

    # ======================================================
    # 3) Demoliciones
    # ======================================================
    cap_dem_bordillo = parametros.dem_bordillo_m * parametros.precio_dem_bordillo_m
    cap_dem_acerado = parametros.dem_acerado_m2 * parametros.precio_dem_acerado_m2
    cap_dem_calzada = parametros.dem_calzada_m2 * parametros.precio_dem_calzada_m2
    cap_dem_arqueta_imbornal = (
        parametros.uds_dem_arqueta_imbornal * parametros.precio_dem_arqueta_imbornal_ud
    )
    cap_dem_imbornal_tuberia = (
        parametros.uds_dem_imbornal_tuberia * parametros.precio_dem_imbornal_tuberia_ud
    )

    # ======================================================
    # 4) Reposiciones
    # ======================================================
    cap_rep_acerado = parametros.rep_acerado_m2 * parametros.precio_rep_acerado_m2
    cap_rep_bordillo = parametros.rep_bordillo_m * parametros.precio_rep_bordillo_m
    cap_rep_adoquin = parametros.rep_adoquin_m2 * parametros.precio_rep_adoquin_m2
    cap_rep_rodadura = (
        parametros.rep_rodadura_m2 * parametros.espesor_rodadura_m * parametros.precio_rodadura_m3
    )
    cap_rep_base_pavimento = (
        parametros.rep_base_pavimento_m2
        * parametros.espesor_base_pavimento_m
        * parametros.precio_base_pavimento_m3
    )
    cap_rep_hormigon = (
        parametros.rep_hormigon_m2 * parametros.espesor_hormigon_m * parametros.precio_hormigon_m3
    )
    cap_rep_base_granular = (
        parametros.rep_base_granular_m2
        * parametros.espesor_base_granular_m
        * parametros.precio_base_granular_m3
    )

    # ======================================================
    # 5) Elementos singulares y acometidas
    # ======================================================
    cap_valvulas = parametros.uds_valvulas * parametros.precio_valvula
    cap_tomas_agua = parametros.uds_tomas_agua * parametros.precio_toma_agua
    cap_conexiones_san = parametros.uds_conexiones_san * parametros.precio_conexion_san
    cap_acometidas_aba = parametros.uds_acometidas_aba * parametros.precio_acometida_aba_ud
    cap_acometidas_san = parametros.uds_acometidas_san * parametros.precio_acometida_san_ud
    cap_pozos = parametros.uds_pozos * parametros.precio_pozo_ud
    cap_imbornales = parametros.uds_imbornales * parametros.precio_imbornal_ud
    cap_marcos = parametros.uds_marcos * parametros.precio_marco_ud
    cap_tapas_pozo = parametros.uds_tapas_pozo * parametros.precio_tapa_pozo_ud
    cap_pates_pozo = parametros.uds_pates_pozo * parametros.precio_pate_pozo_ud

    # ======================================================
    # 6) Parcial de ejecución material antes de porcentajes
    # ======================================================
    parcial_directo = sum(
        [
            cap_tuberia_aba,
            cap_tuberia_san,
            cap_tuberia_ovoide,
            cap_exc_mecanica_aba,
            cap_exc_manual_aba,
            cap_exc_mecanica_san,
            cap_exc_manual_san,
            cap_entibacion_aba,
            cap_entibacion_san,
            cap_carga_tierras,
            cap_transporte_tierras,
            cap_canon_tierras,
            cap_arena,
            cap_relleno,
            cap_dem_bordillo,
            cap_dem_acerado,
            cap_dem_calzada,
            cap_dem_arqueta_imbornal,
            cap_dem_imbornal_tuberia,
            cap_rep_acerado,
            cap_rep_bordillo,
            cap_rep_adoquin,
            cap_rep_rodadura,
            cap_rep_base_pavimento,
            cap_rep_hormigon,
            cap_rep_base_granular,
            cap_valvulas,
            cap_tomas_agua,
            cap_conexiones_san,
            cap_acometidas_aba,
            cap_acometidas_san,
            cap_pozos,
            cap_imbornales,
            cap_marcos,
            cap_tapas_pozo,
            cap_pates_pozo,
        ]
    )

    cap_servicios_afectados = parcial_directo * parametros.pct_servicios_afectados

    modo_ss = _normalizar_modo(parametros.modo_ss)
    modo_ga = _normalizar_modo(parametros.modo_ga)

    cap_seguridad_salud = (
        parametros.importe_ss if modo_ss == "fijo" else parcial_directo * parametros.pct_ss
    )
    cap_gestion_ambiental = (
        parametros.importe_ga if modo_ga == "fijo" else parcial_directo * parametros.pct_ga
    )

    # ======================================================
    # 7) Estructura final del presupuesto
    # ======================================================
    pem = parcial_directo + cap_servicios_afectados + cap_seguridad_salud + cap_gestion_ambiental
    control_calidad_ref = pem * PCT_CONTROL_CALIDAD
    gastos_generales = pem * PCT_GG
    beneficio_industrial = pem * PCT_BI
    pbl_base = pem + gastos_generales + beneficio_industrial
    margen_seguridad = pbl_base * parametros.pct_colchon if parametros.activar_colchon else 0.0
    pbl_sin_iva = pbl_base + margen_seguridad
    iva = pbl_sin_iva * PCT_IVA
    total = pbl_sin_iva + iva

    return {
        # Cantidades auxiliares
        "vol_zanja_aba": vol_zanja_aba,
        "vol_zanja_san": vol_zanja_san,
        "vol_total_tierras": vol_total_tierras,
        "area_entibacion_aba": area_ent_aba,
        "area_entibacion_san": area_ent_san,
        "vol_arena_total": vol_arena_total,
        "vol_relleno_total": vol_relleno_total,

        # Capítulos directos
        "tuberia_aba": cap_tuberia_aba,
        "tuberia_san": cap_tuberia_san,
        "tuberia_ovoide": cap_tuberia_ovoide,
        "exc_mecanica_aba": cap_exc_mecanica_aba,
        "exc_manual_aba": cap_exc_manual_aba,
        "exc_mecanica_san": cap_exc_mecanica_san,
        "exc_manual_san": cap_exc_manual_san,
        "entibacion_aba": cap_entibacion_aba,
        "entibacion_san": cap_entibacion_san,
        "carga_tierras": cap_carga_tierras,
        "transporte_tierras": cap_transporte_tierras,
        "canon_tierras": cap_canon_tierras,
        "arena": cap_arena,
        "relleno": cap_relleno,
        "dem_bordillo": cap_dem_bordillo,
        "dem_acerado": cap_dem_acerado,
        "dem_calzada": cap_dem_calzada,
        "dem_arqueta_imbornal": cap_dem_arqueta_imbornal,
        "dem_imbornal_tuberia": cap_dem_imbornal_tuberia,
        "rep_acerado": cap_rep_acerado,
        "rep_bordillo": cap_rep_bordillo,
        "rep_adoquin": cap_rep_adoquin,
        "rep_rodadura": cap_rep_rodadura,
        "rep_base_pavimento": cap_rep_base_pavimento,
        "rep_hormigon": cap_rep_hormigon,
        "rep_base_granular": cap_rep_base_granular,
        "valvulas": cap_valvulas,
        "tomas_agua": cap_tomas_agua,
        "conexiones_san": cap_conexiones_san,
        "acometidas_aba": cap_acometidas_aba,
        "acometidas_san": cap_acometidas_san,
        "pozos": cap_pozos,
        "imbornales": cap_imbornales,
        "marcos": cap_marcos,
        "tapas_pozo": cap_tapas_pozo,
        "pates_pozo": cap_pates_pozo,
        "parcial_directo": parcial_directo,
        "servicios_afectados": cap_servicios_afectados,
        "seguridad_salud": cap_seguridad_salud,
        "gestion_ambiental": cap_gestion_ambiental,
        "pem": pem,
        "control_calidad_referencia": control_calidad_ref,
        "gastos_generales": gastos_generales,
        "beneficio_industrial": beneficio_industrial,
        "pbl_base": pbl_base,
        "colchon_comercial": margen_seguridad,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
    }
