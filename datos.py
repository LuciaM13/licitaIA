from __future__ import annotations

# Porcentajes generales
PCT_GG = 0.13  # Gastos generales
PCT_BI = 0.06  # Beneficio industrial
PCT_IVA = 0.21  # IVA
PCT_CONTROL_CALIDAD = 0.01  # Referencia interna

# Modos por defecto para SS y GA
MODO_SS_DEFAULT = "fijo"        # "fijo" o "porcentaje"
MODO_GA_DEFAULT = "fijo"        # "fijo" o "porcentaje"
IMPORTE_SS_DEFAULT = 8400.00
IMPORTE_GA_DEFAULT = 12225.00
PCT_SS_DEFAULT = 0.11
PCT_GA_DEFAULT = 0.04

# Colchón comercial opcional
COLCHON_ACTIVO_DEFAULT = False
PCT_COLCHON_DEFAULT = 0.10

CATALOGO_ABA = [
    {"label": "PE-100 Ø 90 mm", "obra_civil": 73.0, "pavimentacion": 88.0, "acometida_ud": 650.0},
    {"label": "PE-100 Ø 110 mm", "obra_civil": 79.0, "pavimentacion": 88.0, "acometida_ud": 680.0},
    {"label": "PE-100 Ø 160 mm", "obra_civil": 103.0, "pavimentacion": 89.0, "acometida_ud": 720.0},
    {"label": "PE-100 Ø 200 mm", "obra_civil": 130.0, "pavimentacion": 91.0, "acometida_ud": 780.0},
    {"label": "FD Ø 80 mm", "obra_civil": 131.0, "pavimentacion": 88.0, "acometida_ud": 760.0},
    {"label": "FD Ø 100 mm", "obra_civil": 135.0, "pavimentacion": 88.0, "acometida_ud": 800.0},
    {"label": "FD Ø 150 mm", "obra_civil": 166.0, "pavimentacion": 88.0, "acometida_ud": 880.0},
    {"label": "FD Ø 200 mm", "obra_civil": 217.0, "pavimentacion": 91.0, "acometida_ud": 950.0},
    {"label": "FD Ø 250 mm", "obra_civil": 252.0, "pavimentacion": 94.0, "acometida_ud": 1020.0},
    {"label": "FD Ø 300 mm", "obra_civil": 308.0, "pavimentacion": 97.0, "acometida_ud": 1100.0},
]

CATALOGO_SAN = [
    {"label": "Gres Ø 300 mm", "obra_civil": 292.0, "pavimentacion": 97.0, "acometida_ud": 900.0},
    {"label": "Gres Ø 400 mm", "obra_civil": 393.0, "pavimentacion": 103.0, "acometida_ud": 980.0},
    {"label": "Gres Ø 500 mm", "obra_civil": 466.0, "pavimentacion": 108.0, "acometida_ud": 1060.0},
    {"label": "Gres Ø 600 mm", "obra_civil": 578.0, "pavimentacion": 114.0, "acometida_ud": 1150.0},
    {"label": "HA Ø 300 mm", "obra_civil": 318.0, "pavimentacion": 97.0, "acometida_ud": 900.0},
    {"label": "HA Ø 400 mm", "obra_civil": 331.0, "pavimentacion": 103.0, "acometida_ud": 980.0},
    {"label": "PVC-U Ø 315 mm", "obra_civil": 280.0, "pavimentacion": 98.0, "acometida_ud": 920.0},
    {"label": "PVC-U Ø 400 mm", "obra_civil": 308.0, "pavimentacion": 103.0, "acometida_ud": 980.0},
    {"label": "PVC-U Ø 500 mm", "obra_civil": 405.0, "pavimentacion": 108.0, "acometida_ud": 1060.0},
]

TIPOS_REURB = [
    {"label": "Acerado hidráulico + calzada aglomerado", "factor_aba": 1.00, "factor_san": 1.00},
    {"label": "Acerado granítico + calzada aglomerado", "factor_aba": 1.20, "factor_san": 1.18},
    {"label": "Solo acerado hidráulico (sin calzada)", "factor_aba": 0.62, "factor_san": 0.60},
    {"label": "Solo acerado granítico (sin calzada)", "factor_aba": 0.72, "factor_san": 0.70},
    {"label": "Calzada aglomerado (sin acerado)", "factor_aba": 0.50, "factor_san": 0.48},
    {"label": "Terrizo / sin urbanizar", "factor_aba": 0.08, "factor_san": 0.06},
]

PRECIOS_UNIDADES = {
    "valvula_compuerta": 950.0,
    "toma_agua": 600.0,
    "conexion_saneamiento": 850.0,
    "pozo_registro": 1650.0,
    "imbornal": 720.0,
}

CASO_PLIEGO_EMASESA = {
    "longitud_aba": 193.0,
    "tipo_aba": "FD Ø 80 mm",
    "longitud_san": 132.0,
    "tipo_san": "Gres Ø 300 mm",
    "reurbanizacion": "Acerado hidráulico + calzada aglomerado",
    "uds_acometidas_aba": 26,
    "uds_acometidas_san": 26,
    "uds_valvulas": 4,
    "uds_tomas_agua": 2,
    "uds_conexiones_san": 4,
    "uds_pozos": 7,
    "uds_imbornales": 12,
    "modo_ss": "fijo",
    "importe_ss": 8400.0,
    "modo_ga": "fijo",
    "importe_ga": 12225.0,
    "activar_colchon": False,
    "pct_colchon": 0.10,
}
