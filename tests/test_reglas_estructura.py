"""Tests que verifican el nuevo layout de ``src/sistema_experto/`` tras el Paso 3 del refactor.

Cubre:
  - Los tres módulos nuevos (``decisor``, ``motor_clips``, ``explicaciones``)
    exponen sus funciones públicas bajo los nombres honestos.
  - ``motor_clips`` es el único módulo bajo ``src/sistema_experto/`` que importa CLIPS;
    ``decisor`` y ``explicaciones`` son Python puro.

Objetivo del paso: alinear código ↔ memoria del TFG. La memoria declara que
CLIPS emite únicamente alertas técnicas; la selección de material es
determinista. Esta separación debe ser visible al abrir la carpeta.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from src.sistema_experto.reglas_clips import RULES
from src.sistema_experto.trazabilidad import RULE_PROVENANCE


_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Nuevos módulos exponen los nombres honestos
# ---------------------------------------------------------------------------

def test_decisor_expone_resolver_decisiones():
    from src.sistema_experto.decisor import resolver_decisiones
    assert callable(resolver_decisiones)


def test_motor_clips_expone_generar_alertas_tecnicas():
    from src.sistema_experto.motor_clips import generar_alertas_tecnicas
    assert callable(generar_alertas_tecnicas)


def test_explicaciones_expone_generar_explicaciones():
    from src.sistema_experto.explicaciones import generar_explicaciones
    assert callable(generar_explicaciones)


# ---------------------------------------------------------------------------
# Separación CLIPS-only: solo motor_clips importa ``clips``
# ---------------------------------------------------------------------------

def _importa_modulo(fichero: Path, modulo: str) -> bool:
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name.split(".")[0] == modulo:
                    return True
        elif isinstance(nodo, ast.ImportFrom):
            if (nodo.module or "").split(".")[0] == modulo:
                return True
    return False


def test_decisor_no_importa_clips():
    fichero = _REPO_ROOT / "src" / "sistema_experto" / "decisor.py"
    assert not _importa_modulo(fichero, "clips"), (
        "decisor.py es lógica determinista Python; no debe importar CLIPS. "
        "Si necesitas inferencia CLIPS, úsala en motor_clips.py."
    )


def test_explicaciones_no_importa_clips():
    fichero = _REPO_ROOT / "src" / "sistema_experto" / "explicaciones.py"
    assert not _importa_modulo(fichero, "clips"), (
        "explicaciones.py es formateo de cadenas; no debe importar CLIPS."
    )


def test_motor_clips_si_importa_clips():
    """Verificación positiva: motor_clips.py SÍ usa CLIPS. Esa es su razón de ser."""
    fichero = _REPO_ROOT / "src" / "sistema_experto" / "motor_clips.py"
    assert _importa_modulo(fichero, "clips"), (
        "motor_clips.py debe importar clips; es el motor CLIPS del sistema."
    )


# ---------------------------------------------------------------------------
# SE-05: cada defrule en templates.py tiene entrada en RULE_PROVENANCE
# ---------------------------------------------------------------------------

_PAT_ID = re.compile(r'\(id\s+"([^"]+)"\)')
_PAT_RID = re.compile(r'\(rule_id\s+"([^"]+)"\)')


def _ids_referenciados_en_reglas() -> set[str]:
    """Extrae ids/rule_ids de RULES, excluyendo comentarios CLIPS (lineas que empiezan con ';')."""
    ids: set[str] = set()
    for linea in RULES.splitlines():
        if linea.strip().startswith(";"):
            continue
        ids.update(_PAT_ID.findall(linea))
        ids.update(_PAT_RID.findall(linea))
    return ids


def test_cada_regla_tiene_provenance():
    """SE-05: cada (id "X")/(rule_id "X") referenciado en templates.py tiene entrada en RULE_PROVENANCE."""
    ids = _ids_referenciados_en_reglas()
    faltan = ids - set(RULE_PROVENANCE.keys())
    assert not faltan, (
        f"Reglas sin entrada en RULE_PROVENANCE: {sorted(faltan)}. "
        "Cada defrule en src/sistema_experto/reglas_clips.py debe tener provenance "
        "estatica en src/sistema_experto/trazabilidad.py:RULE_PROVENANCE."
    )


def test_provenance_no_tiene_ids_huerfanos():
    """Inverso de SE-05: RULE_PROVENANCE no contiene claves no referenciadas en templates.py.

    Si un id existe en RULE_PROVENANCE pero ya no aparece en RULES,
    es una entrada muerta tras una refactorizacion. Marca para limpiar.
    """
    ids = _ids_referenciados_en_reglas()
    sobran = set(RULE_PROVENANCE.keys()) - ids
    assert not sobran, (
        f"Entradas en RULE_PROVENANCE sin defrule correspondiente: {sorted(sobran)}. "
        "Eliminar dead entries o restaurar la regla en templates.py."
    )


def test_provenance_tiene_al_menos_17_entradas():
    """SE-05: el conteo de provenance no debe disminuir.

    Minimo actual: 16 alertas base + 1 meta = 17 (tras retirar R10/R11/R14
    como axiomas inalcanzables y `alerta-coordinacion-servicios` por decision
    de diseno, ya que su consigna se solapaba con `trafico-sin-conduccion`).
    Todas tipo 'alerta', capa 3. Las pruebas de bidireccionalidad ya
    garantizan sincronia exacta con `defrule`; este test solo evita
    regresiones por borrado accidental.
    """
    assert len(RULE_PROVENANCE) >= 17, (
        f"RULE_PROVENANCE tiene {len(RULE_PROVENANCE)} entradas; se esperan >= 17. "
        "Si una regla desaparece, actualizar este invariante explicitamente."
    )
