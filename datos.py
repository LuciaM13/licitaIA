from __future__ import annotations

"""
datos.py
========
Este archivo centraliza todos los datos "fijos" de LicitaIA.

Qué guarda:
- porcentajes generales del presupuesto
- precios sacados del CSV de referencia
- catálogos y opciones que verá el usuario en la app
- valores por defecto para que la interfaz sea cómoda de usar

La idea es que cualquier cambio de precios u opciones se haga aquí y no repartido
por todo el proyecto.
"""

# ==========================================================
# Porcentajes generales del presupuesto
# ==========================================================
# Estos porcentajes no salen de cada partida del CSV:
# forman parte de la estructura final del presupuesto.
PCT_GG = 0.13
PCT_BI = 0.06
PCT_IVA = 0.21
PCT_CONTROL_CALIDAD = 0.01


# ==========================================================
# Precios de abastecimiento (ABA)
# ==========================================================
# El CSV aportado está mucho más orientado a saneamiento y reposiciones urbanas
# que a una familia completa de abastecimiento pequeño/medio. Por eso, para ABA
# mantenemos un catálogo paramétrico por diámetro/material.
#
# Importante:
# - aquí "tuberia_m" representa el coste base por metro de suministro y montaje
#   de la red ABA
# - el resto de familias (demoliciones, excavaciones, materiales auxiliares,
#   reposiciones, elementos singulares...) ya se calculan aparte con partidas
#   específicas y no van escondidas dentro de este precio.
CATALOGO_ABA = [
    {"label": "PE-100 Ø 90 mm",  "tuberia_m": 39.00,  "diametro_mm": 90},
    {"label": "PE-100 Ø 110 mm", "tuberia_m": 44.00,  "diametro_mm": 110},
    {"label": "PE-100 Ø 160 mm", "tuberia_m": 61.00,  "diametro_mm": 160},
    {"label": "PE-100 Ø 200 mm", "tuberia_m": 79.00,  "diametro_mm": 200},
    {"label": "FD Ø 80 mm",      "tuberia_m": 63.00,  "diametro_mm": 80},
    {"label": "FD Ø 100 mm",     "tuberia_m": 69.00,  "diametro_mm": 100},
    {"label": "FD Ø 150 mm",     "tuberia_m": 91.00,  "diametro_mm": 150},
    {"label": "FD Ø 200 mm",     "tuberia_m": 128.00, "diametro_mm": 200},
    {"label": "FD Ø 250 mm",     "tuberia_m": 164.00, "diametro_mm": 250},
    {"label": "FD Ø 300 mm",     "tuberia_m": 209.00, "diametro_mm": 300},
]

# ----------------------------------------------------------
# Segundo tramo ABA (para obras con dos diámetros distintos)
# ----------------------------------------------------------
# Catálogo idéntico al principal; se muestra como "Tramo 2" en la interfaz.
# El usuario puede poner metros = 0 si solo tiene un tramo.
CATALOGO_ABA_2 = CATALOGO_ABA  # mismo catálogo, alias semántico


# ==========================================================
# Precios de saneamiento (SAN) tomados del CSV
# ==========================================================
# "tuberia_m" sí está apoyado en las líneas del CSV de suministro y montaje.
CATALOGO_SAN = [
    {"label": "Gres Ø 300 mm",   "tuberia_m": 126.10,  "diametro_mm": 300,  "familia": "gres"},
    {"label": "Gres Ø 400 mm",   "tuberia_m": 214.00,  "diametro_mm": 400,  "familia": "gres"},
    {"label": "Gres Ø 500 mm",   "tuberia_m": 311.38,  "diametro_mm": 500,  "familia": "gres"},
    {"label": "Gres Ø 600 mm",   "tuberia_m": 412.40,  "diametro_mm": 600,  "familia": "gres"},
    {"label": "Gres Ø 800 mm",   "tuberia_m": 1026.63, "diametro_mm": 800,  "familia": "gres"},
    {"label": "Gres Ø 1000 mm",  "tuberia_m": 1279.56, "diametro_mm": 1000, "familia": "gres"},
    {"label": "HA Ø 300 mm",     "tuberia_m": 57.105,  "diametro_mm": 300,  "familia": "hormigon"},
    {"label": "HA Ø 400 mm",     "tuberia_m": 57.105,  "diametro_mm": 400,  "familia": "hormigon"},
    {"label": "HA Ø 500 mm",     "tuberia_m": 67.575,  "diametro_mm": 500,  "familia": "hormigon"},
    {"label": "HA Ø 600 mm",     "tuberia_m": 76.650,  "diametro_mm": 600,  "familia": "hormigon"},
    {"label": "HA Ø 800 mm",     "tuberia_m": 134.805, "diametro_mm": 800,  "familia": "hormigon"},
    {"label": "HA Ø 1000 mm",    "tuberia_m": 185.595, "diametro_mm": 1000, "familia": "hormigon"},
    {"label": "HA Ø 1200 mm",    "tuberia_m": 314.070, "diametro_mm": 1200, "familia": "hormigon"},
    {"label": "PVC-U Ø 315 mm",  "tuberia_m": 45.92,   "diametro_mm": 315,  "familia": "pvc"},
    {"label": "PVC-U Ø 400 mm",  "tuberia_m": 93.64,   "diametro_mm": 400,  "familia": "pvc"},
    {"label": "PVC-U Ø 500 mm",  "tuberia_m": 146.26,  "diametro_mm": 500,  "familia": "pvc"},
]


