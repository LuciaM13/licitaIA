"""Fixtures compartidos para pytest."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def precios():
    """Carga precios desde SQLite con CI aplicado — igual que en producción.

    usa cargar_precios() (con _aplicar_ci) para que los tests
    trabajen exactamente con los mismos valores que la app real.
    """
    from src.infraestructura.db import DB_PATH
    from src.infraestructura.precios import cargar_precios

    if not Path(DB_PATH).exists():
        pytest.skip("data/precios.db no presente (no versionado)")

    return cargar_precios()
