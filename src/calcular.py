"""
Funciones de cálculo de partidas y capítulos.

Modelo de zanja alineado con el Excel EMASESA (A-Fundición 150 / S-Gres 300):
- Ancho de fondo por fórmula (ABA: IF(DN<250, 0.6, 1.2*DN/1000+0.4) / SAN: 1.2*DN/1000+1.5)
- Clearance de profundidad: P_exc = P + 0.15 + 0.1*DN/1000 - h_pavimento
- Modelo trapezoidal (talud 0.4:1) sin entibación, rectangular con entibación
- Arriñonado por fórmula (ABA: +0.2, SAN: +0.3)
- Excavación split manual/mecánica (pct_manual configurable)
- Factor "piezas especiales" por tipo de tubería (FD×1.2, Gres×1.35, etc.)
- Relleno derivado: vol_excavación - vol_arriñonado - vol_tubo
- Transporte = vol_excavación_total
- Canon = vol_excavación_total × factor_esponjamiento
- Entibación automática cuando profundidad > umbral (ABA: +0.20, SAN: (P+1)×2×1.1)
"""

from __future__ import annotations

import math
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (privadas)
# ═══════════════════════════════════════════════════════════════════════════════

def _importe(cantidad: float, precio: float) -> float:
    return max(float(cantidad or 0), 0.0) * max(float(precio or 0), 0.0)


def _precio_exc(profundidad: float, exc: dict, manual: bool) -> float:
    umbral = exc["umbral_profundidad_m"]
    if manual:
        return exc["manual_hasta_25"] if profundidad < umbral else exc["manual_mas_25"]
    return exc["mec_hasta_25"] if profundidad < umbral else exc["mec_mas_25"]


# ═══════════════════════════════════════════════════════════════════════════════
# GEOMETRÍA DE ZANJA — Fórmulas del Excel EMASESA
# ═══════════════════════════════════════════════════════════════════════════════

def _ancho_fondo(dn_mm: int, es_san: bool) -> float:
    """Ancho de fondo de zanja según fórmula Excel EMASESA.

    ABA (A-Fundición 150:H69): IF(DN<250, 0.6, 1.2*DN/1000+0.4)
    SAN (S-Gres 300:H62):      1.2*DN_mm/1000 + 1.5
    """
    if es_san:
        return 1.2 * dn_mm / 1000.0 + 1.5
    return 0.6 if dn_mm < 250 else (1.2 * dn_mm / 1000.0 + 0.4)


def _altura_arena(dn_mm: int, es_san: bool) -> float:
    """Altura del lecho de arena/arriñonado por fórmula Excel EMASESA.

    ABA (H75): 1.2*DN/1000 + 0.2
    SAN (H68): 1.2*DN/1000 + 0.3
    """
    return 1.2 * dn_mm / 1000.0 + (0.3 if es_san else 0.2)


def _ancho_recubrimiento(dn_mm: int, es_san: bool, hay_entibacion: bool,
                          ancho_fondo: float) -> float:
    """Ancho de zanja a la altura del recubrimiento de arena (Excel EMASESA).

    Con entibación (paredes verticales): igual al fondo.
    Sin entibación (talud 0.4:1): ABA=+0.2 lateral, SAN=+0.3 lateral.
    """
    if hay_entibacion:
        return ancho_fondo
    offset = 0.3 if es_san else 0.2
    return (1.2 * dn_mm / 1000.0 + offset) * 0.4 + ancho_fondo


def _ancho_cima(P_exc: float, hay_entibacion: bool, ancho_fondo: float) -> float:
    """Ancho de zanja en la cima (nivel de pavimento).

    Con entibación: igual al fondo (rectangular).
    Sin entibación: talud 0.4:1 aplicado sobre P_exc.
    """
    if hay_entibacion:
        return ancho_fondo
    return P_exc * 0.4 + ancho_fondo


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO DE OBRA CIVIL — Modelo Excel EMASESA (zanja trapezoidal)
# ═══════════════════════════════════════════════════════════════════════════════