# ==========================================================
# Ovoides del CSV
# ==========================================================
CATALOGO_OVOIDE = [
    {"label": "Ovoide 1200x800",  "tuberia_m": 107.43},
    {"label": "Ovoide 1500x1000", "tuberia_m": 150.90},
    {"label": "Ovoide 1800x1200", "tuberia_m": 247.50},
]


# ==========================================================
# Demoliciones y reposiciones del CSV
# ==========================================================
DEMOLICION_BORDILLO = [
    {"label": "Bordillo hidráulico", "precio_m": 4.44},
    {"label": "Bordillo granítico",  "precio_m": 5.59},
]

DEMOLICION_ACERADO = [
    {"label": "Losa hidráulica", "precio_m2": 14.70},
    {"label": "Losa terrazo",    "precio_m2": 14.70},
    {"label": "Hormigón",        "precio_m2": 14.70},
]

DEMOLICION_CALZADA = [
    {"label": "Adoquín",     "precio_m2": 15.80},
    {"label": "Aglomerado",  "precio_m2": 14.29},
    {"label": "Hormigón",    "precio_m2": 17.43},
]

ACERADOS_REPOSICION = [
    {"label": "Losa hidráulica", "precio_m2": 37.14},
    {"label": "Losa terrazo",    "precio_m2": 43.20},
    {"label": "Hormigón",        "precio_m2": 52.79},
    {"label": "Granito",         "precio_m2": 84.67},
]

BORDILLOS_REPOSICION = [
    {"label": "Bordillo de hormigón", "precio_m": 16.00},
    {"label": "Bordillo granítico",   "precio_m": 22.90},
]

# Para calzada el CSV mezcla partidas por m2 y por m3.
# En la app se pide superficie y espesor para que salga un presupuesto útil.
REPOSICION_CALZADA = {
    "adoquin_m2":                      35.23,
    "rodadura_m3":                     139.64,
    "base_pavimento_m3":               117.34,
    "hormigon_m3":                     117.18,
    "base_granular_m3":                 23.46,
    "demolicion_arqueta_imbornal_ud":   72.70,
    "demolicion_imbornal_tuberia_ud":   49.17,
}


# ==========================================================
# Excavaciones y materiales auxiliares del CSV
# ==========================================================
EXCAVACION = {
    "mecanica_hasta_2_5_m3":             3.07,
    "mecanica_mas_2_5_m3":               5.00,
    "manual_hasta_2_5_m3":              11.17,
    "manual_mas_2_5_m3":                13.99,
    "entibacion_blindada_hasta_2_5_m2":  4.27,
    "entibacion_blindada_mas_2_5_m2":   22.73,
    "carga_tierras_m3":                  0.34,
    "transporte_vertedero_m3":           5.29,
    # Canon de vertedero para tierras limpias de excavación
    "canon_vertedero_tierras_m3":        1.60,
    # Canon de vertedero para residuos mixtos (demoliciones de hormigón,
    # asfalto, etc.) — CORRECCIÓN: se usa este canon para los volúmenes
    # procedentes de demolición de calzada y acerado, no el de tierras.
    "canon_vertedero_mixto_m3":         13.22,
    "arena_m3":                         22.18,
    "relleno_albero_m3":                19.39,
}


