from __future__ import annotations

"""
calcular.py
-----------
Contiene la lógica matemática del presupuesto.

La aplicación Streamlit recoge datos del usuario y este archivo se encarga de:
1. convertir esos datos en capítulos económicos
2. sumar el PEM
3. aplicar GG, BI e IVA
4. devolver un diccionario con el desglose completo
"""

from dataclasses import dataclass
from typing import Dict

from datos import PCT_BI, PCT_CONTROL_CALIDAD, PCT_GG, PCT_IVA


@dataclass
class ParametrosProyecto:
    """Estructura única con todos los datos necesarios para calcular el presupuesto.

    Separar los parámetros en una dataclass evita errores y hace el código más legible.
    """

    # Metros y catálogos elegidos por el usuario
    metros_aba: float
    precios_aba: Dict[str, float]
    metros_san: float
    precios_san: Dict[str, float]
    reurbanizacion: Dict[str, float]

    # Unidades de elementos singulares
    uds_acometidas_aba: int = 0
    uds_acometidas_san: int = 0
    uds_valvulas: int = 0
    uds_tomas_agua: int = 0
    uds_conexiones_san: int = 0
    uds_pozos: int = 0
    uds_imbornales: int = 0

    # Precios unitarios de los elementos singulares
    precio_valvula: float = 0.0
    precio_toma_agua: float = 0.0
    precio_conexion_san: float = 0.0
    precio_pozo: float = 0.0
    precio_imbornal: float = 0.0

    # Seguridad y salud / gestión ambiental
    modo_ss: str = "fijo"
    importe_ss: float = 0.0
    pct_ss: float = 0.0
    modo_ga: str = "fijo"
    importe_ga: float = 0.0
    pct_ga: float = 0.0

    # Margen interno opcional
    activar_colchon: bool = False
    pct_colchon: float = 0.0


def _normalizar_modo(valor: str) -> str:
    """Asegura que el modo sea 'fijo' o 'porcentaje'."""
    valor = (valor or "fijo").strip().lower()
    return valor if valor in {"fijo", "porcentaje"} else "fijo"


def calcular_presupuesto(parametros: ParametrosProyecto) -> dict:
    """Calcula todo el presupuesto y devuelve un desglose por capítulos.

    Importante:
    - El modelo es una estimación simplificada.
    - Parte de la complejidad real del CSV se resume en catálogos y factores.
    """

    # 01 y 02. Obra civil lineal por metros de red
    cap01_obra_civil_aba = parametros.metros_aba * parametros.precios_aba["obra_civil"]
    cap02_obra_civil_san = parametros.metros_san * parametros.precios_san["obra_civil"]

    # 03 y 04. Pavimentación lineal afectada por el tipo de reurbanización
    cap03_pavimentacion_aba = (
        parametros.metros_aba
        * parametros.precios_aba["pavimentacion"]
        * parametros.reurbanizacion["factor_aba"]
    )
    cap04_pavimentacion_san = (
        parametros.metros_san
        * parametros.precios_san["pavimentacion"]
        * parametros.reurbanizacion["factor_san"]
    )

    # 05 y 06. Acometidas por número de unidades, no por metro
    cap05_acometidas_aba = parametros.uds_acometidas_aba * parametros.precios_aba["acometida_ud"]
    cap06_acometidas_san = parametros.uds_acometidas_san * parametros.precios_san["acometida_ud"]

    # Partidas singulares adicionales
    cap09_valvulas = parametros.uds_valvulas * parametros.precio_valvula
    cap10_tomas_agua = parametros.uds_tomas_agua * parametros.precio_toma_agua
    cap11_conexiones_san = parametros.uds_conexiones_san * parametros.precio_conexion_san
    cap12_pozos = parametros.uds_pozos * parametros.precio_pozo
    cap13_imbornales = parametros.uds_imbornales * parametros.precio_imbornal

    # Parcial antes de SS y GA
    parcial = sum(
        [
            cap01_obra_civil_aba,
            cap02_obra_civil_san,
            cap03_pavimentacion_aba,
            cap04_pavimentacion_san,
            cap05_acometidas_aba,
            cap06_acometidas_san,
            cap09_valvulas,
            cap10_tomas_agua,
            cap11_conexiones_san,
            cap12_pozos,
            cap13_imbornales,
        ]
    )

    # 07 y 08. SS / GA en modo fijo o porcentaje
    modo_ss = _normalizar_modo(parametros.modo_ss)
    modo_ga = _normalizar_modo(parametros.modo_ga)

    cap07_seguridad_salud = parametros.importe_ss if modo_ss == "fijo" else parcial * parametros.pct_ss
    cap08_gestion_ambiental = parametros.importe_ga if modo_ga == "fijo" else parcial * parametros.pct_ga

    # PEM y estructura final del presupuesto
    pem = parcial + cap07_seguridad_salud + cap08_gestion_ambiental
    control_calidad_ref = pem * PCT_CONTROL_CALIDAD
    gastos_generales = pem * PCT_GG
    beneficio_industrial = pem * PCT_BI
    pbl_base = pem + gastos_generales + beneficio_industrial

    # Margen interno opcional, útil para simulaciones comerciales
    margen_seguridad = pbl_base * parametros.pct_colchon if parametros.activar_colchon else 0.0
    pbl_sin_iva = pbl_base + margen_seguridad
    iva = pbl_sin_iva * PCT_IVA
    total = pbl_sin_iva + iva

    return {
        "obra_civil_aba": cap01_obra_civil_aba,
        "obra_civil_san": cap02_obra_civil_san,
        "pavimentacion_aba": cap03_pavimentacion_aba,
        "pavimentacion_san": cap04_pavimentacion_san,
        "acometidas_aba": cap05_acometidas_aba,
        "acometidas_san": cap06_acometidas_san,
        "valvulas": cap09_valvulas,
        "tomas_agua": cap10_tomas_agua,
        "conexiones_san": cap11_conexiones_san,
        "pozos": cap12_pozos,
        "imbornales": cap13_imbornales,
        "seguridad_salud": cap07_seguridad_salud,
        "gestion_ambiental": cap08_gestion_ambiental,
        "pem": pem,
        "control_calidad_referencia": control_calidad_ref,
        "gastos_generales": gastos_generales,
        "beneficio_industrial": beneficio_industrial,
        "pbl_base": pbl_base,
        "margen_seguridad": margen_seguridad,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
    }