def capitulo_obra_civil_red(
    longitud: float,
    profundidad: float,
    item: dict,
    precios: dict,
    *,
    es_san: bool = False,
    pct_manual: float = 0.30,
    espesor_pavimento_m: float = 0.0,
):
    """Calcula el capítulo de Obra Civil (excavación, tubería, arriñonado, etc.)

    Retorna (subtotal, partidas, auxiliares).
    Los cánones de vertido se calculan aquí pero se devuelven separados en
    auxiliares["canonnes"] para que presupuesto.py los mueva a su propio capítulo.
    """
    precio_tuberia = item["precio_m"]
    nombre_tuberia = item["label"]
    dn_mm = int(item["diametro_mm"])
    factor_piezas = float(item.get("factor_piezas", 1.0))

    exc = precios["excavacion"]
    factor_esponj = float(precios.get("factor_esponjamiento", 1.30))

    L = max(longitud, 0.0)
    P = max(profundidad, 0.0)
    h_pav = max(espesor_pavimento_m, 0.0)
    pct_m = max(0.0, min(1.0, float(pct_manual)))
    pct_mec = 1.0 - pct_m

    # ─── Geometría de zanja (fórmulas Excel) ────────────────────────────────
    clearance = 0.15 + 0.1 * dn_mm / 1000.0    # Excel: +0.15+0.1*DN/1000
    P_exc = max(P + clearance - h_pav, 0.0)    # profundidad efectiva de excavación

    W_fondo = _ancho_fondo(dn_mm, es_san)

    # Determinar si hay entibación (para forma de zanja)
    # Se consulta el catálogo para saber el umbral aplicable a esta red/profundidad
    red_proyecto = "SAN" if es_san else "ABA"
    hay_entibacion_geo = False
    entibaciones = sorted(
        precios.get("catalogo_entibacion", []),
        key=lambda e: float(e.get("umbral_m", 0)),
        reverse=True,
    )
    entib_aplicada = None
    for entib in entibaciones:
        umbral = float(entib.get("umbral_m", 1.5))
        red_entib = entib.get("red")
        if red_entib is not None and red_entib != red_proyecto:
            continue
        if P > umbral:
            hay_entibacion_geo = True
            entib_aplicada = entib
            break

    W_cima = _ancho_cima(P_exc, hay_entibacion_geo, W_fondo)
    W_media = (W_fondo + W_cima) / 2.0

    # ─── Volúmenes (m³) ─────────────────────────────────────────────────────
    d_ext = 1.2 * dn_mm / 1000.0
    vol_tubo_pm = math.pi / 4.0 * d_ext ** 2          # m³/m (sección tubo)

    vol_zanja = W_media * P_exc * L                    # trapezoidal × longitud
    vol_tubo = vol_tubo_pm * L

    # Arriñonado (lecho de arena)
    h_arena = _altura_arena(dn_mm, es_san)
    W_recub = _ancho_recubrimiento(dn_mm, es_san, hay_entibacion_geo, W_fondo)
    W_arena_media = (W_fondo + W_recub) / 2.0
    vol_arrinonado_pm = W_arena_media * h_arena - vol_tubo_pm
    vol_arrinonado = max(vol_arrinonado_pm * L, 0.0)

    vol_relleno = max(vol_zanja - vol_arrinonado - vol_tubo, 0.0)
    vol_transporte = vol_zanja                         # perfil teórico completo
    vol_canon_tierras = vol_zanja * factor_esponj

    # ─── Partidas de obra civil (sin cánones) ────────────────────────────────
    partidas: dict[str, float] = {}

    # Tubería (con factor piezas especiales)
    partidas[nombre_tuberia] = _importe(L, precio_tuberia * factor_piezas)

    # Excavación split manual/mecánica
    # Umbral de precio según profundidad cruda (P), NO P_exc — Excel: IF(D17<2.5,...)
    if pct_m > 0:
        partidas["Excavación manual"] = _importe(
            vol_zanja * pct_m, _precio_exc(P, exc, manual=True))
    if pct_mec > 0:
        partidas["Excavación mecánica"] = _importe(
            vol_zanja * pct_mec, _precio_exc(P, exc, manual=False))

    # Apoyo y arriñonado
    partidas["Apoyo y arriñonado"] = _importe(vol_arrinonado, exc["arrinonado"])

    # Relleno de albero
    partidas["Relleno de albero"] = _importe(vol_relleno, exc["relleno"])

    # Carga de tierras (siempre mecánica sobre volumen total)
    partidas["Carga de tierras"] = _importe(vol_transporte, exc["carga_mec"])

    # Transporte a vertedero
    partidas["Transporte a vertedero"] = _importe(vol_transporte, exc["transporte"])

    # ─── Entibación ──────────────────────────────────────────────────────────
    # Fórmulas Excel EMASESA:
    # SAN: (P + 1.0) × 2.0 × 1.1 × L  (H17 en S-Gres 300)
    # ABA: (P + 0.1×DN/1000 + 0.20) × 2.0 × L  (H77 en A-Fundición 150)
    if entib_aplicada is not None:
        if es_san:
            sup_entib = (P + 1.0) * 2.0 * 1.1 * L
        else:
            sup_entib = (P + 0.1 * dn_mm / 1000.0 + 0.20) * 2.0 * L
        partidas[entib_aplicada["label"]] = _importe(sup_entib, entib_aplicada["precio_m2"])

    # ─── Cánones de vertido (se devuelven separados para capítulo CÁNONES) ──
    canon_tierras = _importe(vol_canon_tierras, exc["canon_tierras"])
    # Canon mixto RCD (demolición pavimento)
    # ABA: L × h_pav (footprint 1m²/m)
    # SAN: L × h_pav × (W_cima + 0.75)  — Excel S-Gres 300: H72*(H63+0.75)
    canon_mixto = 0.0
    if h_pav > 0 and "canon_mixto" in exc:
        if es_san:
            vol_mixto = L * h_pav * (W_cima + 0.75)
        else:
            vol_mixto = L * h_pav
        canon_mixto = _importe(vol_mixto, exc["canon_mixto"])

    subtotal = sum(partidas.values())

    auxiliares = {
        "ancho_fondo_m": round(W_fondo, 3),
        "ancho_cima_m": round(W_cima, 3),
        "P_exc_m": round(P_exc, 3),
        "vol_zanja_m3": round(vol_zanja, 3),
        "vol_tubo_m3": round(vol_tubo, 3),
        "vol_arrinonado_m3": round(vol_arrinonado, 3),
        "vol_relleno_m3": round(vol_relleno, 3),
        "vol_transporte_m3": round(vol_transporte, 3),
        "vol_canon_m3": round(vol_canon_tierras, 3),
        "pct_manual": round(pct_m, 2),
        # Cánones separados para capítulo CÁNONES DE VERTIDO
        "canon_tierras": round(canon_tierras, 2),
        "canon_mixto": round(canon_mixto, 2),
    }
    return subtotal, partidas, auxiliares


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSIÓN DE UNIDADES — Calzada (m² → m³)
# ═══════════════════════════════════════════════════════════════════════════════

