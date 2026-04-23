"""Helpers UI para selectboxes de material de demolición.

Las opciones se derivan del catálogo BD (tabla `demolicion`) en lugar de
constantes hardcodeadas. Así, si el admin añade una variante vía UI, el
selector la recoge automáticamente sin tocar código.
"""

from __future__ import annotations

from src.presupuesto.materiales import materiales_demo_disponibles


_ETIQUETAS_MATERIAL = {
    "granitico": "Granítico",
    "hidraulico": "Hidráulico",
    "adoquin": "Adoquín",
    "aglomerado": "Aglomerado",
    "hormigon": "Hormigón",
    "hormigon_acerado": "Hormigón (acerado)",
    "losa_hidraulica": "Losa hidráulica",
    "losa_terrazo": "Losa terrazo",
    "generico": "Genérico",
}


def format_material(material: str) -> str:
    """Devuelve la etiqueta presentable del material para la UI."""
    return _ETIQUETAS_MATERIAL.get(material, material.replace("_", " ").capitalize())


def opciones_material(
    precios: dict, clave_catalogo: str, tipo: str, unidad: str,
) -> list[str]:
    """Lista materiales disponibles para poblar un selectbox.

    - ``clave_catalogo``: 'demolicion_aba' | 'demolicion_san'.
    - ``tipo``: 'bordillo' | 'acerado' | 'calzada' (se compara contra label).
    - ``unidad``: 'm' | 'm2'.

    Excluye 'generico' porque no existe en el Excel oficial y su uso induce
    drift vs EMASESA (documentado en AGENTS.md § Demolición).
    """
    cat = precios.get(clave_catalogo, [])
    materiales = materiales_demo_disponibles(cat, tipo, unidad)
    return [m for m in materiales if m != "generico"]
