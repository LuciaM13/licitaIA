"""Normalizacion de inputs y constantes de dominio.

Funciones puras para normalizar tipos, redes e instalaciones,
mas la tabla de factores de piezas especiales por tipo de tuberia.
"""

from __future__ import annotations

from typing import Any

# Factor piezas especiales por tipo de tuberia.
# Fuente: src/db.py _migrar_columnas() y spec del prompt.
FACTORES_PIEZAS: dict[str, float] = {
    "FD": 1.2,
    "PE-100": 1.2,
    "PE-80": 1.2,
    "Gres": 1.35,
    "PVC": 1.2,
    "Hormigon": 1.0,     # Normalizado (sin tilde)
    "Hormigón": 1.0,     # Con tilde, por si llega asi
    "HA": 1.0,
    "HA+PE80": 1.4,
}

# Valor sentinel para representar NULL/None en campos STRING de CLIPS.
NULL_SENTINEL = "*"


def normalizar_tipo(tipo: str) -> str:
    """Normaliza el tipo de tuberia: trim + preserva mayusculas originales."""
    return tipo.strip()


def normalizar_red(red: str) -> str:
    """Normaliza la red: trim + mayusculas."""
    return red.strip().upper()


def normalizar_instalacion(inst: str) -> str:
    """Normaliza el tipo de instalacion: trim + minusculas."""
    return inst.strip().lower()


def null_to_sentinel(value: Any) -> str:
    """Convierte None a sentinel para campos STRING de CLIPS."""
    if value is None:
        return NULL_SENTINEL
    return str(value).strip()