def _importe_calzada_desde_m2(item: dict[str, Any], superficie_m2: float,
                               espesores: dict) -> float:
    if item.get("unidad") == "m2":
        return _importe(superficie_m2, item["precio"])
    espesor = espesores.get(item["label"])
    if espesor is None:
        raise ValueError(
            f"No existe espesor definido para '{item['label']}'. "
            "Añádelo en Administración de precios → Espesores de calzada."
        )
    return _importe(superficie_m2 * espesor, item["precio"])


# ═══════════════════════════════════════════════════════════════════════════════
# POZOS DE REGISTRO
# ═══════════════════════════════════════════════════════════════════════════════

def capitulo_pozos_registro(
    longitud: float, es_san: bool, precios: dict,
    *, profundidad: float = 0.0, diametro_mm: int = 0,
) -> tuple[float, dict] | None:
    catalogo = precios.get("catalogo_pozos", [])
    if not catalogo or longitud <= 0:
        return None
    red_proyecto = "SAN" if es_san else "ABA"
    candidatos = []
    for item in catalogo:
        red_item = item.get("red")
        if red_item is not None and red_item != red_proyecto:
            continue
        prof_max = item.get("profundidad_max")
        if prof_max is not None and profundidad >= float(prof_max):
            continue
        dn_max = item.get("dn_max")
        if dn_max is not None and diametro_mm > int(dn_max):
            continue
        candidatos.append(item)
    if not candidatos:
        if catalogo:
            red_label = "SAN" if es_san else "ABA"
            raise ValueError(
                f"Hay {len(catalogo)} pozos en el catálogo pero ninguno aplica para "
                f"red={red_label}, profundidad={profundidad:.1f} m, DN={diametro_mm} mm. "
                "Revisa los rangos en Administración de precios."
            )
        return None

    def _especificidad(item):
        sin_red = item.get("red") is None
        p_max = float(item["profundidad_max"]) if item.get("profundidad_max") is not None else 9999
        d_max = int(item["dn_max"]) if item.get("dn_max") is not None else 99999
        return (sin_red, p_max, d_max)

    mejor = min(candidatos, key=_especificidad)
    intervalo = float(mejor.get("intervalo", 0))
    if intervalo <= 0:
        return None
    n_pozos = longitud / intervalo
    importe_pozo = _importe(n_pozos, mejor["precio"])

    # Tapa de pozo registro (si tiene precio_tapa configurado)
    importe_tapa = 0.0
    precio_tapa = float(mejor.get("precio_tapa", 0.0) or 0.0)
    if precio_tapa > 0:
        importe_tapa = _importe(n_pozos, precio_tapa)

    partidas: dict[str, float] = {mejor["label"]: importe_pozo}
    if importe_tapa > 0:
        partidas[mejor["label"] + " (tapa)"] = importe_tapa

    return sum(partidas.values()), partidas


