"""Helpers privados compartidos por los capítulos de obra civil.

  - ``_importe`` — multiplicador con fail-fast ante None/negativos/NaN.
    Lo importan también ``capitulos_superficie`` y tests; por eso queda
    re-exportado en el ``__init__`` del subpaquete.
  - ``_precio_excavacion`` — precio €/m³ según profundidad y tipo (manual/mecánico).
  - ``_partidas_excavacion`` — desglose excavación manual + mecánica.
  - ``_calcular_canones`` — cánones de tierras y mixto RCD.
"""

from __future__ import annotations

import math


def _importe(cantidad: float, precio: float) -> float:
    # Fail-fast: un cálculo con datos inválidos no debe producir 0 € silencioso.
    # Cualquier None/negativo/NaN indica bug aguas arriba (carga de precios o parámetros).
    if cantidad is None or precio is None:
        raise ValueError(
            f"_importe: valor None recibido (cantidad={cantidad!r}, precio={precio!r}). "
            "Esto indica un bug de carga de precios o de parámetros del proyecto."
        )
    c = float(cantidad)
    p = float(precio)
    if not (math.isfinite(c) and math.isfinite(p)):
        raise ValueError(
            f"_importe: valor no finito (cantidad={c}, precio={p}). "
            "NaN o infinito indican un bug aritmético previo."
        )
    if c < 0 or p < 0:
        raise ValueError(
            f"_importe: valor negativo no permitido (cantidad={c:.4f}, precio={p:.4f}). "
            "Los importes deben ser positivos o cero — revisa la BD y los parámetros."
        )
    return c * p


def _precio_excavacion(profundidad: float, exc: dict, manual: bool) -> float:
    """Precio de excavación según profundidad y tipo (umbral 2.5 m)."""
    umbral = exc["umbral_profundidad_m"]
    if manual:
        return exc["manual_hasta_25"] if profundidad < umbral else exc["manual_mas_25"]
    return exc["mec_hasta_25"] if profundidad < umbral else exc["mec_mas_25"]


def _partidas_excavacion(
    vol_zanja: float,
    pct_manual: float,
    profundidad: float,
    exc: dict,
) -> dict[str, float]:
    """Calcula las partidas de excavación manual y mecánica."""
    partidas: dict[str, float] = {}
    pct_mec = 1.0 - pct_manual
    if pct_manual > 0:
        partidas["Excavación manual"] = _importe(
            vol_zanja * pct_manual, _precio_excavacion(profundidad, exc, manual=True))
    if pct_mec > 0:
        partidas["Excavación mecánica"] = _importe(
            vol_zanja * pct_mec, _precio_excavacion(profundidad, exc, manual=False))
    return partidas


def _calcular_canones(
    vol_zanja: float,
    factor_esponj: float,
    longitud: float,
    h_pav: float,
    ancho_cima: float,
    es_san: bool,
    exc: dict,
) -> tuple[float, float]:
    """Calcula canon de vertido de tierras y canon mixto RCD.

    Returns:
        (canon_tierras, canon_mixto)
    """
    vol_canon = vol_zanja * factor_esponj
    canon_tierras = _importe(vol_canon, exc["canon_tierras"])

    canon_mixto = 0.0
    if h_pav > 0 and "canon_mixto" in exc:
        if es_san:
            vol_mixto = longitud * h_pav * (ancho_cima + 0.75)
        else:
            vol_mixto = longitud * h_pav
        canon_mixto = _importe(vol_mixto, exc["canon_mixto"])

    return canon_tierras, canon_mixto
