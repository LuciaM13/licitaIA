"""
Modelo de datos: parámetros que el usuario introduce en la UI.

ParametrosProyecto es un dataclass con todos los inputs del formulario.
No contiene lógica de cálculo ni referencias a Streamlit, SQLite o CLIPS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParametrosProyecto:
    # ── ABASTECIMIENTO (ABA) ─────────────────────────────────────────────────
    aba_item: dict[str, Any] | None = None   # Item del catálogo (tubería seleccionada)
    aba_longitud_m: float = 0.0
    aba_profundidad_m: float = 1.20

    # ── SANEAMIENTO (SAN) ────────────────────────────────────────────────────
    san_item: dict[str, Any] | None = None
    san_longitud_m: float = 0.0
    san_profundidad_m: float = 1.60

    # ── PAVIMENTACIÓN ABA ────────────────────────────────────────────────────
    pav_aba_acerado_m2: float = 0.0
    pav_aba_acerado_item: dict[str, Any] = field(default_factory=dict)
    pav_aba_bordillo_m: float = 0.0
    pav_aba_bordillo_item: dict[str, Any] = field(default_factory=dict)

    # ── PAVIMENTACIÓN SAN ────────────────────────────────────────────────────
    pav_san_calzada_m2: float = 0.0
    pav_san_calzada_item: dict[str, Any] = field(default_factory=dict)
    pav_san_acera_m2: float = 0.0
    pav_san_acera_item: dict[str, Any] = field(default_factory=dict)

    # ── ACOMETIDAS ───────────────────────────────────────────────────────────
    acometidas_aba_n: int = 0
    acometidas_san_n: int = 0

    # ── PARÁMETROS DE OBRA ───────────────────────────────────────────────────
    pct_manual: float = 0.30              # Porcentaje de excavación manual (0-1)
    instalacion_valvuleria: str = "enterrada"  # "enterrada" o "pozo"
    conduccion_provisional_m: float = 0.0
    espesor_pavimento_m: float = 0.0     # Para cálculo de canon RCD

    # ── SEGURIDAD Y GESTIÓN AMBIENTAL ────────────────────────────────────────
    pct_seguridad: float = 0.0           # % sobre subtotal de obra (0-1)
    pct_gestion: float = 0.0

    # ── SERVICIOS AFECTADOS ──────────────────────────────────────────────────
    pct_servicios_afectados: float = 0.0  # % sobre PEM

    # ── SUB-BASE DE PAVIMENTACIÓN ────────────────────────────────────────────
    subbase_aba_item: dict[str, Any] | None = None
    subbase_aba_espesor_m: float = 0.0
    subbase_san_item: dict[str, Any] | None = None
    subbase_san_espesor_m: float = 0.0

    # ── DESMONTAJE TUBERÍA EXISTENTE (ABA) ───────────────────────────────────
    # "none" | "normal" | "fibrocemento"
    desmontaje_tipo: str = "none"

    # ── POZOS EXISTENTES ─────────────────────────────────────────────────────
    # "none" | "demolicion" | "anulacion"
    pozos_existentes_aba: str = "none"
    pozos_existentes_san: str = "none"

    # ── IMBORNALES (SAN) ─────────────────────────────────────────────────────
    # "none" | "adaptacion" | "nuevo"
    imbornales_tipo: str = "none"
    imbornales_nuevo_label: str = ""

    # ── HELPERS ──────────────────────────────────────────────────────────────

    @property
    def aba_activa(self) -> bool:
        return self.aba_item is not None and self.aba_longitud_m > 0

    @property
    def san_activa(self) -> bool:
        return self.san_item is not None and self.san_longitud_m > 0

    @property
    def aba_diametro_mm(self) -> int:
        return int(self.aba_item["diametro_mm"]) if self.aba_item else 0

    @property
    def san_diametro_mm(self) -> int:
        return int(self.san_item["diametro_mm"]) if self.san_item else 0

    @property
    def aba_tipo(self) -> str:
        return self.aba_item["tipo"] if self.aba_item else ""

    @property
    def san_tipo(self) -> str:
        return self.san_item["tipo"] if self.san_item else ""
