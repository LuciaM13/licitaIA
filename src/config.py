"""
Este módulo centraliza TODOS los valores por defecto y constantes que necesita
la aplicación. Así se facilita el mantenimiento: si cambia un valor de obra, solo hay que
tocarlo aquí.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULTS BACKEND — Motor de cálculo
# ═══════════════════════════════════════════════════════════════════════════════
# Estos valores los usa el motor de cálculo (backend) para determinar
# dimensiones de zanja, espesores de relleno y tipos de acometida.
# No se muestran directamente en la UI; alimentan las fórmulas internas.

# ─── Umbrales ─────────────────────────────────────────────────────────────
# A partir de esta profundidad de excavación (en metros) se aplican
# condiciones especiales (p.ej. entibación obligatoria, sobrecoste, etc.)
PROFUNDIDAD_EXCAVACION_UMBRAL_M = 2.5

# ─── Anchos de zanja por diámetro (m) ────────────────────────────────────
# Diccionarios que mapean el diámetro nominal de la tubería (en mm)
# al ancho mínimo de zanja requerido (en metros).
# Se usan para calcular el volumen de excavación y relleno.

# Anchos de zanja para tuberías de ABASTECIMIENTO (agua potable).
ANCHO_ZANJA_ABA = {
    80: 0.60, 90: 0.60, 100: 0.65, 110: 0.65,
    150: 0.75, 160: 0.80, 200: 0.90,
}

# Anchos de zanja para tuberías de SANEAMIENTO (aguas residuales/pluviales).
ANCHO_ZANJA_SAN = {
    300: 0.90, 315: 0.95, 400: 1.00, 500: 1.10,
    600: 1.20, 800: 1.40, 1000: 1.60, 1200: 1.80,
}


# ─── Espesores fijos (m) ─────────────────────────────────────────────────
# Capas de material que se colocan dentro de la zanja alrededor de la tubería.

ESPESOR_ARENA = 0.10          # Cama de arena bajo la tubería (asiento)
ESPESOR_RELLENO_ABA = 0.30   # Relleno sobre tubería en abastecimiento
ESPESOR_RELLENO_SAN = 0.40   # Relleno sobre tubería en saneamiento






#................................................................................

# DEFAULTS FRONTEND — Valores iniciales de la UI (Streamlit)

# Estos valores rellenan los campos del formulario de Streamlit cuando el
# usuario abre la aplicación por primera vez. Son orientativos y editables.

# ─── Supuestos por defecto ───────────────────────────────────────────────

# Tipos de acometida preseleccionados. Una acometida es la conexión entre
# la red general y cada vivienda/parcela.
ACOMETIDA_ABA = "Con demolición (<6m)"   
ACOMETIDA_SAN = "Adaptación gres"        

# Tuberías — longitud y profundidad por defecto
ABA_LONGITUD_M = 100.0       # Metros lineales de tubería de abastecimiento
ABA_PROFUNDIDAD_M = 1.20     # Profundidad de zanja para abastecimiento (m)
SAN_LONGITUD_M = 132.0       # Metros lineales de tubería de saneamiento
SAN_PROFUNDIDAD_M = 1.60     # Profundidad de zanja para saneamiento (m)

# Pavimentación ABA — reposición de superficie tras la obra de abastecimiento
PAV_ABA_ACERADO_M2 = 390.0   # Superficie de acera a reponer (m²)
PAV_ABA_BORDILLO_M = 310.0   # Metros lineales de bordillo a reponer

# Pavimentación SAN — reposición de superficie tras la obra de saneamiento
PAV_SAN_CALZADA_M2 = 760.0   # Superficie de calzada a reponer (m²)
PAV_SAN_ACERA_M2 = 390.0     # Superficie de acera a reponer (m²)

# Acometidas — número total de conexiones domiciliarias
ACOMETIDAS_N = 26

# Seguridad y Gestión — partidas de importe fijo (€) que se suman al
# presupuesto independientemente de las mediciones de obra.
IMPORTE_SEGURIDAD = 5000.0   # Plan de seguridad y salud
IMPORTE_GESTION = 5000.0     # Gestión de residuos de construcción


# ═══════════════════════════════════════════════════════════════════════════════
# MODELO DE DATOS — Parámetros que el usuario introduce en Streamlit
# ══════════════════════════════════════════════════════════════════════════════

#tenemos una clase paara forzar el tipo de dato
@dataclass
class ParametrosProyecto:
    # --- ABASTECIMIENTO (ABA) ------------------------------------------------
    # Si aba_item es None, el proyecto no incluye abastecimiento.
    aba_item: Optional[dict[str, Any]] = None       # Item del cuadro de precios seleccionado
    aba_longitud_m: float = 0.0                     # Longitud de tubería (m)
    aba_profundidad_m: float = ABA_PROFUNDIDAD_M    # Profundidad de excavación (m)

    # --- SANEAMIENTO (SAN) ---------------------------------------------------
    # Si san_item es None, el proyecto no incluye saneamiento.
    san_item: Optional[dict[str, Any]] = None       # Item del cuadro de precios seleccionado
    san_longitud_m: float = 0.0                     # Longitud de tubería (m)
    san_profundidad_m: float = SAN_PROFUNDIDAD_M    # Profundidad de excavación (m)

    # --- PAVIMENTACIÓN ABA ---------------------------------------------------
    # Superficie y longitud de reposición de pavimento tras obra de abastecimiento.
    pav_aba_acerado_m2: float = 0.0                 # m² de acera a reponer
    pav_aba_acerado_item: dict[str, Any] = field(default_factory=dict)   # Item de precio
    pav_aba_bordillo_m: float = 0.0                 # Metros lineales de bordillo
    pav_aba_bordillo_item: dict[str, Any] = field(default_factory=dict)  # Item de precio

    # --- PAVIMENTACIÓN SAN ---------------------------------------------------
    # Superficie de reposición de pavimento tras obra de saneamiento.
    pav_san_calzada_m2: float = 0.0                 # m² de calzada a reponer
    pav_san_calzada_item: dict[str, Any] = field(default_factory=dict)   # Item de precio
    pav_san_acera_m2: float = 0.0                   # m² de acera a reponer
    pav_san_acera_item: dict[str, Any] = field(default_factory=dict)     # Item de precio

    # --- ACOMETIDAS ----------------------------------------------------------
    # Número de conexiones domiciliarias (de la red general a cada parcela).
    acometidas_aba_n: int = 0    # Nº acometidas de abastecimiento
    acometidas_san_n: int = 0    # Nº acometidas de saneamiento

    # --- SEGURIDAD Y GESTIÓN (importes fijos en €) ---------------------------
    # Partidas que no dependen de mediciones, se añaden como suma alzada.
    importe_seguridad: float = 0.0   # Plan de seguridad y salud (€)
    importe_gestion: float = 0.0     # Gestión de residuos (€)
