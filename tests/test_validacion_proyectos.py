"""Test unico de invariante de formato del parser BC3.

No es test de logica de negocio (cumple memoria "Solo AppTest"); valida que
el parser acepta el formato de columnas A-K documentado en
data/proyectos_individuales/README.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.validacion_proyectos.parser_excel import parsear_proyecto


FIXTURE = Path(__file__).parent / "fixtures" / "proyecto_sintetico_minimo.xlsx"


def test_parser_invariante_formato():
    proyecto = parsear_proyecto(FIXTURE)

    assert len(proyecto.partidas) == 2, (
        f"Se esperaban 2 partidas, se obtuvieron {len(proyecto.partidas)}: "
        f"{[p.codigo for p in proyecto.partidas]}"
    )
    assert proyecto.pem_total == pytest.approx(1234.56, abs=0.01)
    assert proyecto.capitulos_real["01"] == pytest.approx(1234.56, abs=0.01)

    codigos = sorted(p.codigo for p in proyecto.partidas)
    assert codigos == ["1.1.001", "1.1.002"]
