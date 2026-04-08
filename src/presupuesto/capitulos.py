"""
Cálculo de partidas y capítulos del presupuesto.

Cada función recibe cantidades y precios ya resueltos y devuelve
(subtotal: float, partidas: dict[str, float]) | None.

Este módulo:
  - SÍ importa de src.domain (geometría y parámetros)
  - NO importa de src.reglas (el motor ya resolvió las decisiones)
  - NO importa streamlit
"""

from __future__ import annotations

import math
from typing import Any

from src.domain.geometria import calcular_geometria, GeometriaZanja


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _importe(cantidad: float, precio: float) -> float:
    return max(float(cantidad or 0), 0.0) * max(float(precio or 0), 0.0)


def _precio_excavacion(profundidad: float, exc: dict, manual: bool) -> float:
    """Precio de excavación según profundidad y tipo (umbral 2.5 m)."""
    umbral = exc["umbral_profundidad_m"]
    if manual:
        return exc["manual_hasta_25"] if profundidad < umbral else exc["manual_mas_25"]
    return exc["mec_hasta_25"] if profundidad < umbral else exc["mec_mas_25"]


# ---------------------------------------------------------------------------
# Capítulo OBRA CIVIL (ABA o SAN)
# ---------------------------------------------------------------------------

def capitulo_obra_civil(
    longitud: float,
    profundidad: float,
    item: dict,
    precios: dict,
    *,
    es_san: bool = False,
    pct_manual: float = 0.30,
    espesor_pavimento_m: float = 0.0,
    entibacion_item: dict | None = None,
) -> tuple[float, dict, dict]:
    """
    Calcula el capítulo de Obra Civil por metro lineal escalado a la longitud.

    Returns:
        (subtotal, partidas, auxiliares)
        Los cánones de vertido se devuelven en auxiliares["canon_tierras"] y
        auxiliares["canon_mixto"] para que ensamblaje.py los mueva al capítulo OTROS.
    """
    L = max(longitud, 0.0)
    P = max(profundidad, 0.0)
    h_pav = max(espesor_pavimento_m, 0.0)
    pct_m = max(0.0, min(1.0, float(pct_manual)))
    pct_mec = 1.0 - pct_m

    hay_entibacion = entibacion_item is not None

    # Geometría (por metro lineal)
    geo: GeometriaZanja = calcular_geometria(
        dn_mm=int(item["diametro_mm"]),
        profundidad_m=P,
        es_san=es_san,
        hay_entibacion=hay_entibacion,
        espesor_pavimento_m=h_pav,
    )

    exc = precios["excavacion"]
    factor_esponj = float(precios.get("factor_esponjamiento", 1.30))
    factor_piezas = float(item.get("factor_piezas", 1.0))
    precio_tuberia = float(item["precio_m"])
    nombre_tuberia = item["label"]
    dn_mm = int(item["diametro_mm"])

    # Volúmenes totales (× longitud)
    vol_zanja = geo.vol_zanja_m3 * L
    vol_arena = geo.vol_arena_pm * L
    vol_relleno = geo.vol_relleno_pm * L
    vol_transporte = vol_zanja                      # perfil completo
    vol_canon = vol_zanja * factor_esponj

    # ── Partidas ──────────────────────────────────────────────────────────────
    partidas: dict[str, float] = {}

    # Tubería (con factor piezas especiales)
    partidas[nombre_tuberia] = _importe(L, precio_tuberia * factor_piezas)

    # Excavación (split manual/mecánica; umbral de precio según P cruda)
    if pct_m > 0:
        partidas["Excavación manual"] = _importe(
            vol_zanja * pct_m, _precio_excavacion(P, exc, manual=True))
    if pct_mec > 0:
        partidas["Excavación mecánica"] = _importe(
            vol_zanja * pct_mec, _precio_excavacion(P, exc, manual=False))

    # Arriñonado
    partidas["Apoyo y arriñonado"] = _importe(vol_arena, exc["arrinonado"])

    # Relleno
    partidas["Relleno de albero"] = _importe(vol_relleno, exc["relleno"])

    # Carga y transporte
    partidas["Carga de tierras"] = _importe(vol_transporte, exc["carga_mec"])
    partidas["Transporte a vertedero"] = _importe(vol_transporte, exc["transporte"])

    # Entibación
    if entibacion_item is not None:
        sup_entib = geo.sup_entibacion_pm * L
        partidas[entibacion_item["label"]] = _importe(sup_entib, entibacion_item["precio_m2"])

    # ── Cánones (se devuelven separados para capítulo OTROS) ─────────────────
    canon_tierras = _importe(vol_canon, exc["canon_tierras"])

    # Canon mixto RCD (demolición de pavimento)
    canon_mixto = 0.0
    if h_pav > 0 and "canon_mixto" in exc:
        W_cima = geo.ancho_cima_m
        if es_san:
            vol_mixto = L * h_pav * (W_cima + 0.75)
        else:
            vol_mixto = L * h_pav
        canon_mixto = _importe(vol_mixto, exc["canon_mixto"])

    subtotal = sum(partidas.values())

    auxiliares = {
        # Datos geométricos (para debug y tests)
        "ancho_fondo_m":   geo.ancho_fondo_m,
        "ancho_cima_m":    geo.ancho_cima_m,
        "P_exc_m":         geo.P_exc_m,
        "vol_zanja_m3":    round(vol_zanja, 3),
        "vol_arena_m3":    round(vol_arena, 3),
        "vol_relleno_m3":  round(vol_relleno, 3),
        "pct_manual":      round(pct_m, 2),
        # Cánones (para capítulo OTROS)
        "canon_tierras":   round(canon_tierras, 2),
        "canon_mixto":     round(canon_mixto, 2),
    }

    return subtotal, partidas, auxiliares


