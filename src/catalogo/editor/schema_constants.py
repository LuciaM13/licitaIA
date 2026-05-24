"""Constantes derivadas del schema real de SQLite.

Fuente: ``src/almacenamiento/schema.py``. Estas tuplas/sets las usa
``inline_create`` para validar antes del INSERT (BLOCK 2 / BLOCK 3 fix
del plan 03-01 / 03-03).
"""

from __future__ import annotations

from typing import Mapping


# Tablas cuyo schema declara `red` como NOT NULL: el use case rechaza
# `red=None` para estas y rechaza `red != None` para las demás (las que
# no tienen columna `red` o la tienen como nullable y aún no la modelamos).
_TABLAS_CON_RED: frozenset[str] = frozenset({
    "tuberias",                  # red TEXT NOT NULL
    "acerados",                  # red TEXT NOT NULL
    "acometidas",                # red TEXT NOT NULL
    "demolicion",                # red TEXT NOT NULL
    "pozos_existentes_precios",  # red TEXT NOT NULL
})

# Clave de unicidad lógica por catálogo, derivada del schema real. El
# duplicado se chequea con SELECT 1 ... WHERE <clave> antes del INSERT.
# Tupla vacía -> sin chequeo (e.g. pozos: el schema no declara UNIQUE).
_CLAVES_UNICIDAD: Mapping[str, tuple[str, ...]] = {
    "tuberias":                 ("red", "label"),
    "acerados":                 ("red", "label"),
    "acometidas":               ("red", "tipo"),    # acometidas NO usa label
    "valvuleria":               ("label",),
    "bordillos":                ("label",),
    "calzadas":                 ("label",),
    "imbornales":               ("label",),
    "pozos":                    (),                  # sin UNIQUE; sin chequeo en use case
    "demolicion":               ("red", "unidad", "material"),
    "subbases":                 ("label",),
    "desmontaje":               ("label",),
    "pozos_existentes_precios": ("red", "accion"),
}

# Materiales canónicos aceptados para la tabla `demolicion`. 'generico' queda
# fuera porque no existe en el Excel oficial EMASESA y su uso induce drift
# (memoria de proyecto: AGENTS.md § Demolición).
_MATERIALES_DEMOLICION: frozenset[str] = frozenset({
    "granitico", "hidraulico", "adoquin", "aglomerado", "hormigon",
    "hormigon_acerado", "losa_hidraulica", "losa_terrazo",
})

# Acciones aceptadas para la tabla `pozos_existentes_precios` (CHECK schema).
_ACCIONES_POZOS_EXISTENTES: frozenset[str] = frozenset({"demolicion", "anulacion"})
