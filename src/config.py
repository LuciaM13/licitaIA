"""
Modelo de datos: parámetros que el usuario introduce en Streamlit.

Todos los valores por defecto numéricos y de configuración se leen de la
BD SQLite (data/precios.db vía src/db.py), editables desde la página de
administración. Este módulo solo contiene el dataclass ParametrosProyecto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParametrosProyecto:
    # --- ABASTECIMIENTO (ABA) ------------------------------------------------
    aba_item: dict[str, Any] | None = None
    aba_longitud_m: float = 0.0
    aba_profundidad_m: float = 1.20

    # --- SANEAMIENTO (SAN) ---------------------------------------------------
    san_item: dict[str, Any] | None = None
    san_longitud_m: float = 0.0
    san_profundidad_m: float = 1.60

    # --- PAVIMENTACIÓN ABA ---------------------------------------------------
    pav_aba_acerado_m2: float = 0.0
    pav_aba_acerado_item: dict[str, Any] = field(default_factory=dict)
    pav_aba_bordillo_m: float = 0.0
    pav_aba_bordillo_item: dict[str, Any] = field(default_factory=dict)

    # --- PAVIMENTACIÓN SAN ---------------------------------------------------
    pav_san_calzada_m2: float = 0.0
    pav_san_calzada_item: dict[str, Any] = field(default_factory=dict)
    pav_san_acera_m2: float = 0.0
    pav_san_acera_item: dict[str, Any] = field(default_factory=dict)

    # --- ACOMETIDAS ----------------------------------------------------------
    acometidas_aba_n: int = 0
    acometidas_san_n: int = 0

    # --- PARÁMETROS DE OBRA ---------------------------------------------------
    pct_manual: float = 0.30
    conduccion_provisional_m: float = 0.0
    instalacion_valvuleria: str = "enterrada"

    # --- SEGURIDAD Y GESTIÓN (% del subtotal de obra) -------------------------
    pct_seguridad: float = 0.0
    pct_gestion: float = 0.0

    # --- SUB-BASE PAVIMENTACION -----------------------------------------------
    subbase_aba_item: dict[str, Any] | None = None
    subbase_aba_espesor_m: float = 0.0
    subbase_san_item: dict[str, Any] | None = None
    subbase_san_espesor_m: float = 0.0

    # --- OTROS ----------------------------------------------------------------
    espesor_pavimento_m: float = 0.0   # Para canon vertido mixto (RCD demolición)
    pct_servicios_afectados: float = 0.0  # % sobre PEM para servicios afectados

    # --- DESMONTAJE TUBERÍA (ABA) ------------------------------------------
    # "none" = no hay desmontaje, "normal" = tubería normal, "fibrocemento" = FC
    desmontaje_tipo: str = "none"

    # --- POZOS EXISTENTES (ABA/SAN) -----------------------------------------
    # "none" = no hay, "demolicion" = se demole, "anulacion" = se anula
    pozos_existentes_aba: str = "none"
    pozos_existentes_san: str = "none"

    # --- IMBORNALES (SAN) ---------------------------------------------------
    # "none" = no hay, "adaptacion" = adaptación, "nuevo" = nuevo (tipo según DB)
    imbornales_tipo: str = "none"
    imbornales_nuevo_label: str = ""  # label del imbornal nuevo seleccionado
