from __future__ import annotations

# Impuestos y coeficientes generales
PCT_GG = 0.13
PCT_BI = 0.06
PCT_IVA = 0.21

# Valores por defecto alineados con el pliego subido por el usuario
# PBL sin IVA: 289.161,57 €
# SS: 8.400,00 €
# GA: 12.225,00 €
VALORES_PLIEGO = {
    "obra_civil_aba": 54633.99,
    "obra_civil_san": 63039.17,
    "pavimentacion_aba": 29472.47,
    "pavimentacion_san": 34492.96,
    "acometidas_aba": 17748.32,
    "acometidas_san": 22981.01,
    "seguridad_salud": 8400.00,
    "gestion_ambiental": 12225.00,
}

# Magnitudes físicas observadas en el pliego concreto
DEFAULTS_PLIEGO = {
    "metros_aba_80": 132.0,
    "metros_aba_100": 61.0,
    "metros_san": 132.0,
    "num_acometidas_aba": 26,
    "num_acometidas_san": 26,
    "num_valvulas": 4,
    "num_tomas_agua": 2,
    "num_conexiones_san": 4,
    "num_pozos": 7,
    "num_imbornales": 12,
}

# Catálogos unitarios orientativos (€/m o €/ud). No sustituyen una medición real.
CATALOGO_ABA = [
    {"label": "PE-100 Ø 90 mm", "obra_civil": 73.0, "pavimentacion": 88.0},
    {"label": "PE-100 Ø 110 mm", "obra_civil": 79.0, "pavimentacion": 88.0},
    {"label": "PE-100 Ø 160 mm", "obra_civil": 103.0, "pavimentacion": 89.0},
    {"label": "FD Ø 80 mm", "obra_civil": 131.0, "pavimentacion": 88.0},
    {"label": "FD Ø 100 mm", "obra_civil": 135.0, "pavimentacion": 88.0},
    {"label": "FD Ø 150 mm", "obra_civil": 166.0, "pavimentacion": 88.0},
]

CATALOGO_SAN = [
    {"label": "Gres Ø 300 mm", "obra_civil": 292.0, "pavimentacion": 97.0},
    {"label": "Gres Ø 400 mm", "obra_civil": 393.0, "pavimentacion": 103.0},
    {"label": "PVC-U Ø 315 mm", "obra_civil": 280.0, "pavimentacion": 98.0},
    {"label": "PVC-U Ø 400 mm", "obra_civil": 308.0, "pavimentacion": 103.0},
]

TIPOS_REURB = [
    {"label": "Acerado hidráulico + calzada aglomerado", "factor_aba": 1.00, "factor_san": 1.00},
    {"label": "Acerado granítico + calzada aglomerado", "factor_aba": 1.20, "factor_san": 1.18},
    {"label": "Solo acerado hidráulico (sin calzada)", "factor_aba": 0.62, "factor_san": 0.60},
    {"label": "Calzada aglomerado (sin acerado)", "factor_aba": 0.50, "factor_san": 0.48},
    {"label": "Terrizo / sin urbanizar", "factor_aba": 0.08, "factor_san": 0.06},
]

# Costes unitarios por defecto para partidas que faltaban en la versión original.
# Se calculan a partir de los importes de capítulo del pliego para que el resultado
# quede razonablemente calibrado cuando se usan las magnitudes del pliego.
COSTES_UNITARIOS_DEFAULT = {
    "acometida_aba": VALORES_PLIEGO["acometidas_aba"] / DEFAULTS_PLIEGO["num_acometidas_aba"],
    "acometida_san": VALORES_PLIEGO["acometidas_san"] / DEFAULTS_PLIEGO["num_acometidas_san"],
    # Reparto orientativo interno del capítulo de abastecimiento
    "valvula": 900.0,
    "toma_agua": 650.0,
    # Reparto orientativo interno del capítulo de saneamiento
    "conexion_san": 850.0,
    "pozo": 1600.0,
    "imbornal": 780.0,
}
