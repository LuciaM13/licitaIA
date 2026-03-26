from __future__ import annotations

PCT_GG = 0.13
PCT_BI = 0.06
PCT_IVA = 0.21

CATALOGO_ABA = [
    {"label": "FD Ø 80 mm", "tipo": "FD", "diametro_mm": 80, "precio_m": 63.00},
    {"label": "FD Ø 100 mm", "tipo": "FD", "diametro_mm": 100, "precio_m": 69.00},
    {"label": "FD Ø 150 mm", "tipo": "FD", "diametro_mm": 150, "precio_m": 91.00},
    {"label": "FD Ø 200 mm", "tipo": "FD", "diametro_mm": 200, "precio_m": 128.00},
    {"label": "PE-100 Ø 90 mm", "tipo": "PE-100", "diametro_mm": 90, "precio_m": 39.00},
    {"label": "PE-100 Ø 110 mm", "tipo": "PE-100", "diametro_mm": 110, "precio_m": 44.00},
    {"label": "PE-100 Ø 160 mm", "tipo": "PE-100", "diametro_mm": 160, "precio_m": 61.00},
    {"label": "PE-100 Ø 200 mm", "tipo": "PE-100", "diametro_mm": 200, "precio_m": 79.00},
]

CATALOGO_SAN = [
    {"label": "Gres Ø 300 mm", "tipo": "Gres", "diametro_mm": 300, "precio_m": 126.10},
    {"label": "Gres Ø 400 mm", "tipo": "Gres", "diametro_mm": 400, "precio_m": 214.00},
    {"label": "Gres Ø 500 mm", "tipo": "Gres", "diametro_mm": 500, "precio_m": 311.38},
    {"label": "Gres Ø 600 mm", "tipo": "Gres", "diametro_mm": 600, "precio_m": 412.40},
    {"label": "Gres Ø 800 mm", "tipo": "Gres", "diametro_mm": 800, "precio_m": 1026.63},
    {"label": "Gres Ø 1000 mm", "tipo": "Gres", "diametro_mm": 1000, "precio_m": 1279.56},
    {"label": "HA Ø 300 mm", "tipo": "Hormigón", "diametro_mm": 300, "precio_m": 57.105},
    {"label": "HA Ø 400 mm", "tipo": "Hormigón", "diametro_mm": 400, "precio_m": 57.105},
    {"label": "HA Ø 500 mm", "tipo": "Hormigón", "diametro_mm": 500, "precio_m": 67.575},
    {"label": "HA Ø 600 mm", "tipo": "Hormigón", "diametro_mm": 600, "precio_m": 76.650},
    {"label": "HA Ø 800 mm", "tipo": "Hormigón", "diametro_mm": 800, "precio_m": 134.805},
    {"label": "HA Ø 1000 mm", "tipo": "Hormigón", "diametro_mm": 1000, "precio_m": 185.595},
    {"label": "HA Ø 1200 mm", "tipo": "Hormigón", "diametro_mm": 1200, "precio_m": 314.070},
    {"label": "PVC-U Ø 315 mm", "tipo": "PVC", "diametro_mm": 315, "precio_m": 45.92},
    {"label": "PVC-U Ø 400 mm", "tipo": "PVC", "diametro_mm": 400, "precio_m": 93.64},
    {"label": "PVC-U Ø 500 mm", "tipo": "PVC", "diametro_mm": 500, "precio_m": 146.26},
]

EXCAVACION = {
    "mec_hasta_25": 3.07,
    "mec_mas_25": 5.00,
    "carga": 0.34,
    "transporte": 5.29,
    "canon_tierras": 1.60,
    "arena": 22.18,
    "relleno": 19.39,
}

ACERADOS_REPOSICION = [
    {"label": "Losa hidráulica", "precio_m2": 37.14},
    {"label": "Losa terrazo", "precio_m2": 43.20},
    {"label": "Hormigón", "precio_m2": 52.79},
    {"label": "Granito", "precio_m2": 84.67},
]

BORDILLOS_REPOSICION = [
    {"label": "Bordillo de hormigón", "precio_m": 16.00},
    {"label": "Bordillo granítico", "precio_m": 22.90},
]

CALZADAS_REPOSICION = [
    {"label": "Adoquín", "unidad": "m2", "precio": 35.23},
    {"label": "Aglomerado", "unidad": "m3", "precio": 139.64},
    {"label": "Hormigón", "unidad": "m3", "precio": 117.18},
]

ESPESOR_RELLENO_SAN = 0.40