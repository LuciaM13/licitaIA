"""Constantes derivadas del schema real (BLOCK 3 fix del plan inline).

Mapeo target -> (tabla, red), contexto de demolicion por target y opciones
de material. Si cambia ``src/almacenamiento/schema.py`` (NOT NULL en
``red``, nuevos materiales canonicos), aqui es donde se ajusta.
"""

from __future__ import annotations


# Mapeo target -> (tabla, red). El alta inline esta restringida a 10
# variantes de catalogo (pediente expreso del usuario): tuberia ABA/SAN,
# acerado ABA/SAN, bordillo (ABA), calzada (SAN) y las 4 demoliciones de
# pavimento ABA acerado/bordillo y SAN calzada/acerado. La regla de `red`
# la fija el schema: red NOT NULL en {tuberias, acerados, demolicion},
# nullable en {bordillos, calzadas}.
_TARGET_A_TABLA: dict[str, tuple[str, str | None]] = {
    "tuberias_aba":            ("tuberias",   "ABA"),
    "tuberias_san":            ("tuberias",   "SAN"),
    "acerados_aba":            ("acerados",   "ABA"),
    "acerados_san":            ("acerados",   "SAN"),
    "bordillos":               ("bordillos",  None),
    "calzadas":                ("calzadas",   None),
    "demolicion_aba_acerado":  ("demolicion", "ABA"),
    "demolicion_aba_bordillo": ("demolicion", "ABA"),
    "demolicion_san_acerado":  ("demolicion", "SAN"),
    "demolicion_san_calzada":  ("demolicion", "SAN"),
}


# Contexto del form de demolicion por target. Cada selectbox de la calculadora
# vive en un contexto fijo (red x tipo de elemento x unidad). El form pre-rellena
# `unidad` y `tipo` desde aqui, asi el usuario solo decide `material`/`label`/`precio`.
_DEMOLICION_CTX: dict[str, dict[str, str]] = {
    "demolicion_aba_acerado":  {"tipo": "acerado",  "unidad": "m2"},
    "demolicion_aba_bordillo": {"tipo": "bordillo", "unidad": "m"},
    "demolicion_san_acerado":  {"tipo": "acerado",  "unidad": "m2"},
    "demolicion_san_calzada":  {"tipo": "calzada",  "unidad": "m2"},
}


# Materiales de demolicion que la UI ofrece (excluye 'generico', mismo set que
# `_MATERIALES_DEMOLICION` del use case). `format_material` produce las
# etiquetas legibles (Granitico, Hidraulico, Adoquin, ...).
_MATERIALES_DEMOLICION_OPCIONES: list[str] = [
    "granitico", "hidraulico", "adoquin", "aglomerado", "hormigon",
    "hormigon_acerado", "losa_hidraulica", "losa_terrazo",
]
