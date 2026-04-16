"""
Capítulos de obra civil - excavación, tubería, pozos, valvulería, etc.

Cada función recibe cantidades y precios ya resueltos y devuelve
(subtotal: float, partidas: dict[str, float]) | None.

  - SÍ importa de src.domain (geometría)
  - NO importa de src.reglas (el motor ya resolvió las decisiones)
  - NO importa streamlit
"""

from __future__ import annotations

import logging
from typing import Any

from src.domain.geometria import calcular_geometria, GeometriaZanja

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers internos (compartidos con capitulos_superficie via import)
# ---------------------------------------------------------------------------

def _importe(cantidad: float, precio: float) -> float:
    c = float(cantidad or 0)
    p = float(precio or 0)
    if c < 0 or p < 0:
        logger.warning("_importe: valor negativo silenciado (cantidad=%.4f, precio=%.4f)", c, p)
    if cantidad is None or precio is None:
        logger.warning("_importe: valor None recibido (cantidad=%s, precio=%s)", cantidad, precio)
    return max(c, 0.0) * max(p, 0.0)


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
    red_label = "SAN" if es_san else "ABA"
    logger.debug("[OC-%s] Entrada: L=%.2f P=%.2f item=%s pct_manual=%.2f h_pav=%.3f entib=%s",
                 red_label, longitud, profundidad, item.get("label", "?"),
                 pct_manual, espesor_pavimento_m,
                 entibacion_item["label"] if entibacion_item else None)

    L = max(longitud, 0.0)
    P = max(profundidad, 0.0)
    h_pav = max(espesor_pavimento_m, 0.0)
    pct_m = max(0.0, min(1.0, float(pct_manual)))

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

    # Volúmenes totales (× longitud)
    vol_zanja = geo.vol_zanja_m3 * L
    vol_arena = geo.vol_arena_pm * L
    vol_relleno = geo.vol_relleno_pm * L
    vol_transporte = vol_zanja                      # perfil completo

    logger.debug("[OC-%s] Geo: fondo=%.3f cima=%.3f P_exc=%.3f | vol: zanja=%.3f arena=%.3f relleno=%.3f"
                 " transporte=%.3f (esponj=%.2f)",
                 red_label, geo.ancho_fondo_m, geo.ancho_cima_m, geo.P_exc_m,
                 vol_zanja, vol_arena, vol_relleno,
                 vol_transporte, factor_esponj)
    logger.debug("[OC-%s] Tubería: %s precio=%.4f fp=%.2f → %.2f €",
                 red_label, nombre_tuberia, precio_tuberia, factor_piezas,
                 _importe(L, precio_tuberia * factor_piezas))

    # ── Partidas ──────────────────────────────────────────────────────────────
    partidas: dict[str, float] = {}

    # Tubería (con factor piezas especiales)
    partidas[nombre_tuberia] = _importe(L, precio_tuberia * factor_piezas)

    # Excavación (split manual/mecánica; umbral de precio según P cruda)
    partidas.update(_partidas_excavacion(vol_zanja, pct_m, P, exc))

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
        logger.debug("[OC-%s] Entibación: sup=%.3f × precio=%.4f = %.2f €",
                     red_label, sup_entib, entibacion_item["precio_m2"],
                     partidas[entibacion_item["label"]])
    else:
        logger.debug("[OC-%s] Sin entibación", red_label)

    # ── Cánones (se devuelven separados para capítulo OTROS) ─────────────────
    canon_tierras, canon_mixto = _calcular_canones(
        vol_zanja, factor_esponj, L, h_pav, geo.ancho_cima_m, es_san, exc)

    subtotal = sum(partidas.values())
    logger.debug("[OC-%s] Subtotal obra civil: %.2f € | canon_tierras=%.2f canon_mixto=%.2f",
                 red_label, subtotal, canon_tierras, canon_mixto)

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
    red_label = "SAN" if es_san else "ABA"
    logger.debug("[POZOS-%s] Entrada: L=%.2f P=%.2f DN=%d pozo_item=%s",
                 red_label, longitud, profundidad, diametro_mm,
                 pozo_item["label"] if pozo_item else None)
    if not precios.get("catalogo_pozos") or longitud <= 0:
        logger.debug("[POZOS-%s] Guard: catálogo vacío o L<=0 → None", red_label)
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

    # Guardia SAN: rechazar el pozo genérico ABA (red=None) cuando estamos
    # en saneamiento. Ocurre cuando P supera el máximo del catálogo SAN (5 m).
    # El Excel EMASESA no define pozos SAN para esas profundidades → None.
    if es_san and pozo_item.get("red") is None:
        logger.warning(
            "[POZOS-SAN] P=%.2fm supera el máximo cubierto por el catálogo SAN "
            "(profundidad_max=5.0m). No existe pozo de registro SAN para esta "
            "profundidad en la Base de Precios EMASESA → partida nula.",
            profundidad,
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

    total = sum(partidas.values())
    logger.debug("[POZOS-%s] n=%.2f intervalo=%.1f → %.2f € (%d partidas)",
                 red_label, n_pozos, intervalo, total, len(partidas))
    return total, partidas


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
    logger.debug("[VALV] Entrada: L=%.2f DN=%d inst=%s items=%d",
                 longitud, diametro_mm, instalacion,
                 len(valvuleria_items) if valvuleria_items else 0)
    if not precios.get("catalogo_valvuleria") or longitud <= 0:
        logger.debug("[VALV] Guard: catálogo vacío o L<=0 → None")
        return None

    items = valvuleria_items or []
    partidas: dict[str, float] = {}
    for item in items:
        intervalo = float(item.get("intervalo_m", 0))
        if intervalo <= 0:
            continue
        n = longitud / intervalo
        factor = float(item.get("factor_piezas", 1.0))
        imp = _importe(n, item["precio"] * factor)
        partidas[item["label"]] = imp
        logger.debug("[VALV]   '%s': n=%.2f × precio=%.4f × fp=%.2f = %.2f €",
                     item["label"], n, item["precio"], factor, imp)

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
        logger.debug("[DESM] Guard: L=%.2f item=%s → None",
                     longitud, desmontaje_item["label"] if desmontaje_item else None)
        return None
    importe = _importe(longitud, desmontaje_item["precio_m"])
    logger.debug("[DESM] %s: L=%.2f × precio=%.4f = %.2f €",
                 desmontaje_item["label"], longitud, desmontaje_item["precio_m"], importe)
    return importe, {desmontaje_item["label"]: importe}


# ---------------------------------------------------------------------------
# Imbornales (SAN)
# ---------------------------------------------------------------------------

def capitulo_imbornales(
    longitud: float, tipo: str, label_nuevo: str, precios: dict
) -> tuple[float, dict] | None:
    """Fórmula: n_imbornales = 2/32 × L."""
    logger.debug("[IMBORN] Entrada: L=%.2f tipo=%s label_nuevo=%s", longitud, tipo, label_nuevo)
    if tipo == "none" or longitud <= 0:
        logger.debug("[IMBORN] Guard: tipo=none o L<=0 → None")
        return None
    catalogo = precios.get("catalogo_imbornales", [])
    if not catalogo:
        logger.warning("[IMBORN] Catálogo imbornales vacío → None")
        return None
    n = 2.0 / 32.0 * longitud
    if tipo == "adaptacion":
        item = next((x for x in catalogo if x["tipo"] == "adaptacion"), None)
    else:
        item = next((x for x in catalogo if x["label"] == label_nuevo), None)
        if item is None:
            item = next((x for x in catalogo if x["tipo"] == "nuevo"), None)
    if item is None:
        logger.warning("[IMBORN] No se encontró item para tipo=%s label=%s → None", tipo, label_nuevo)
        return None
    importe = _importe(n, item["precio"])
    logger.debug("[IMBORN] %s: n=%.4f × precio=%.4f = %.2f €", item["label"], n, item["precio"], importe)
    return importe, {item["label"]: importe}


# ---------------------------------------------------------------------------
# Pozos existentes (demolición / anulación)
# ---------------------------------------------------------------------------

def capitulo_pozos_existentes(
    longitud: float, accion: str, red: str, precios: dict
) -> tuple[float, dict] | None:
    logger.debug("[POZOS-EX] Entrada: L=%.2f accion=%s red=%s", longitud, accion, red)
    if accion == "none" or longitud <= 0:
        logger.debug("[POZOS-EX] Guard → None")
        return None
    catalogo = precios.get("catalogo_pozos_existentes", [])
    item = next(
        (x for x in catalogo if x["red"] == red and x["accion"] == accion), None
    )
    if item is None:
        logger.warning("[POZOS-EX] No se encontró item red=%s accion=%s en catálogo (%d items) → None",
                       red, accion, len(catalogo))
        return None
    intervalo = float(item.get("intervalo_m", 100.0))
    n = longitud / intervalo
    importe = _importe(n, item["precio"])
    label = f"{accion.capitalize()} pozos existentes {red}"
    logger.debug("[POZOS-EX] %s: n=%.2f × precio=%.4f = %.2f €", label, n, item["precio"], importe)
    return importe, {label: importe}
