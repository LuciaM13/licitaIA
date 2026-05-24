"""Utilidades de conversión céntimos↔EUR y mapa de campos monetarios.

Convención storage (desde Migración 13):
  - BD almacena precios como INTEGER céntimos (ej. 12.96 € → 1296).
  - Al leer se divide por 100 → floats €.
  - Al guardar se multiplica por 100 con round() → INTEGER céntimos.
  - El resto del código (dominio, UI) opera en floats €.

Módulo neutral (sin dependencias internas) compartido por
``src.catalogo.repositorio`` y ``src.catalogo.editor``,
para evitar que el use case dependa de símbolos privados de un módulo de
infraestructura concreto.
"""

from __future__ import annotations


# Campos de precio monetario que se almacenan como INTEGER céntimos en BD.
# Se dividen por 100 al leer, se multiplican por 100 con round() al escribir.
_CAMPOS_MONETARIOS = {
    "tuberias": ("precio_m", "precio_material_m"),
    "valvuleria": ("precio", "precio_material"),
    "pozos": ("precio", "precio_tapa", "precio_tapa_material", "precio_pate_material"),
    "acerados": ("precio",),
    "bordillos": ("precio",),
    "calzadas": ("precio",),
    "demolicion": ("precio",),
    "entibacion": ("precio_m2",),
    "acometidas": ("precio",),
    "subbases": ("precio_m3",),
    "desmontaje": ("precio_m",),
    "imbornales": ("precio",),
    "pozos_existentes_precios": ("precio",),
}


def _cents_a_eur(val):
    """Convierte INTEGER céntimos → float €. None → None."""
    return val / 100.0 if val is not None else None


def _eur_a_cents(val):
    """Convierte float € → INTEGER céntimos con redondeo bancario (round())."""
    return round(float(val) * 100) if val is not None else 0


def _convertir_filas(filas, campos):
    """Aplica _cents_a_eur a los campos indicados en cada fila (list of dicts)."""
    for fila in filas:
        for campo in campos:
            if campo in fila:
                fila[campo] = _cents_a_eur(fila[campo])
    return filas
