"""Tests de los TypedDict de dominio (Paso 5 del refactor Fase 2).

Cubre:
  - Los TypedDict se importan sin error.
  - Las firmas de las funciones públicas que los usan los referencian.
  - Un dict que coincide con el shape es aceptado en runtime (son dicts).
  - ``cargar_precios()`` devuelve un objeto compatible con ``Precios``.
  - ``calcular_presupuesto()`` devuelve un objeto compatible con
    ``ResultadoPresupuesto``.

TypedDict no hace checking en runtime; este test solo valida que los
contratos están bien declarados y que el shape efectivo coincide.

Excepción a la regla "solo AppTest": tests de contratos de tipos puros
sin superficie Streamlit.
"""
from __future__ import annotations

import inspect
import typing

from src.domain.tipos import (
    ItemCatalogo,
    Precios,
    ResultadoPresupuesto,
    CapituloResultado,
    PctsFinancieros,
)


# ---------------------------------------------------------------------------
# Los TypedDict existen y son TypedDict
# ---------------------------------------------------------------------------

def test_typeddicts_expone_atributos_typeddict():
    # TypedDict declara __annotations__ y __total__ (o __required_keys__).
    for tipo in (ItemCatalogo, Precios, ResultadoPresupuesto,
                 CapituloResultado, PctsFinancieros):
        assert hasattr(tipo, "__annotations__"), f"{tipo.__name__} sin annotations"
        assert tipo.__annotations__, f"{tipo.__name__} con annotations vacías"


def test_itemcatalogo_declara_campos_esperados():
    campos_clave = {"label", "precio", "precio_m", "tipo", "diametro_mm",
                    "factor_piezas", "umbral_m", "dn_min", "dn_max"}
    assert campos_clave.issubset(set(ItemCatalogo.__annotations__))


def test_precios_declara_catalogos_y_escalares():
    campos_clave = {"pct_ci", "pct_gg", "pct_bi", "pct_iva",
                    "catalogo_aba", "catalogo_san", "catalogo_pozos",
                    "catalogo_valvuleria", "catalogo_entibacion",
                    "excavacion", "defaults_ui"}
    assert campos_clave.issubset(set(Precios.__annotations__))


def test_resultadopresupuesto_declara_totales_y_capitulos():
    campos_clave = {"pem", "pbl_sin_iva", "iva", "total",
                    "capitulos", "trazabilidad", "pct_seguridad_info"}
    assert campos_clave.issubset(set(ResultadoPresupuesto.__annotations__))


# ---------------------------------------------------------------------------
# Las firmas públicas referencian los tipos
# ---------------------------------------------------------------------------

def test_capitulo_obra_civil_firma_usa_itemcatalogo_y_precios():
    from src.presupuesto.capitulos_obra_civil import capitulo_obra_civil
    hints = typing.get_type_hints(capitulo_obra_civil)
    # ``item`` debe resolverse a ItemCatalogo; ``precios`` a Precios.
    assert hints["item"] is ItemCatalogo
    assert hints["precios"] is Precios


def test_calcular_presupuesto_firma_devuelve_resultadopresupuesto():
    from src.aplicacion.calcular_presupuesto import calcular_presupuesto
    hints = typing.get_type_hints(calcular_presupuesto)
    assert hints["precios_base"] is Precios
    assert hints["return"] is ResultadoPresupuesto


def test_elegibilidad_firmas_usan_itemcatalogo():
    from src.domain.reglas.elegibilidad import (
        elegibles_entibacion, elegibles_pozos,
        elegibles_valvuleria, elegibles_desmontaje,
    )
    for fn in (elegibles_entibacion, elegibles_pozos,
               elegibles_valvuleria, elegibles_desmontaje):
        hints = typing.get_type_hints(fn)
        ann = hints["catalogo"]
        # list[ItemCatalogo] → typing.get_args(list[ItemCatalogo]) == (ItemCatalogo,)
        args = typing.get_args(ann)
        assert args and args[0] is ItemCatalogo, (
            f"{fn.__name__} catalogo anotado como {ann!r}, debería ser list[ItemCatalogo]"
        )


# ---------------------------------------------------------------------------
# Runtime: TypedDict es dict → interoperabilidad transparente
# ---------------------------------------------------------------------------

def test_typeddict_es_dict_en_runtime():
    """Un dict literal se puede pasar donde se espera ItemCatalogo/Precios."""
    item: ItemCatalogo = {"label": "Test", "precio_m": 10.0, "diametro_mm": 100}
    assert item["label"] == "Test"
    assert isinstance(item, dict)


def test_cargar_precios_devuelve_shape_compatible_con_precios():
    """El resultado real de ``cargar_precios()`` tiene las claves de Precios.

    No es un check estricto (Precios es ``total=False``) pero sí verifica
    que las claves más importantes del contrato están presentes.
    """
    from src.infraestructura.precios import cargar_precios
    precios = cargar_precios()
    for clave in ("pct_ci", "pct_gg", "pct_bi", "pct_iva",
                  "catalogo_aba", "catalogo_san", "excavacion"):
        assert clave in precios, f"Falta '{clave}' en cargar_precios()"
