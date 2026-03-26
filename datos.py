from __future__ import annotations

"""
datos.py
========
Versión estricta: solo contiene familias, precios y parámetros que aparecen
literalmente en la base de precios CSV y/o en el PPTP.

Reglas de esta versión:
- no hay precios manuales
- no hay geometrías auxiliares ni espesores por defecto para convertir unidades
- no hay partidas fuera de la base/pliego
- las cantidades las introduce el usuario directamente en la unidad de la base
"""

# Estructura económica del pliego
PCT_GG = 0.13
PCT_BI = 0.06
PCT_IVA = 0.21

# Capítulos del PPTP
CAPITULOS = [
    "01 OBRA CIVIL ABASTECIMIENTO",
    "02 OBRA CIVIL SANEAMIENTO",
    "03 PAVIMENTACIÓN ABASTECIMIENTO",
    "04 PAVIMENTACIÓN SANEAMIENTO",
    "05 ACOMETIDAS ABASTECIMIENTO",
    "06 ACOMETIDAS SANEAMIENTO",
    "07 SEGURIDAD Y SALUD",
    "08 GESTIÓN AMBIENTAL",
]

# El CSV visible no aporta precios cerrados para FD/PE de ABA ni para válvulas,
# tomas de agua o conexiones ABA/SAN, así que esas familias se excluyen en esta versión.

# Obra civil SAN / colectores visibles en el CSV
CATALOGO_SAN = [
    {"label": "Gres Ø 300 mm", "precio": 126.10, "unidad": "m"},
    {"label": "Gres Ø 400 mm", "precio": 214.00, "unidad": "m"},
    {"label": "Gres Ø 500 mm", "precio": 311.38, "unidad": "m"},
    {"label": "Gres Ø 600 mm", "precio": 412.40, "unidad": "m"},
    {"label": "Gres Ø 800 mm", "precio": 1026.63, "unidad": "m"},
    {"label": "Gres Ø 1000 mm", "precio": 1279.56, "unidad": "m"},
    {"label": "HA Ø 300 mm", "precio": 57.105, "unidad": "m"},
    {"label": "HA Ø 400 mm", "precio": 57.105, "unidad": "m"},
    {"label": "HA Ø 500 mm", "precio": 67.575, "unidad": "m"},
    {"label": "HA Ø 600 mm", "precio": 76.650, "unidad": "m"},
    {"label": "HA Ø 800 mm", "precio": 134.805, "unidad": "m"},
    {"label": "HA Ø 1000 mm", "precio": 185.595, "unidad": "m"},
    {"label": "HA Ø 1200 mm", "precio": 314.070, "unidad": "m"},
    {"label": "PVC-U Ø 315 mm", "precio": 45.92, "unidad": "m"},
    {"label": "PVC-U Ø 400 mm", "precio": 93.64, "unidad": "m"},
    {"label": "PVC-U Ø 500 mm", "precio": 146.26, "unidad": "m"},
]

CATALOGO_OVOIDE = [
    {"label": "Ovoide 1200x800", "precio": 107.43, "unidad": "m"},
    {"label": "Ovoide 1500x1000", "precio": 150.90, "unidad": "m"},
    {"label": "Ovoide 1800x1200", "precio": 247.50, "unidad": "m"},
]

# Movimiento de tierras / obra civil
EXCAVACION = {
    "Excavación mecánica ≤ 2,5 m": {"precio": 3.07, "unidad": "m³"},
    "Excavación mecánica > 2,5 m": {"precio": 5.00, "unidad": "m³"},
    "Excavación manual ≤ 2,5 m": {"precio": 11.17, "unidad": "m³"},
    "Excavación manual > 2,5 m": {"precio": 13.99, "unidad": "m³"},
    "Entibación blindada ≤ 2,5 m": {"precio": 4.27, "unidad": "m²"},
    "Entibación blindada > 2,5 m": {"precio": 22.73, "unidad": "m²"},
    "Carga de tierras": {"precio": 0.34, "unidad": "m³"},
    "Transporte a vertedero": {"precio": 5.29, "unidad": "m³"},
    "Canon vertido tierras": {"precio": 1.60, "unidad": "m³"},
    "Canon vertido mixto": {"precio": 13.22, "unidad": "m³"},
    "Suministro de arena": {"precio": 22.18, "unidad": "m³"},
    "Relleno de albero": {"precio": 19.39, "unidad": "m³"},
}

