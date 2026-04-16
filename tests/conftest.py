"""Setup compartido para tests de LicitaIA.

pytest descubre este fichero automáticamente y ejecuta el código de nivel
de módulo antes de cualquier test. Aquí fijamos el working directory e
inicializamos la BD.

Ejecutar:  pytest tests/ -v
Entorno:   conda activate licitaia
"""

from __future__ import annotations

import os
import sys

# Fijar working directory a la raiz del proyecto (necesario para imports relativos)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_project_root)

# Añadir tests/ al path para que helpers.py sea importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.infraestructura.db import init_db  # noqa: E402

init_db()
