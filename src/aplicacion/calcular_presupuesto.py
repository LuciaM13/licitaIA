"""
Use case principal: calcular un presupuesto EMASESA completo.

Orquestación pura del cálculo de presupuesto. Este módulo:
  1. Aplica el CI sobre una copia local de los precios.
  2. Re-resuelve los items seleccionados por el usuario en el catálogo CI.
  3. Invoca al decisor determinista para obtener ganadores de entibación,
     pozos, valvulería y desmontaje (con overrides del usuario si los hay).
  4. Ensambla los capítulos llamando a los bloques de ``src.presupuesto``.
  5. Monta el resumen financiero (GG, BI, IVA) y retorna ``ResultadoPresupuesto``.

No contiene fórmulas de obra (viven en ``src.domain.geometria`` y
``src.presupuesto.capitulos_*``), no contiene reglas de elegibilidad
(viven en ``src.domain.reglas``) y no accede a persistencia (SQLite queda
tras la frontera de ``src.infraestructura``).
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from src.domain.parametros import ParametrosProyecto
from src.domain.financiero import calcular_resumen
from src.domain.tipos import ItemCatalogo, Precios, ResultadoPresupuesto
from src.infraestructura.precios import aplicar_ci
from src.reglas.decisor import resolver_decisiones
from src.presupuesto.bloques import (
    ensamblar_obra_civil_aba,
    ensamblar_obra_civil_san,
    ensamblar_pavimentacion_aba,
    ensamblar_pavimentacion_san,
    ensamblar_acometidas,
    ensamblar_seguridad_gestion,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de resolución CI
# ---------------------------------------------------------------------------

def _resolver_item_ci(label: str, catalogo: list[ItemCatalogo]) -> ItemCatalogo | None:
    """Re-busca un item por label en el catálogo ya transformado con CI."""
    if not label or not catalogo:
        logger.debug("[CI-RESOLVE] label=%r catalogo_len=%d → None (guard)",
                     label, len(catalogo) if catalogo else 0)
        return None
    item = next((i for i in catalogo if i.get("label") == label), None)
    if item is None:
        logger.warning("[CI-RESOLVE] ITEM NO ENCONTRADO: label=%r no está en el catálogo "
                       "(%d items). El precio NO incluirá CI → posible infravaloración del 5%%.",
                       label, len(catalogo))
    else:
        logger.debug("[CI-RESOLVE] '%s' resuelto con CI (precio_m=%.4f)",
                     label, item.get("precio_m", item.get("precio", 0)))
    return item


def _reresolver_items_ci(
    p: ParametrosProyecto, precios: Precios,
) -> dict[str, Any]:
    """Re-resuelve todos los items de ParametrosProyecto con CI aplicado."""
    def _ci(item: dict | None, catalogo_key: str) -> dict | None:
        if not item:
            return None
        label = item.get("label", "")
        resolved = _resolver_item_ci(label, precios[catalogo_key])
        if resolved is None:
            # Fail-fast: si el item no se encuentra tras aplicar el CI, la invariante
            # BD × pct_ci = Excel se habría violado por infravaloración ~5 %.
            # Abortamos el cálculo en vez de devolver precio base silenciosamente.
            raise ValueError(
                f"Item '{label}' del catálogo '{catalogo_key}' no se resolvió tras "
                "aplicar el CI. Indica inconsistencia entre el catálogo base y el "
                "catálogo con CI aplicado: revisa pct_ci y los precios en admin."
            )
        return resolved

    result = {
        "aba_item": _ci(p.aba_item, "catalogo_aba"),
        "san_item": _ci(p.san_item, "catalogo_san"),
        "pav_aba_acerado_item": _ci(p.pav_aba_acerado_item, "acerados_aba"),
        "pav_aba_bordillo_item": _ci(p.pav_aba_bordillo_item, "bordillos_reposicion"),
        "pav_aba_calzada_item": _ci(p.pav_aba_calzada_item, "calzadas_reposicion"),
        "pav_san_calzada_item": _ci(p.pav_san_calzada_item, "calzadas_reposicion"),
        "pav_san_acera_item": _ci(p.pav_san_acera_item, "acerados_san"),
        "subbase_aba_item": _ci(p.subbase_aba_item, "catalogo_subbases"),
        "subbase_san_item": _ci(p.subbase_san_item, "catalogo_subbases"),
    }
    logger.debug("Re-resolución CI → aba_item=%s san_item=%s",
                 result["aba_item"]["label"] if result["aba_item"] else None,
                 result["san_item"]["label"] if result["san_item"] else None)
    return result


# ---------------------------------------------------------------------------
# Overrides del usuario sobre decisiones CLIPS
# ---------------------------------------------------------------------------

def _aplicar_overrides(decisiones: dict, override: dict) -> None:
    """Reemplaza los ganadores del desempate con las selecciones del usuario.

    El override contiene labels; los items se buscan en el catálogo CI
    que ya está dentro de decisiones["candidatos"].
    """
    cand = decisiones.get("candidatos")
    if not cand:
        logger.warning("_aplicar_overrides: no candidatos en decisiones, override ignorado")
        return

    if "entibacion_label" in override:
        label = override["entibacion_label"]
        if label is None:
            decisiones["entibacion"] = {"necesaria": False, "item": None}
        else:
            item = next(
                (it for it in cand["entibacion"]["catalogo"]
                 if it.get("label") == label), None)
            if item:
                decisiones["entibacion"] = {"necesaria": True, "item": item}

    if "pozo_label" in override:
        label = override["pozo_label"]
        item = next(
            (it for it in cand["pozo_registro"]["catalogo"]
             if it.get("label") == label), None)
        decisiones["pozo_registro"]["item"] = item

    if "valvuleria_labels" in override:
        labels = set(override["valvuleria_labels"])
        items = [it for it in cand["valvuleria"]["catalogo"]
                 if it.get("label") in labels]
        decisiones["valvuleria"]["items"] = items

    if "desmontaje_label" in override:
        label = override["desmontaje_label"]
        if label is None:
            decisiones["desmontaje"]["item"] = None
        else:
            item = next(
                (it for it in cand["desmontaje"]["catalogo"]
                 if it.get("label") == label), None)
            decisiones["desmontaje"]["item"] = item


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_presupuesto(
    p: ParametrosProyecto,
    precios_base: Precios,
    overrides: dict | None = None,
) -> ResultadoPresupuesto:
    """
    Calcula el presupuesto completo para un proyecto EMASESA.

    Args:
        p: Parámetros del proyecto introducidos por el usuario.
        precios_base: Dict de precios BASE cargado desde SQLite. El CI se aplica
            internamente sobre una copia local - el dict original no se muta.
        overrides: Selecciones manuales del usuario sobre las decisiones del
            sistema experto. Dict con claves "aba" y/o "san", cada una con
            labels de los items seleccionados (entibacion_label, pozo_label,
            valvuleria_labels, desmontaje_label). None = desempate automático.

    Returns:
        Dict con:
          - capitulos: dict numerado con subtotal y partidas de cada capítulo
          - pem, gg, bi, pbl_sin_iva, iva, total: resumen financiero
          - auxiliares: datos geométricos de ABA y SAN (para debug)
    """
    logger.info("═══ calcular_presupuesto INICIO ═══")
    logger.info("  ABA: activa=%s tipo=%s DN=%d L=%.2f P=%.2f",
                p.aba_activa, p.aba_tipo if p.aba_activa else "-",
                p.aba_diametro_mm if p.aba_activa else 0,
                p.aba_longitud_m if p.aba_activa else 0,
                p.aba_profundidad_m if p.aba_activa else 0)
    logger.info("  SAN: activa=%s tipo=%s DN=%d L=%.2f P=%.2f",
                p.san_activa, p.san_tipo if p.san_activa else "-",
                p.san_diametro_mm if p.san_activa else 0,
                p.san_longitud_m if p.san_activa else 0,
                p.san_profundidad_m if p.san_activa else 0)
    logger.info("  pct_manual=%.2f espesor_pav=%.3f pct_seg=%.4f pct_gest=%.4f",
                p.pct_manual, p.espesor_pavimento_m, p.pct_seguridad, p.pct_gestion)

    # Aplicar CI sobre copia local para no mutar el dict del caller.
    precios = copy.deepcopy(precios_base)
    pct_ci = precios.get("pct_ci", 0.0)
    logger.debug("Aplicando CI=%.4f sobre deepcopy de precios", pct_ci)
    aplicar_ci(precios)

    # ── Re-resolver items con CI aplicado ───────────────────────────────────
    items_ci = _reresolver_items_ci(p, precios)
    espesores = precios["espesores_calzada"]
    caps: dict[str, dict] = {}
    estado: dict[str, Any] = {
        "excluir_ss": 0.0,
        "materiales_total": 0.0,
        "trazabilidad": {},
        "aux_aba": None,
        "aux_san": None,
    }

    # ── Resolver decisiones del decisor determinista ───────────────────────
    # CLIPS no interviene en la selección de material (solo emite alertas
    # técnicas vía src.reglas.alertas_clips). El decisor aplica elegibilidad
    # + desempate sobre los precios CI. Los overrides de usuario se aplican
    # después para reemplazar ganadores concretos si el licitador lo desea.
    decisiones_aba = None
    decisiones_san = None

    if p.aba_activa:
        decisiones_aba = resolver_decisiones(
            tipo_tuberia=p.aba_tipo,
            diametro_mm=p.aba_diametro_mm,
            red="ABA",
            profundidad=p.aba_profundidad_m,
            precios=precios,
            instalacion=p.instalacion_valvuleria,
            desmontaje_tipo=p.desmontaje_tipo,
        )
        if overrides and "aba" in overrides:
            _aplicar_overrides(decisiones_aba, overrides["aba"])
            logger.info("  [ABA] Overrides del usuario aplicados")

    if p.san_activa:
        decisiones_san = resolver_decisiones(
            tipo_tuberia=p.san_tipo,
            diametro_mm=p.san_diametro_mm,
            red="SAN",
            profundidad=p.san_profundidad_m,
            precios=precios,
            instalacion="enterrada",
            desmontaje_tipo="none",
        )
        if overrides and "san" in overrides:
            _aplicar_overrides(decisiones_san, overrides["san"])
            logger.info("  [SAN] Overrides del usuario aplicados")

    # ── Ensamblar capítulos ─────────────────────────────────────────────────
    ensamblar_obra_civil_aba(p, precios, items_ci["aba_item"], caps, estado, decisiones_aba)
    ensamblar_obra_civil_san(p, precios, items_ci["san_item"], caps, estado, decisiones_san)
    ensamblar_pavimentacion_aba(p, precios, items_ci, espesores, caps)
    ensamblar_pavimentacion_san(p, precios, items_ci, espesores, caps)
    ensamblar_acometidas(p, precios, caps)
    ensamblar_seguridad_gestion(p, caps, estado)

    # ── Numerar capítulos en orden de inserción ─────────────────────────────
    capitulos = {
        f"{i + 1:02d} {nombre}": datos
        for i, (nombre, datos) in enumerate(caps.items())
    }

    # ── Resumen financiero ──────────────────────────────────────────────────
    pem = sum(c["subtotal"] for c in capitulos.values())
    logger.info("── RESUMEN FINANCIERO ──")
    logger.info("PEM = %.2f € (materiales excluidos de GG/BI = %.2f €)", pem, estado["materiales_total"])
    fin = calcular_resumen(
        pem=pem,
        materiales=estado["materiales_total"],
        pct_gg=precios["pct_gg"],
        pct_bi=precios["pct_bi"],
        pct_iva=precios["pct_iva"],
    )
    logger.info("GG=%.2f BI=%.2f PBL_sin_IVA=%.2f IVA=%.2f TOTAL=%.2f €",
                fin.gg, fin.bi, fin.pbl_sin_iva, fin.iva, fin.total)

    for cap_nombre, cap_datos in capitulos.items():
        logger.debug("  %s: %.2f € - partidas: %s", cap_nombre, cap_datos["subtotal"],
                     {k: round(v, 2) for k, v in cap_datos["partidas"].items()})

    logger.info("═══ calcular_presupuesto FIN - TOTAL %.2f € ═══", fin.total)

    return {
        "capitulos": capitulos,
        "pem": fin.pem,
        "gg": fin.gg,
        "bi": fin.bi,
        "pbl_sin_iva": fin.pbl_sin_iva,
        "iva": fin.iva,
        "total": fin.total,
        "pcts": {
            "gg": precios["pct_gg"],
            "bi": precios["pct_bi"],
            "iva": precios["pct_iva"],
        },
        "pct_seguridad_info": round(p.pct_seguridad * 100, 2),
        "pct_gestion_info": round(p.pct_gestion * 100, 2),
        "auxiliares": {"aba": estado["aux_aba"] or {}, "san": estado["aux_san"] or {}},
        "trazabilidad": estado["trazabilidad"],
    }