# Pavimentación y demoliciones
DEMOLICION_BORDILLO = [
    {"label": "Bordillo hidráulico", "precio": 4.44, "unidad": "m"},
    {"label": "Bordillo granítico", "precio": 5.59, "unidad": "m"},
]
DEMOLICION_ACERADO = [
    {"label": "Losa hidráulica", "precio": 14.70, "unidad": "m²"},
    {"label": "Losa terrazo", "precio": 14.70, "unidad": "m²"},
    {"label": "Hormigón", "precio": 14.70, "unidad": "m²"},
]
DEMOLICION_CALZADA = [
    {"label": "Adoquín", "precio": 15.80, "unidad": "m²"},
    {"label": "Aglomerado", "precio": 14.29, "unidad": "m²"},
    {"label": "Hormigón", "precio": 17.43, "unidad": "m²"},
]
BORDILLOS_REPOSICION = [
    {"label": "Bordillo de hormigón", "precio": 16.00, "unidad": "m"},
    {"label": "Bordillo granítico", "precio": 22.90, "unidad": "m"},
]
ACERADOS_REPOSICION = [
    {"label": "Losa hidráulica", "precio": 37.14, "unidad": "m²"},
    {"label": "Losa terrazo", "precio": 43.20, "unidad": "m²"},
    {"label": "Hormigón", "precio": 52.79, "unidad": "m²"},
    {"label": "Granito", "precio": 84.67, "unidad": "m²"},
]
REPOSICION_CALZADA = {
    "Reposición adoquín": {"precio": 35.23, "unidad": "m²"},
    "Capa de rodadura": {"precio": 139.64, "unidad": "m³"},
    "Base de pavimento": {"precio": 117.34, "unidad": "m³"},
    "Hormigón": {"precio": 117.18, "unidad": "m³"},
    "Base granular": {"precio": 23.46, "unidad": "m³"},
    "Demolición arqueta de imbornal": {"precio": 72.70, "unidad": "ud"},
    "Demolición imbornal y tubería": {"precio": 49.17, "unidad": "ud"},
}

# Saneamiento / elementos del CSV
POZOS = [
    {"label": "Ladrillo P < 2,5 m", "precio": 1043.82, "unidad": "ud"},
    {"label": "Ladrillo P < 3,5 m", "precio": 1273.56, "unidad": "ud"},
    {"label": "Ladrillo P < 5 m", "precio": 1714.04, "unidad": "ud"},
    {"label": "Ladrillo P > 5 m", "precio": 2455.28, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 500", "precio": 1071.83, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 500", "precio": 1291.82, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 500", "precio": 1555.71, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 600", "precio": 1124.58, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 600", "precio": 1344.55, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 600", "precio": 1608.48, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 800", "precio": 1651.37, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 800", "precio": 1406.96, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 800", "precio": 1651.37, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 1000", "precio": 2344.91, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 1000", "precio": 2564.87, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 1000", "precio": 2841.49, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 1200", "precio": 2491.87, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 1200", "precio": 2701.83, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 1200", "precio": 2978.75, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 1500", "precio": 3238.86, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 1500", "precio": 3463.31, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 1500", "precio": 3739.16, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 1600", "precio": 3404.77, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 1600", "precio": 3629.22, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 1600", "precio": 3905.07, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 1800", "precio": 3879.69, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 1800", "precio": 4104.15, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 1800", "precio": 4379.98, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 2000", "precio": 4168.38, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 2000", "precio": 4382.97, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 2000", "precio": 4684.38, "unidad": "ud"},
    {"label": "Prefabricado P < 2,5 m · Tub < 2500", "precio": 5199.18, "unidad": "ud"},
    {"label": "Prefabricado P < 3,5 m · Tub < 2500", "precio": 5439.21, "unidad": "ud"},
    {"label": "Prefabricado P > 3,5 m · Tub < 2500", "precio": 5715.51, "unidad": "ud"},
    {"label": "Acondicionamiento de pozo", "precio": 222.88, "unidad": "ud"},
    {"label": "Anulación de pozo", "precio": 545.82, "unidad": "ud"},
    {"label": "Demolición de pozo", "precio": 44.72, "unidad": "ud"},
]
IMBORNALES = [
    {"label": "Rejilla con clapeta", "precio": 547.98, "unidad": "ud"},
    {"label": "Rejilla sin clapeta", "precio": 547.98, "unidad": "ud"},
    {"label": "Buzón con clapeta", "precio": 872.03, "unidad": "ud"},
    {"label": "Buzón sin clapeta", "precio": 802.03, "unidad": "ud"},
]
MARCOS = [
    {"label": "Marco superficie hasta 10 m²", "precio": 1683.64, "unidad": "ud"},
    {"label": "Marco superficie hasta 20 m²", "precio": 3498.89, "unidad": "ud"},
    {"label": "Marco superficie hasta 30 m²", "precio": 4446.06, "unidad": "ud"},
    {"label": "Marco superficie hasta 35 m²", "precio": 5127.49, "unidad": "ud"},
]
ACOMETIDAS = [
    {"label": "PVC - Adaptación", "precio": 446.64, "unidad": "ud"},
    {"label": "PVC - Reposición < 6 m", "precio": 885.12, "unidad": "ud"},
    {"label": "PVC - Reposición > 6 m", "precio": 1278.78, "unidad": "ud"},
    {"label": "GRES - Adaptación", "precio": 485.43, "unidad": "ud"},
    {"label": "GRES - Reposición < 6 m", "precio": 1231.79, "unidad": "ud"},
    {"label": "GRES - Reposición > 6 m", "precio": 1759.63, "unidad": "ud"},
]
MATERIALES_POZO_TAPA = [{"label": "Tapa de pozo de registro", "precio": 160.37, "unidad": "ud"}]
MATERIALES_POZO_PATE = [{"label": "Pate para pozos", "precio": 1.94, "unidad": "ud"}]

# Parámetros visibles en base / pliego
SERVICIOS_AFECTADOS = [
    {"label": "Poco", "pct": 0.01},
    {"label": "Normal", "pct": 0.03},
    {"label": "Mucho", "pct": 0.05},
]
PCT_SS_CSV = 0.03
IMPORTE_SS_DEFAULT = 8400.00
IMPORTE_GA_DEFAULT = 12225.00
