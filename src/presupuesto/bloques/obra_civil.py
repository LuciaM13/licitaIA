"""Capítulos 01-02: Obra Civil ABA y SAN.

Estos dos bloques ensamblan el grueso del presupuesto: tubería + zanja +
arena + relleno + entibación + pozos de registro + valvulería (ABA) +
imbornales (SAN) + pozos existentes + materiales propios.

Convención EMASESA crítica: los **materiales ABA** se acumulan en
``estado["materiales_aba_total"]`` y se excluyen de la base GG/BI; los
**materiales SAN** se acumulan en ``estado["materiales_san_total"]`` y
SÍ se incluyen en GG/BI. Los cánones de vertido y el desmontaje se
excluyen de la base S&S vía ``estado["excluir_ss"]``.
"""

from __future__ import annotations

import logging

from src.modelo.parametros import ParametrosProyecto
from src.modelo.tipos import ItemCatalogo, Precios
from src.presupuesto.bloques._comun import _acumular
from src.presupuesto.capitulos_obra_civil import (
    capitulo_canones,
    capitulo_desmontaje,
    capitulo_imbornales,
    capitulo_obra_civil,
    capitulo_pozos_existentes,
    capitulo_pozos_registro,
    capitulo_valvuleria,
)
from src.presupuesto.materiales import (
    materiales_aba as _materiales_aba,
    materiales_san as _materiales_san,
)

logger = logging.getLogger(__name__)


def ensamblar_obra_civil_aba(
    p: ParametrosProyecto,
    precios: Precios,
    _aba_item: ItemCatalogo | None,
    caps: dict,
    estado: dict,
    decisiones_aba: dict,
) -> None:
    """Capítulo 01 - Obra Civil Abastecimiento."""
    if not p.aba_activa:
        return

    logger.info("── CAP 01: OBRA CIVIL ABA ──")
    estado["trazabilidad"]["ABA"] = decisiones_aba.get("trazabilidad", [])
    logger.debug("[ABA] Decisiones CLIPS: entib=%s pozo=%s valv=%d items desm=%s",
                 decisiones_aba["entibacion"]["item"]["label"] if decisiones_aba["entibacion"]["item"] else None,
                 decisiones_aba["pozo_registro"]["item"]["label"] if decisiones_aba["pozo_registro"]["item"] else None,
                 len(decisiones_aba["valvuleria"]["items"]),
                 decisiones_aba["desmontaje"]["item"]["label"] if decisiones_aba["desmontaje"]["item"] else None)

    # Obra civil base (excavación, tubería, arriñonado, relleno, entibación)
    cap_aba, partidas_aba, aux_aba = capitulo_obra_civil(
        p.aba_longitud_m, p.aba_profundidad_m, _aba_item, precios,
        pct_manual=p.pct_manual,
        espesor_pavimento_m=p.espesor_pavimento_m,
        entibacion_item=decisiones_aba["entibacion"]["item"],
    )
    estado["aux_aba"] = aux_aba
    _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", (cap_aba, partidas_aba))
    logger.debug("[ABA] Obra civil base: %.2f € (%d partidas)", cap_aba, len(partidas_aba))
    logger.debug("[ABA] Aux: %s", {k: round(v, 4) if isinstance(v, float) else v for k, v in aux_aba.items()})

    # Cánones (se muestran en obra civil pero se excluyen de base S&S)
    canon_aba = capitulo_canones(
        aux_aba.get("canon_tierras", 0.0),
        aux_aba.get("canon_mixto", 0.0),
    )
    _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", canon_aba)
    if canon_aba:
        estado["excluir_ss"] += canon_aba[0]
        logger.debug("[ABA] Cánones: %.2f € (excluidos de base S&S)", canon_aba[0])
    else:
        logger.debug("[ABA] Sin cánones")

    # Pozos de registro ABA
    _acumular(caps, "OBRA CIVIL ABASTECIMIENTO",
              capitulo_pozos_registro(
                  p.aba_longitud_m, p.aba_profundidad_m, p.aba_diametro_mm, precios,
                  pozo_item=decisiones_aba["pozo_registro"]["item"]))

    # Valvulería ABA
    _acumular(caps, "OBRA CIVIL ABASTECIMIENTO",
              capitulo_valvuleria(
                  p.aba_longitud_m, p.aba_diametro_mm, precios,
                  instalacion=p.instalacion_valvuleria,
                  valvuleria_items=decisiones_aba["valvuleria"]["items"]))

    # Desmontaje tubería existente (excluido de base S&S)
    logger.debug("[ABA] Desmontaje tipo=%s", p.desmontaje_tipo)
    if p.desmontaje_tipo != "none":
        _desm = capitulo_desmontaje(
            p.aba_longitud_m, precios,
            desmontaje_item=decisiones_aba["desmontaje"]["item"])
        _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", _desm)
        if _desm:
            estado["excluir_ss"] += _desm[0]
            logger.debug("[ABA] Desmontaje: %.2f € (excluido de base S&S)", _desm[0])
        else:
            logger.debug("[ABA] Desmontaje: item resuelto pero capítulo=None")

    # Pozos existentes ABA
    if p.pozos_existentes_aba != "none":
        _acumular(caps, "OBRA CIVIL ABASTECIMIENTO",
                  capitulo_pozos_existentes(
                      p.aba_longitud_m, p.pozos_existentes_aba, "ABA", precios))

    # Conducción provisional
    if p.conduccion_provisional_m > 0:
        precio_cp = float(precios.get("conduccion_provisional_precio_m", 12.0))
        importe_cp = p.conduccion_provisional_m * precio_cp
        if importe_cp > 0:
            _acumular(caps, "OBRA CIVIL ABASTECIMIENTO",
                      (importe_cp, {"Conducción provisional PE": importe_cp}))

    # Materiales ABA - van dentro del cap. 01, excluidos de GG/BI
    # (sección e) del CUADRO RESUMEN del Excel EMASESA)
    _mat = _materiales_aba(p.aba_longitud_m, _aba_item, decisiones_aba)
    if _mat:
        estado["materiales_total"] += _mat[0]
        estado["materiales_aba_total"] += _mat[0]
        _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", _mat)
        logger.debug("[ABA] Materiales ABA: %.2f € (excluidos de GG/BI)", _mat[0])

    _sub_aba = caps.get("OBRA CIVIL ABASTECIMIENTO", {}).get("subtotal", 0)
    logger.info("[ABA] SUBTOTAL CAP 01: %.2f €", _sub_aba)


