"""Carga, persistencia y formateo de precios."""

from __future__ import annotations

import json
from pathlib import Path

_RUTA = Path(__file__).resolve().parent.parent / "data" / "precios.json"


def cargar_precios() -> dict:
    return json.loads(_RUTA.read_text(encoding="utf-8"))


def guardar_precios(precios: dict) -> None:
    _RUTA.write_text(
        json.dumps(precios, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def euro(valor: float) -> str:
    """Formatea un número como moneda española (1.234,56 €)."""
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
