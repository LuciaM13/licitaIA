"""Fixtures compartidos para pytest."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def precios():
    """Carga precios desde SQLite local (mismo camino que verify_clips.py).

    No aplica _aplicar_ci — replica exactamente el path de verify_clips.py
    linea 283: precios = cargar_todo().
    """
    from src.db import cargar_todo, DB_PATH

    if not Path(DB_PATH).exists():
        pytest.skip("data/precios.db no presente (no versionado)")

    return cargar_todo()
