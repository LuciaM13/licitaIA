from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from datos import PCT_BI, PCT_GG, PCT_IVA


@dataclass
class ParametrosProyecto:
    metros_aba: float
    precios_aba: Dict[str, float]
    metros_san: float
    precios_san: Dict[str, float]
    reurbanizacion: Dict[str, float]
    num_acometidas_aba: int
    coste_acometida_aba: float
    num_acometidas_san: int
    coste_acometida_san: float
    num_valvulas: int = 0
    coste_valvula: float = 0.0
    num_tomas_agua: int = 0
    coste_toma_agua: float = 0.0
    num_conexiones_san: int = 0
    coste_conexion_san: float = 0.0
    num_pozos: int = 0
    coste_pozo: float = 0.0
    num_imbornales: int = 0
    coste_imbornal: float = 0.0
    seguridad_salud_modo: str = "fijo"   # fijo | porcentaje
    seguridad_salud_valor: float = 0.0     # € si fijo, ratio si porcentaje
    gestion_ambiental_modo: str = "fijo"  # fijo | porcentaje
    gestion_ambiental_valor: float = 0.0   # € si fijo, ratio si porcentaje
    incluir_colchon: bool = False
    pct_colchon: float = 0.0


def _validar_no_negativo(nombre: str, valor: float) -> None:
    if valor < 0:
        raise ValueError(f"{nombre} no puede ser negativo")


def _importe_partida(modo: str, valor: float, base: float) -> float:
    if modo == "fijo":
        return valor
    if modo == "porcentaje":
        return base * valor
    raise ValueError("El modo debe ser 'fijo' o 'porcentaje'")


def calcular_presupuesto(params: ParametrosProyecto) -> dict:
    for nombre, valor in [
        ("metros_aba", params.metros_aba),
        ("metros_san", params.metros_san),
        ("coste_acometida_aba", params.coste_acometida_aba),
        ("coste_acometida_san", params.coste_acometida_san),
        ("coste_valvula", params.coste_valvula),
        ("coste_toma_agua", params.coste_toma_agua),
        ("coste_conexion_san", params.coste_conexion_san),
        ("coste_pozo", params.coste_pozo),
        ("coste_imbornal", params.coste_imbornal),
        ("seguridad_salud_valor", params.seguridad_salud_valor),
        ("gestion_ambiental_valor", params.gestion_ambiental_valor),
        ("pct_colchon", params.pct_colchon),
    ]:
        _validar_no_negativo(nombre, float(valor))

    cap01_obra_civil_aba = params.metros_aba * params.precios_aba["obra_civil"]
    cap02_obra_civil_san = params.metros_san * params.precios_san["obra_civil"]
    cap03_pavimentacion_aba = (
        params.metros_aba * params.precios_aba["pavimentacion"] * params.reurbanizacion["factor_aba"]
    )
    cap04_pavimentacion_san = (
        params.metros_san * params.precios_san["pavimentacion"] * params.reurbanizacion["factor_san"]
    )

    cap05_acometidas_aba = (
        params.num_acometidas_aba * params.coste_acometida_aba
        + params.num_valvulas * params.coste_valvula
        + params.num_tomas_agua * params.coste_toma_agua
    )
    cap06_acometidas_san = (
        params.num_acometidas_san * params.coste_acometida_san
        + params.num_conexiones_san * params.coste_conexion_san
        + params.num_pozos * params.coste_pozo
        + params.num_imbornales * params.coste_imbornal
    )

    subtotal_capitulos_1_6 = sum([
        cap01_obra_civil_aba,
        cap02_obra_civil_san,
        cap03_pavimentacion_aba,
        cap04_pavimentacion_san,
        cap05_acometidas_aba,
        cap06_acometidas_san,
    ])

    cap07_seguridad_salud = _importe_partida(
        params.seguridad_salud_modo,
        params.seguridad_salud_valor,
        subtotal_capitulos_1_6,
    )
    cap08_gestion_ambiental = _importe_partida(
        params.gestion_ambiental_modo,
        params.gestion_ambiental_valor,
        subtotal_capitulos_1_6,
    )

    pem = subtotal_capitulos_1_6 + cap07_seguridad_salud + cap08_gestion_ambiental
    gastos_generales = pem * PCT_GG
    beneficio_industrial = pem * PCT_BI
    pbl_base = pem + gastos_generales + beneficio_industrial

    colchon = pbl_base * params.pct_colchon if params.incluir_colchon else 0.0
    pbl_sin_iva = pbl_base + colchon
    iva = pbl_sin_iva * PCT_IVA
    total = pbl_sin_iva + iva
    control_calidad_recomendado = pem * 0.01

    return {
        "obra_civil_aba": cap01_obra_civil_aba,
        "obra_civil_san": cap02_obra_civil_san,
        "pavimentacion_aba": cap03_pavimentacion_aba,
        "pavimentacion_san": cap04_pavimentacion_san,
        "acometidas_aba": cap05_acometidas_aba,
        "acometidas_san": cap06_acometidas_san,
        "subtotal_capitulos_1_6": subtotal_capitulos_1_6,
        "seguridad_salud": cap07_seguridad_salud,
        "gestion_ambiental": cap08_gestion_ambiental,
        "pem": pem,
        "gastos_generales": gastos_generales,
        "beneficio_industrial": beneficio_industrial,
        "pbl_base": pbl_base,
        "margen_seguridad": colchon,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
        "control_calidad_recomendado": control_calidad_recomendado,
    }
