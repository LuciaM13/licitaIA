from datos import PCT_SS, PCT_GA, PCT_GG, PCT_BI, PCT_COLCHON, PCT_IVA


def calcular_presupuesto(
    metros_aba: float,
    precios_aba: dict,
    metros_san: float,
    precios_san: dict,
    reurbanizacion: dict,
) -> dict:
    cap01_obra_civil_aba     = metros_aba * precios_aba["obra_civil"]
    cap02_obra_civil_san     = metros_san * precios_san["obra_civil"]
    cap03_pavimentacion_aba  = metros_aba * precios_aba["pavimentacion"] * reurbanizacion["factor_aba"]
    cap04_pavimentacion_san  = metros_san * precios_san["pavimentacion"] * reurbanizacion["factor_san"]
    cap05_acometidas_aba     = metros_aba * precios_aba["acometidas"]
    cap06_acometidas_san     = metros_san * precios_san["acometidas"]

    parcial = (cap01_obra_civil_aba + cap02_obra_civil_san
             + cap03_pavimentacion_aba + cap04_pavimentacion_san
             + cap05_acometidas_aba + cap06_acometidas_san)

    cap07_seguridad_salud   = parcial * PCT_SS
    cap08_gestion_ambiental = parcial * PCT_GA

    pem                  = parcial + cap07_seguridad_salud + cap08_gestion_ambiental
    gastos_generales     = pem * PCT_GG
    beneficio_industrial = pem * PCT_BI
    pbl_base             = pem + gastos_generales + beneficio_industrial
    colchon              = pbl_base * PCT_COLCHON
    pbl_sin_iva          = pbl_base + colchon
    iva                  = pbl_sin_iva * PCT_IVA
    total                = pbl_sin_iva + iva

    return {
        "obra_civil_aba": cap01_obra_civil_aba,
        "obra_civil_san": cap02_obra_civil_san,
        "pavimentacion_aba": cap03_pavimentacion_aba,
        "pavimentacion_san": cap04_pavimentacion_san,
        "acometidas_aba": cap05_acometidas_aba,
        "acometidas_san": cap06_acometidas_san,
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
    }