# ==========================================================
# Acometidas del CSV
# ==========================================================
ACOMETIDAS = [
    {"label": "PVC - Adaptación",        "precio_ud":  446.64},
    {"label": "PVC - Reposición < 6 m",  "precio_ud":  885.12},
    {"label": "PVC - Reposición > 6 m",  "precio_ud": 1278.78},
    {"label": "GRES - Adaptación",       "precio_ud":  485.43},
    {"label": "GRES - Reposición < 6 m", "precio_ud": 1231.79},
    {"label": "GRES - Reposición > 6 m", "precio_ud": 1759.63},
]


# ==========================================================
# Pozos, imbornales, marcos y materiales del CSV
# ==========================================================
POZOS = [
    {"label": "Ladrillo P < 2,5 m",                      "precio_ud": 1043.82},
    {"label": "Ladrillo P < 3,5 m",                      "precio_ud": 1273.56},
    {"label": "Ladrillo P < 5 m",                        "precio_ud": 1714.04},
    {"label": "Ladrillo P > 5 m",                        "precio_ud": 2455.28},
    {"label": "Prefabricado P < 2,5 m · Tub < 500",      "precio_ud": 1071.83},
    {"label": "Prefabricado P < 3,5 m · Tub < 500",      "precio_ud": 1291.82},
    {"label": "Prefabricado P > 3,5 m · Tub < 500",      "precio_ud": 1555.71},
    {"label": "Prefabricado P < 2,5 m · Tub < 600",      "precio_ud": 1124.58},
    {"label": "Prefabricado P < 3,5 m · Tub < 600",      "precio_ud": 1344.55},
    {"label": "Prefabricado P > 3,5 m · Tub < 600",      "precio_ud": 1608.48},
    {"label": "Prefabricado P < 2,5 m · Tub < 800",      "precio_ud": 1651.37},
    {"label": "Prefabricado P < 3,5 m · Tub < 800",      "precio_ud": 1406.96},
    {"label": "Prefabricado P > 3,5 m · Tub < 800",      "precio_ud": 1651.37},
    {"label": "Prefabricado P < 2,5 m · Tub < 1000",     "precio_ud": 2344.91},
    {"label": "Prefabricado P < 3,5 m · Tub < 1000",     "precio_ud": 2564.87},
    {"label": "Prefabricado P > 3,5 m · Tub < 1000",     "precio_ud": 2841.49},
    {"label": "Prefabricado P < 2,5 m · Tub < 1200",     "precio_ud": 2491.87},
    {"label": "Prefabricado P < 3,5 m · Tub < 1200",     "precio_ud": 2701.83},
    {"label": "Prefabricado P > 3,5 m · Tub < 1200",     "precio_ud": 2978.75},
    {"label": "Prefabricado P < 2,5 m · Tub < 1500",     "precio_ud": 3238.86},
    {"label": "Prefabricado P < 3,5 m · Tub < 1500",     "precio_ud": 3463.31},
    {"label": "Prefabricado P > 3,5 m · Tub < 1500",     "precio_ud": 3739.16},
    {"label": "Prefabricado P < 2,5 m · Tub < 1600",     "precio_ud": 3404.77},
    {"label": "Prefabricado P < 3,5 m · Tub < 1600",     "precio_ud": 3629.22},
    {"label": "Prefabricado P > 3,5 m · Tub < 1600",     "precio_ud": 3905.07},
    {"label": "Prefabricado P < 2,5 m · Tub < 1800",     "precio_ud": 3879.69},
    {"label": "Prefabricado P < 3,5 m · Tub < 1800",     "precio_ud": 4104.15},
    {"label": "Prefabricado P > 3,5 m · Tub < 1800",     "precio_ud": 4379.98},
    {"label": "Prefabricado P < 2,5 m · Tub < 2000",     "precio_ud": 4168.38},
    {"label": "Prefabricado P < 3,5 m · Tub < 2000",     "precio_ud": 4382.97},
    {"label": "Prefabricado P > 3,5 m · Tub < 2000",     "precio_ud": 4684.38},
    {"label": "Prefabricado P < 2,5 m · Tub < 2500",     "precio_ud": 5199.18},
    {"label": "Prefabricado P < 3,5 m · Tub < 2500",     "precio_ud": 5439.21},
    {"label": "Prefabricado P > 3,5 m · Tub < 2500",     "precio_ud": 5715.51},
    {"label": "Acondicionamiento de pozo",                "precio_ud":  222.88},
    {"label": "Anulación de pozo",                        "precio_ud":  545.82},
    {"label": "Demolición de pozo",                       "precio_ud":   44.72},
]