def ensamblar_obra_civil_san(
    p: ParametrosProyecto,
    precios: Precios,
    _san_item: ItemCatalogo | None,
    caps: dict,
    estado: dict,
    decisiones_san: dict,
) -> None:
    """Capítulo 02 - Obra Civil Saneamiento."""
    if not p.san_activa:
        logger.info("SAN no activa - omitiendo capítulo 02")
        return

    logger.info("── CAP 02: OBRA CIVIL SAN ──")
    # SAN no tiene valvulería ni desmontaje → solo entibación (idx 0) y pozo (idx 1)
    _traz_san = decisiones_san.get("trazabilidad", [])
    estado["trazabilidad"]["SAN"] = _traz_san[:2] if len(_traz_san) >= 2 else _traz_san
    logger.debug("[SAN] Decisiones CLIPS: entib=%s pozo=%s",
                 decisiones_san["entibacion"]["item"]["label"] if decisiones_san["entibacion"]["item"] else None,
                 decisiones_san["pozo_registro"]["item"]["label"] if decisiones_san["pozo_registro"]["item"] else None)

    cap_san, partidas_san, aux_san = capitulo_obra_civil(
        p.san_longitud_m, p.san_profundidad_m, _san_item, precios,
        es_san=True,
        pct_manual=p.pct_manual,
        espesor_pavimento_m=p.espesor_pavimento_m,
        entibacion_item=decisiones_san["entibacion"]["item"],
    )
    estado["aux_san"] = aux_san
    _acumular(caps, "OBRA CIVIL SANEAMIENTO", (cap_san, partidas_san))
    logger.debug("[SAN] Obra civil base: %.2f € (%d partidas)", cap_san, len(partidas_san))

    canon_san = capitulo_canones(
        aux_san.get("canon_tierras", 0.0),
        aux_san.get("canon_mixto", 0.0),
    )
    _acumular(caps, "OBRA CIVIL SANEAMIENTO", canon_san)
    if canon_san:
        estado["excluir_ss"] += canon_san[0]

    # Pozos de registro SAN
    _acumular(caps, "OBRA CIVIL SANEAMIENTO",
              capitulo_pozos_registro(
                  p.san_longitud_m, p.san_profundidad_m, p.san_diametro_mm, precios,
                  es_san=True,
                  pozo_item=decisiones_san["pozo_registro"]["item"]))

    # Materiales SAN - van dentro del cap. 02, excluidos de GG/BI
    # (sección e) del CUADRO RESUMEN del Excel EMASESA)
    _mat_san = _materiales_san(
        p.san_longitud_m, p.san_profundidad_m,
        decisiones_san["pozo_registro"]["item"])
    if _mat_san:
        estado["materiales_total"] += _mat_san[0]
        estado["materiales_san_total"] += _mat_san[0]
        _acumular(caps, "OBRA CIVIL SANEAMIENTO", _mat_san)
        logger.debug("[SAN] Materiales SAN: %.2f € (incluidos en base GG/BI)", _mat_san[0])

    # Imbornales
    if p.imbornales_tipo != "none":
        _acumular(caps, "OBRA CIVIL SANEAMIENTO",
                  capitulo_imbornales(
                      p.san_longitud_m, p.imbornales_tipo,
                      p.imbornales_nuevo_label, precios))

    # Pozos existentes SAN
    if p.pozos_existentes_san != "none":
        _acumular(caps, "OBRA CIVIL SANEAMIENTO",
                  capitulo_pozos_existentes(
                      p.san_longitud_m, p.pozos_existentes_san, "SAN", precios))

    _sub_san = caps.get("OBRA CIVIL SANEAMIENTO", {}).get("subtotal", 0)
    logger.info("[SAN] SUBTOTAL CAP 02: %.2f €", _sub_san)