# ═══════════════════════════════════════════════════════════════════════════════
# VALVULERÍA ABA (con factor_piezas)
# ═══════════════════════════════════════════════════════════════════════════════

def capitulo_valvuleria(
    longitud: float, diametro_mm: int, precios: dict,
    *, instalacion: str = "enterrada",
) -> tuple[float, dict] | None:
    catalogo = precios.get("catalogo_valvuleria", [])
    if not catalogo or longitud <= 0:
        return None
    partidas: dict[str, float] = {}
    for item in catalogo:
        if "dn_min" not in item or "dn_max" not in item:
            continue
        dn_min = int(item["dn_min"])
        dn_max = int(item["dn_max"])
        if not (dn_min <= int(diametro_mm) <= dn_max):
            continue
        inst = item.get("instalacion")
        if inst is not None and inst != instalacion:
            continue
        intervalo = float(item.get("intervalo_m", 0))
        if intervalo <= 0:
            continue
        n = longitud / intervalo
        factor = float(item.get("factor_piezas", 1.0))
        partidas[item["label"]] = _importe(n, item["precio"] * factor)
    if not partidas:
        if catalogo:
            raise ValueError(
                f"Hay {len(catalogo)} items de valvulería pero ninguno aplica para "
                f"DN={diametro_mm} mm, instalación='{instalacion}'. "
                "Revisa los rangos DN e instalación en Administración de precios."
            )
        return None
    return sum(partidas.values()), partidas


# ═══════════════════════════════════════════════════════════════════════════════
# GENERADORES DE CAPÍTULOS SIMPLES
# ═══════════════════════════════════════════════════════════════════════════════

def capitulo_demolicion(
    qty1: float, item1: dict[str, Any] | None,
    qty2: float, item2: dict[str, Any] | None,
) -> tuple[float, dict] | None:
    if qty1 <= 0 and qty2 <= 0:
        return None
    partidas: dict[str, float] = {}
    if qty1 > 0 and item1 and "label" in item1:
        partidas[item1["label"]] = _importe(qty1, item1["precio"])
    if qty2 > 0 and item2 and "label" in item2:
        partidas[item2["label"]] = _importe(qty2, item2["precio"])
    if not partidas:
        return None
    return sum(partidas.values()), partidas


def capitulo_pavimentacion(
    qty1: float, item1: dict[str, Any],
    qty2: float, item2: dict[str, Any],
    *,
    calzada_conversion: bool = False,
    espesores: dict | None = None,
) -> tuple[float, dict] | None:
    if qty1 <= 0 and qty2 <= 0:
        return None
    partidas = {}
    if qty1 > 0:
        if not item1 or "label" not in item1:
            raise ValueError("Superficie de pavimentación > 0 pero no se seleccionó material.")
        partidas[item1["label"]] = (
            _importe_calzada_desde_m2(item1, qty1, espesores or {}) if calzada_conversion
            else _importe(qty1, item1["precio"]))
    if qty2 > 0:
        if not item2 or "label" not in item2:
            raise ValueError("Longitud de pavimentación > 0 pero no se seleccionó material.")
        partidas[item2["label"]] = _importe(qty2, item2["precio"])
    return sum(partidas.values()), partidas