# ---------------------------------------------------------------------------
# Pozos de registro
# ---------------------------------------------------------------------------

def capitulo_pozos_registro(
    longitud: float,
    profundidad: float,
    diametro_mm: int,
    precios: dict,
    *,
    es_san: bool = False,
    pozo_item: dict | None = None,
) -> tuple[float, dict] | None:
    if not precios.get("catalogo_pozos") or longitud <= 0:
        return None

    if pozo_item is None:
        if precios["catalogo_pozos"]:
            red_label = "SAN" if es_san else "ABA"
            raise ValueError(
                f"Hay {len(precios['catalogo_pozos'])} pozos en el catálogo pero ninguno aplica "
                f"para red={red_label}, profundidad={profundidad:.1f} m, DN={diametro_mm} mm. "
                "Revisa los rangos en Administración de precios."
            )
        return None

    intervalo = float(pozo_item.get("intervalo", 0))
    if intervalo <= 0:
        return None

    n_pozos = longitud / intervalo
    partidas: dict[str, float] = {
        pozo_item["label"]: _importe(n_pozos, pozo_item["precio"])
    }

    precio_tapa = float(pozo_item.get("precio_tapa", 0.0) or 0.0)
    if precio_tapa > 0:
        partidas[pozo_item["label"] + " (tapa)"] = _importe(n_pozos, precio_tapa)

    return sum(partidas.values()), partidas


# ---------------------------------------------------------------------------
# Valvulería ABA
# ---------------------------------------------------------------------------

def capitulo_valvuleria(
    longitud: float,
    diametro_mm: int,
    precios: dict,
    *,
    instalacion: str = "enterrada",
    valvuleria_items: list | None = None,
) -> tuple[float, dict] | None:
    if not precios.get("catalogo_valvuleria") or longitud <= 0:
        return None

    items = valvuleria_items or []
    partidas: dict[str, float] = {}
    for item in items:
        intervalo = float(item.get("intervalo_m", 0))
        if intervalo <= 0:
            continue
        n = longitud / intervalo
        factor = float(item.get("factor_piezas", 1.0))
        partidas[item["label"]] = _importe(n, item["precio"] * factor)

    if not partidas:
        if precios["catalogo_valvuleria"]:
            raise ValueError(
                f"Hay {len(precios['catalogo_valvuleria'])} items de valvulería pero ninguno "
                f"aplica para DN={diametro_mm} mm, instalación='{instalacion}'. "
                "Revisa los rangos DN e instalación en Administración de precios."
            )
        return None

    return sum(partidas.values()), partidas


# ---------------------------------------------------------------------------
# Demolición de pavimento
# ---------------------------------------------------------------------------

def capitulo_demolicion(
    qty1: float, item1: dict[str, Any] | None,
    qty2: float, item2: dict[str, Any] | None,
) -> tuple[float, dict] | None:
    if qty1 <= 0 and qty2 <= 0:
        return None
    partidas: dict[str, float] = {}
    for qty, item in [(qty1, item1), (qty2, item2)]:
        if qty > 0 and item and "label" in item:
            factor = float(item.get("factor_ci", 1.0))
            partidas[item["label"]] = _importe(qty, item["precio"] * factor)
    if not partidas:
        return None
    return sum(partidas.values()), partidas


# ---------------------------------------------------------------------------
# Pavimentación (acerado, bordillo, calzada)
# ---------------------------------------------------------------------------