IMBORNALES = [
    {"label": "Rejilla con clapeta",    "precio_ud": 547.98},
    {"label": "Rejilla sin clapeta",    "precio_ud": 547.98},
    {"label": "Buzón con clapeta",      "precio_ud": 872.03},
    {"label": "Buzón sin clapeta",      "precio_ud": 802.03},
]

MARCOS = [
    {"label": "Marco superficie hasta 10 m²", "precio_ud": 1683.64},
    {"label": "Marco superficie hasta 20 m²", "precio_ud": 3498.89},
    {"label": "Marco superficie hasta 30 m²", "precio_ud": 4446.06},
    {"label": "Marco superficie hasta 35 m²", "precio_ud": 5127.49},
]

MATERIALES_POZO = [
    {"label": "Tapa de pozo de registro", "precio_ud": 160.37},
    {"label": "Pate para pozos",          "precio_ud":   1.94},
]


# ==========================================================
# Gestión de fibrocemento / amianto
# ==========================================================
# Las redes existentes de fibrocemento requieren tratamiento especial según
# normativa vigente (RD 396/2006). Se incluyen partidas orientativas:
# - retirada y transporte a vertedero autorizado (precio por metro lineal)
# - coste adicional por metro de tubería de fibrocemento (embolsado, etiquetado,
#   gestión documental, empresa especializada)
FIBROCEMENTO = {
    # Precio orientativo por metro lineal de tubería de fibrocemento retirada,
    # embolsada y transportada a gestor autorizado de residuos peligrosos.
    "retirada_m": 35.00,
    # Importe fijo de Plan de Trabajo con amianto (PTWA) y coordinación,
    # independiente de la longitud. Ajustar según empresa especializada.
    "plan_trabajo_fijo": 1200.00,
}


# ==========================================================
# Redes provisionales de suministro durante obras
# ==========================================================
# Partidas orientativas para mantener servicio a abonados mientras se ejecuta
# la renovación (Art. 2 del PPTP: incluye dimensionamiento, tendido, conexión,
# desinfección, mantenimiento y retirada final).
REDES_PROVISIONALES = {
    # Precio por metro lineal de tubería provisional (PE flexible + conexiones)
    "tuberia_provisional_m": 18.50,
    # Coste fijo de montaje y desmontaje del sistema provisional (conexiones
    # a red existente, llaves de corte provisionales, desinfección, etc.)
    "montaje_desmontaje_fijo": 850.00,
}


# ==========================================================
# Otros costes porcentuales del CSV / del proyecto
# ==========================================================
SERVICIOS_AFECTADOS = [
    {"label": "Poco",   "pct": 0.01},
    {"label": "Normal", "pct": 0.03},
    {"label": "Mucho",  "pct": 0.05},
]

PCT_SS_CSV = 0.03       # aparece en el CSV como referencia
MODO_SS_DEFAULT = "fijo"
IMPORTE_SS_DEFAULT = 8400.00

# La gestión ambiental no aparece desglosada como familia propia en el CSV aportado,
# pero sí suele venir fijada en el presupuesto base del expediente.
MODO_GA_DEFAULT = "fijo"
IMPORTE_GA_DEFAULT = 12225.00

COLCHON_ACTIVO_DEFAULT = False
PCT_COLCHON_DEFAULT = 0.10


# ==========================================================
# Geometría por defecto para estimación de zanjas y materiales
# ==========================================================
# Se muestran en la app para que el usuario pueda ajustarlos.
GEOMETRIA_DEFAULT = {
    "ancho_zanja_aba_m":                  0.60,
    "profundidad_aba_m":                  1.20,
    "ancho_zanja_san_m":                  0.90,
    "profundidad_san_m":                  1.60,
    "porcentaje_excavacion_manual_aba":  10.0,
    "porcentaje_excavacion_manual_san":  10.0,
    "porcentaje_entibacion_aba":          0.0,
    "porcentaje_entibacion_san":          0.0,
    "espesor_arena_aba_m":                0.10,
    "espesor_arena_san_m":                0.10,
    "espesor_relleno_aba_m":              0.30,
    "espesor_relleno_san_m":              0.40,
}

ESPESORES_REPOSICION_DEFAULT = {
    "espesor_rodadura_m":        0.05,
    "espesor_base_pavimento_m":  0.20,
    "espesor_hormigon_m":        0.15,
    "espesor_base_granular_m":   0.20,
}
