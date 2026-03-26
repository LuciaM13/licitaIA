#Bloque 1 - Los porcentajes de la fórmula de presupuesto
PCT_SS      = 0.11    # Seguridad y Salud
PCT_GA      = 0.04    # Gestión Ambiental
PCT_GG      = 0.13    # Gastos Generales
PCT_BI      = 0.06    # Beneficio Industrial
PCT_COLCHON = 0.10    # Colchón de seguridad
PCT_IVA     = 0.21    # IVA



CATALOGO_ABA = [
    {"label": "PE-100  Ø 90 mm",   "obra_civil": 73,   "pavimentacion": 88,  "acometidas": 69},
    {"label": "PE-100  Ø 110 mm",  "obra_civil": 79,   "pavimentacion": 88,  "acometidas": 71},
    {"label": "PE-100  Ø 160 mm",  "obra_civil": 103,  "pavimentacion": 89,  "acometidas": 67},
    {"label": "PE-100  Ø 200 mm",  "obra_civil": 130,  "pavimentacion": 91,  "acometidas": 60},
    {"label": "FD  Ø 80 mm",       "obra_civil": 131,  "pavimentacion": 88,  "acometidas": 77},
    {"label": "FD  Ø 100 mm",      "obra_civil": 135,  "pavimentacion": 88,  "acometidas": 80},
    {"label": "FD  Ø 150 mm",      "obra_civil": 166,  "pavimentacion": 88,  "acometidas": 88},
    {"label": "FD  Ø 200 mm",      "obra_civil": 217,  "pavimentacion": 91,  "acometidas": 72},
    {"label": "FD  Ø 250 mm",      "obra_civil": 252,  "pavimentacion": 94,  "acometidas": 65},
    {"label": "FD  Ø 300 mm",      "obra_civil": 308,  "pavimentacion": 97,  "acometidas": 70},
    {"label": "FD  Ø 400 mm",      "obra_civil": 587,  "pavimentacion": 103, "acometidas": 64},
    {"label": "FD  Ø 500 mm",      "obra_civil": 692,  "pavimentacion": 108, "acometidas": 72},
    {"label": "FD  Ø 600 mm",      "obra_civil": 829,  "pavimentacion": 114, "acometidas": 60},
    {"label": "FD  Ø 800 mm",      "obra_civil": 1444, "pavimentacion": 126, "acometidas": 48},
    {"label": "FD  Ø 1000 mm",     "obra_civil": 1839, "pavimentacion": 137, "acometidas": 56},
    {"label": "FD  Ø 1200 mm",     "obra_civil": 2196, "pavimentacion": 149, "acometidas": 32},
]

CATALOGO_SAN = [
    {"label": "Gres  Ø 300 mm",     "obra_civil": 292,  "pavimentacion": 97,  "acometidas": 70},
    {"label": "Gres  Ø 400 mm",     "obra_civil": 393,  "pavimentacion": 103, "acometidas": 64},
    {"label": "Gres  Ø 500 mm",     "obra_civil": 466,  "pavimentacion": 108, "acometidas": 54},
    {"label": "Gres  Ø 600 mm",     "obra_civil": 578,  "pavimentacion": 114, "acometidas": 60},
    {"label": "HA  Ø 300 mm",       "obra_civil": 318,  "pavimentacion": 97,  "acometidas": 70},
    {"label": "HA  Ø 400 mm",       "obra_civil": 331,  "pavimentacion": 103, "acometidas": 64},
    {"label": "HA  Ø 500 mm",       "obra_civil": 407,  "pavimentacion": 108, "acometidas": 54},
    {"label": "HA  Ø 600 mm",       "obra_civil": 426,  "pavimentacion": 114, "acometidas": 60},
    {"label": "HA  Ø 800 mm",       "obra_civil": 600,  "pavimentacion": 126, "acometidas": 48},
    {"label": "HA  Ø 1000 mm",      "obra_civil": 765,  "pavimentacion": 137, "acometidas": 56},
    {"label": "HA  Ø 1200 mm",      "obra_civil": 1039, "pavimentacion": 149, "acometidas": 32},
    {"label": "HA+PE80  Ø 800 mm",  "obra_civil": 675,  "pavimentacion": 126, "acometidas": 48},
    {"label": "HA+PE80  Ø 1000 mm", "obra_civil": 869,  "pavimentacion": 137, "acometidas": 56},
    {"label": "HA+PE80  Ø 1500 mm", "obra_civil": 1851, "pavimentacion": 166, "acometidas": 38},
    {"label": "HA+PE80  Ø 2000 mm", "obra_civil": 2603, "pavimentacion": 195, "acometidas": 48},
    {"label": "PVC-U  Ø 315 mm",    "obra_civil": 280,  "pavimentacion": 98,  "acometidas": 72},
    {"label": "PVC-U  Ø 400 mm",    "obra_civil": 308,  "pavimentacion": 103, "acometidas": 64},
    {"label": "PVC-U  Ø 500 mm",    "obra_civil": 405,  "pavimentacion": 108, "acometidas": 54},
]

TIPOS_REURB = [
    {"label": "Acerado hidráulico + calzada aglomerado",  "factor_aba": 1.00, "factor_san": 1.00},
    {"label": "Acerado granítico + calzada aglomerado",   "factor_aba": 1.20, "factor_san": 1.18},
    {"label": "Solo acerado hidráulico (sin calzada)",     "factor_aba": 0.62, "factor_san": 0.60},
    {"label": "Solo acerado granítico (sin calzada)",      "factor_aba": 0.72, "factor_san": 0.70},
    {"label": "Calzada aglomerado (sin acerado)",          "factor_aba": 0.50, "factor_san": 0.48},
    {"label": "Terrizo / sin urbanizar",                   "factor_aba": 0.08, "factor_san": 0.06},
]
