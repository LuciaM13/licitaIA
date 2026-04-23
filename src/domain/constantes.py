"""Constantes de dominio. Ancla canónica de valores antes dispersos.

Este módulo es la fuente única de verdad para magnitudes que aparecían
duplicadas literalmente en varias ubicaciones (migraciones, documentación,
lógica de runtime). Antes del Paso 1 de la Fase 3 de refactor, el factor
del CI (``1.05``) vivía hardcodeado en ``precios.py``, en la migración
M15 y en el texto de ``AGENTS.md``, sin referencia cruzada que garantice
la coherencia.

Regla: cualquier valor numérico que sea "convencional de EMASESA" o
"invariante del sistema" debe estar aquí o justificar por qué no.
"""

from __future__ import annotations


PCT_CI_DEFAULT: float = 1.05
"""Factor de Costes Indirectos por defecto en EMASESA.

Invariante canónica: ``BD.precio × PCT_CI_DEFAULT = precio_oficial_Excel``.

Al cargar precios desde la BD, el runtime aplica este factor sobre una
copia local (ver ``_aplicar_ci`` en ``src.infraestructura.precios``). La
BD almacena siempre precios base **sin** CI. El licitador puede
sobrescribir el valor editando la clave ``pct_ci`` en ``config``; si no
hay valor, el dict devuelve 1.0 (neutral, no aplicar CI), no este default.
"""

TOLERANCIA_INVARIANTE_CI: float = 0.005
"""Tolerancia absoluta (en €) para la comparación BD × pct_ci = Excel.

Usado por migraciones (M4, M8, M9, M10, M11) en las guardas
``ABS(valor - drifted) < 0.005`` para decidir si un precio ya fue
corregido por el admin manualmente, y por el test
``tests/test_bd_invariante_ci.py``.
"""

NULL_SENTINEL: str = "*"
"""Marca de wildcard en catálogos y hechos CLIPS.

Concepto de dominio: "este campo aplica a cualquier valor". En los
catálogos JSON se usa también ``None``, pero los hechos CLIPS (hoy en
``src.reglas.templates``) requieren un string; por eso la constante es
``"*"``. Las funciones de elegibilidad aceptan ambas representaciones.
"""