def capitulo_acometidas(n: int, precio: float, label: str,
                         factor: float = 1.0) -> tuple[float, dict] | None:
    if n <= 0:
        return None
    importe = _importe(n, precio * factor)
    return importe, {label: importe}


def capitulo_importe_fijo(importe: float, label: str) -> tuple[float, dict] | None:
    if importe <= 0:
        return None
    return importe, {label: importe}


def capitulo_subbase(
    superficie_m2: float, espesor_m: float, item: dict[str, Any] | None,
) -> tuple[float, dict] | None:
    if superficie_m2 <= 0 or espesor_m <= 0 or item is None:
        return None
    vol = superficie_m2 * espesor_m
    importe = _importe(vol, item["precio_m3"])
    return importe, {item["label"]: importe}


def capitulo_canones(canon_tierras: float, canon_mixto: float) -> tuple[float, dict] | None:
    """Capítulo d) OTROS — cánones de vertido (excluidos de base S&S)."""
    partidas: dict[str, float] = {}
    if canon_tierras > 0:
        partidas["Canon vertido tierras"] = canon_tierras
    if canon_mixto > 0:
        partidas["Canon vertido mixto"] = canon_mixto
    if not partidas:
        return None
    return sum(partidas.values()), partidas


def capitulo_desmontaje_tuberia(
    longitud: float, diametro_mm: int, tipo: str, precios: dict
) -> tuple[float, dict] | None:
    """Desmontaje de tubería existente. tipo='normal' o 'fibrocemento'."""
    if tipo == "none" or longitud <= 0:
        return None
    catalogo = precios.get("catalogo_desmontaje", [])
    if not catalogo:
        return None
    es_fc = (tipo == "fibrocemento")
    # Filtrar por fibrocemento y diámetro
    candidatos = [
        item for item in catalogo
        if bool(item.get("es_fibrocemento", 0)) == es_fc
        and (es_fc or diametro_mm <= int(item["dn_max"]))
    ]
    if not candidatos:
        return None
    # Elegir el de menor dn_max que aplique (más específico)
    mejor = min(candidatos, key=lambda x: int(x["dn_max"]))
    importe = _importe(longitud, mejor["precio_m"])
    return importe, {mejor["label"]: importe}


def capitulo_imbornales(
    longitud: float, tipo: str, label_nuevo: str, precios: dict,
    pct_ci: float = 1.0,
) -> tuple[float, dict] | None:
    """Imbornales SAN: adaptación o nuevos. Fórmula: n = 2/32 × L."""
    if tipo == "none" or longitud <= 0:
        return None
    catalogo = precios.get("catalogo_imbornales", [])
    if not catalogo:
        return None
    n = 2.0 / 32.0 * longitud
    if tipo == "adaptacion":
        item = next((x for x in catalogo if x["tipo"] == "adaptacion"), None)
        if item is None:
            return None
        importe = _importe(n, item["precio"])
        return importe, {item["label"]: importe}
    else:  # nuevo
        item = next((x for x in catalogo if x["label"] == label_nuevo), None)
        if item is None:
            # fallback al primer "nuevo"
            item = next((x for x in catalogo if x["tipo"] == "nuevo"), None)
        if item is None:
            return None
        importe = _importe(n, item["precio"])
        return importe, {item["label"]: importe}


def capitulo_pozos_existentes(
    longitud: float, red: str, accion: str, precios: dict
) -> tuple[float, dict] | None:
    """Demolición o anulación de pozos existentes."""
    if accion == "none" or longitud <= 0:
        return None
    catalogo = precios.get("catalogo_pozos_existentes", [])
    item = next(
        (x for x in catalogo if x["red"] == red and x["accion"] == accion),
        None
    )
    if item is None:
        return None
    intervalo = float(item.get("intervalo_m", 100))
    n = longitud / intervalo
    importe = _importe(n, item["precio"])
    accion_label = "Demolición pozo existente" if accion == "demolicion" else "Anulación pozo existente"
    return importe, {accion_label: importe}
