from __future__ import annotations

"""
datos.py
-------
Aquí se centralizan los datos "fijos" de la aplicación:
- porcentajes generales del presupuesto
- catálogos de tuberías y reurbanización
- precios unitarios de elementos singulares
- configuración de ejemplo del caso base EMASESA
- correspondencia aproximada entre el CSV de precios y el modelo simplificado

La idea es que, si mañana quieres cambiar precios o añadir nuevos diámetros,
solo tengas que tocar este archivo.
"""

# =========================
# Porcentajes generales
# =========================
# Estos porcentajes NO salen del CSV de precios unitarios.
# Se aplican en la parte final del presupuesto porque vienen del esquema del pliego.
PCT_GG = 0.13  # Gastos generales
PCT_BI = 0.06  # Beneficio industrial
PCT_IVA = 0.21  # IVA
PCT_CONTROL_CALIDAD = 0.01  # Referencia interna para análisis de rentabilidad


# =========================
# Configuración por defecto
# =========================
# Seguridad y Salud (SS) y Gestión Ambiental (GA) pueden meterse como:
# - importe fijo
# - porcentaje sobre el parcial antes de GG/BI/IVA
MODO_SS_DEFAULT = "fijo"
MODO_GA_DEFAULT = "fijo"
IMPORTE_SS_DEFAULT = 8400.00
IMPORTE_GA_DEFAULT = 12225.00
PCT_SS_DEFAULT = 0.11
PCT_GA_DEFAULT = 0.04

# Colchón comercial opcional. Sirve como margen interno adicional.
COLCHON_ACTIVO_DEFAULT = False
PCT_COLCHON_DEFAULT = 0.10


# =========================
# Catálogo de abastecimiento
# =========================
# Cada fila representa un tipo de red ABA que puede elegir el usuario.
# Los importes son simplificados y están pensados para una estimación rápida.
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


# =========================
# Catálogo de saneamiento
# =========================
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


# =========================
# Tipos de reurbanización
# =========================
# En vez de pedir todas las superficies y espesores reales, usamos factores.
# Es una simplificación útil para una primera estimación, pero no sustituye una medición.
TIPOS_REURB = [
    {"label": "Acerado hidráulico + calzada aglomerado", "factor_aba": 1.00, "factor_san": 1.00},
    {"label": "Acerado granítico + calzada aglomerado", "factor_aba": 1.20, "factor_san": 1.18},
    {"label": "Solo acerado hidráulico (sin calzada)", "factor_aba": 0.62, "factor_san": 0.60},
    {"label": "Solo acerado granítico (sin calzada)", "factor_aba": 0.72, "factor_san": 0.70},
    {"label": "Calzada aglomerado (sin acerado)", "factor_aba": 0.50, "factor_san": 0.48},
    {"label": "Terrizo / sin urbanizar", "factor_aba": 0.08, "factor_san": 0.06},
]


# =========================
# Elementos unitarios singulares
# =========================
# Son partidas que no dependen linealmente de los metros de tubería.
PRECIOS_UNIDADES = {
    "valvula_compuerta": 950.0,
    "toma_agua": 600.0,
    "conexion_saneamiento": 850.0,
    "pozo_registro": 1650.0,
    "imbornal": 720.0,
}


# =========================
# Caso base de referencia
# =========================
# Este preset solo sirve para rellenar la interfaz con un ejemplo parecido al pliego.
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
    "pct_colchon": PCT_COLCHON_DEFAULT,
}


# =========================
# Cobertura del CSV frente al modelo
# =========================
# El CSV contiene muchísimas líneas de precios unitarios. El modelo actual NO reproduce
# cada una de ellas, sino que las resume en unas pocas familias de coste.
# Este mapa se usa para explicar qué grupos del CSV están:
# - cubiertos directamente
# - cubiertos de forma parcial/indirecta
# - no cubiertos todavía
CSV_GROUP_STATUS = {
    "Acometidas": ("parcial", "Se modelan como unidades ABA/SAN, pero no se distinguen todos los tipos del CSV."),
    "Acerados": ("parcial", "Se absorben mediante el factor de reurbanización; no se desglosan todas las solerías."),
    "Demolición acerado": ("no", "No existe partida específica de demolición; hoy queda absorbida dentro de los precios simplificados."),
    "Demolición bordillo": ("no", "Falta un campo específico para bordillos demolidos."),
    "Demolición calzada": ("no", "No se desglosa por tipo de firme demolido."),
    "Excavación manual": ("no", "No se pide profundidad ni volumen, así que no puede calcularse explícitamente."),
    "Excavación mecánica": ("no", "No se pide profundidad ni volumen, así que no puede calcularse explícitamente."),
    "GRES": ("parcial", "Parte de estos precios se representa con el catálogo SAN, pero no todas las combinaciones ni accesorios."),
    "Imbornal nuevo": ("directo", "Se calcula como número de imbornales por precio unitario."),
    "MATERIALES": ("no", "Materiales auxiliares no están separados como partidas independientes."),
    "Montaje MARCOS": ("no", "No hay partida específica para marcos/tapas diferenciados."),
    "Montaje tubería HA+PE80": ("parcial", "Se aproxima mediante los catálogos ABA/SAN, pero no se separan todos los materiales y montajes."),
    "OTROS": ("no", "Varios conceptos auxiliares todavía no están modelados."),
    "Pav. Bordillos y corriente": ("parcial", "La reposición de pavimento va por factor global, no por bordillo lineal."),
    "Pozos de registro": ("directo", "Se calcula como número de pozos por precio unitario."),
    "Reposición calzada": ("parcial", "Se aproxima con el factor de reurbanización; no se distinguen capas ni espesores."),
    "Servicios Afectados": ("no", "No hay partidas para afecciones o desvíos de servicios."),
    "Suministro y montaje ovoide": ("no", "No existe aún catálogo específico para tubería ovoide."),
    "Suministro y montaje tubería PVC": ("parcial", "Existe catálogo SAN para algunos PVC, pero no todo el detalle del CSV."),
    "Suministro y montaje tubería gres": ("parcial", "Existe catálogo SAN para gres, pero resumido."),
    "Suministro y montaje tubería hormigón": ("parcial", "Existe catálogo SAN para HA, pero resumido."),
}