def capitulo_pavimentacion(
    qty1: float, item1: dict[str, Any],
    qty2: float, item2: dict[str, Any],
    *,
    calzada_conversion: bool = False,
    espesores: dict | None = None,
    factor_calzada_san: float = 1.0,
) -> tuple[float, dict] | None:
    if qty1 <= 0 and qty2 <= 0:
        return None
    partidas: dict[str, float] = {}

    for qty, item in [(qty1, item1), (qty2, item2)]:
        if qty <= 0:
            continue
        if not item or "label" not in item:
            raise ValueError("Cantidad de pavimentación > 0 pero no se seleccionó material.")
        factor = float(item.get("factor_ci", 1.0))
        if calzada_conversion and espesores and item.get("unidad", "m2") != "m2":
            # Conversión m² → m³ solo para items con unidad m3 (aglomerado, hormigón, etc.)
            espesor = espesores.get(item["label"])
            if espesor is None:
                raise ValueError(
                    f"No existe espesor definido para '{item['label']}'. "
                    "Añádelo en Administración de precios → Espesores de calzada."
                )
            importe = _importe(qty * espesor, item["precio"]) * factor * factor_calzada_san
        else:
            importe = _importe(qty, item["precio"] * factor) * factor_calzada_san
        partidas[item["label"]] = importe

    return sum(partidas.values()), partidas


# ---------------------------------------------------------------------------
# Acometidas
# ---------------------------------------------------------------------------

def capitulo_acometidas(
    n: int, precio: float, label: str, factor: float = 1.0
) -> tuple[float, dict] | None:
    if n <= 0:
        return None
    importe = _importe(n, precio * factor)
    return importe, {label: importe}


# ---------------------------------------------------------------------------
# Sub-base
# ---------------------------------------------------------------------------

def capitulo_subbase(
    superficie_m2: float, espesor_m: float, item: dict[str, Any] | None
) -> tuple[float, dict] | None:
    if superficie_m2 <= 0 or espesor_m <= 0 or item is None:
        return None
    vol = superficie_m2 * espesor_m
    importe = _importe(vol, item["precio_m3"])
    return importe, {item["label"]: importe}


# ---------------------------------------------------------------------------
# Cánones de vertido
# ---------------------------------------------------------------------------

def capitulo_canones(
    canon_tierras: float, canon_mixto: float
) -> tuple[float, dict] | None:
    partidas: dict[str, float] = {}
    if canon_tierras > 0:
        partidas["Canon vertido tierras"] = canon_tierras
    if canon_mixto > 0:
        partidas["Canon vertido mixto"] = canon_mixto
    if not partidas:
        return None
    return sum(partidas.values()), partidas


# ---------------------------------------------------------------------------
# Desmontaje de tubería existente
# ---------------------------------------------------------------------------

def capitulo_desmontaje(
    longitud: float, precios: dict, *, desmontaje_item: dict | None = None
) -> tuple[float, dict] | None:
    if longitud <= 0 or desmontaje_item is None:
        return None
    importe = _importe(longitud, desmontaje_item["precio_m"])
    return importe, {desmontaje_item["label"]: importe}


# ---------------------------------------------------------------------------
# Imbornales (SAN)
# ---------------------------------------------------------------------------

def capitulo_imbornales(
    longitud: float, tipo: str, label_nuevo: str, precios: dict, pct_ci: float = 1.0
) -> tuple[float, dict] | None:
    """Fórmula: n_imbornales = 2/32 × L."""
    if tipo == "none" or longitud <= 0:
        return None
    catalogo = precios.get("catalogo_imbornales", [])
    if not catalogo:
        return None
    n = 2.0 / 32.0 * longitud
    if tipo == "adaptacion":
        item = next((x for x in catalogo if x["tipo"] == "adaptacion"), None)
    else:
        item = next((x for x in catalogo if x["label"] == label_nuevo), None)
        if item is None:
            item = next((x for x in catalogo if x["tipo"] == "nuevo"), None)
    if item is None:
        return None
    importe = _importe(n, item["precio"] * pct_ci)
    return importe, {item["label"]: importe}


# ---------------------------------------------------------------------------
# Pozos existentes (demolición / anulación)
# ---------------------------------------------------------------------------

def capitulo_pozos_existentes(
    longitud: float, accion: str, red: str, precios: dict, pct_ci: float = 1.0
) -> tuple[float, dict] | None:
    if accion == "none" or longitud <= 0:
        return None
    catalogo = precios.get("catalogo_pozos_existentes", [])
    item = next(
        (x for x in catalogo if x["red"] == red and x["accion"] == accion), None
    )
    if item is None:
        return None
    intervalo = float(item.get("intervalo_m", 100.0))
    n = longitud / intervalo
    importe = _importe(n, item["precio"] * pct_ci)
    label = f"{accion.capitalize()} pozos existentes {red}"
    return importe, {label: importe}
