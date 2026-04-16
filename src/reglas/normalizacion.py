"""
Normalización de inputs y constantes de dominio del motor de reglas.

Funciones puras: sin efectos laterales, sin dependencias externas.
"""

from __future__ import annotations

from typing import Any

from src.reglas.templates import NULL_SENTINEL

# Factor de piezas especiales por tipo de tubería.
# Fuente: spec EMASESA y comentarios del Excel de valoración.
FACTORES_PIEZAS: dict[str, float] = {
    "FD":        1.2,
    "PE-100":    1.2,
    "PE-80":     1.2,
    "Gres":      1.35,
    "PVC":       1.2,
    "Hormigon":  1.0,   # Sin tilde
    "Hormigón":  1.0,   # Con tilde
    "HA":        1.0,
    "HA+PE80":   1.4,
}


def normalizar_tipo(tipo: str) -> str:
    """Trim del tipo de tubería (preserva mayúsculas originales)."""
    return tipo.strip()


def normalizar_red(red: str) -> str:
    """Trim + mayúsculas."""
    return red.strip().upper()


def normalizar_instalacion(inst: str) -> str:
    """Trim + minúsculas."""
    return inst.strip().lower()


def null_a_sentinel(value: Any) -> str:
    """Convierte None al sentinel CLIPS para campos STRING nulos."""
    if value is None:
        return NULL_SENTINEL
    return str(value).strip()


def regla_pct_manual(profundidad: float) -> tuple[float, str]:
    """Calcula el % de excavación manual según la profundidad de la zanja.

    Rangos:
      ≤ 1,00 m → 10%
      1,00 – 2,00 m → 25%
      > 2,00 m → 40%

    Returns:
        (porcentaje 0-1, explicación breve)
    """
    p_fmt = f"{profundidad:.2f}".replace(".", ",")
    if profundidad <= 1.0:
        return 0.10, f"Prof. {p_fmt} m ≤ 1,00 m → 10%"
    elif profundidad <= 2.0:
        return 0.25, f"Prof. {p_fmt} m en rango 1–2 m → 25%"
    else:
        return 0.40, f"Prof. {p_fmt} m > 2,00 m → 40%"
