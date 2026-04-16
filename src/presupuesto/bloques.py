"""
Bloques de ensamblaje - construyen cada sección del presupuesto.

Cada función ensambla un capítulo completo llamando a las funciones
de cálculo de capitulos_obra_civil y capitulos_superficie, y acumula
los resultados en el dict compartido `caps`.

ensamblaje.py orquesta la secuencia; este módulo define los bloques.
"""

from __future__ import annotations

import logging
from typing import Any

from src.domain.parametros import ParametrosProyecto
from src.presupuesto.capitulos_obra_civil import (
    capitulo_obra_civil,
    capitulo_pozos_registro,
    capitulo_valvuleria,
    capitulo_desmontaje,
    capitulo_imbornales,
    capitulo_pozos_existentes,
    capitulo_canones,
)
from src.presupuesto.capitulos_superficie import (
    capitulo_demolicion,
    capitulo_pavimentacion,
    capitulo_acometidas,
    capitulo_subbase,
)
from src.presupuesto.materiales import (
    materiales_aba as _materiales_aba,
    materiales_san as _materiales_san,
    demo_items as _demo_items,
)

logger = logging.getLogger(__name__)


def _acumular(caps: dict, nombre: str, resultado: tuple[float, dict] | None) -> None:
    if resultado is None:
        logger.debug("[ACUM] '%s' → resultado=None, nada que acumular", nombre)
        return
    subtotal, partidas = resultado
    if subtotal == 0.0:
        logger.warning("[ACUM] '%s' tiene subtotal=0.0 con %d partidas: %s",
                       nombre, len(partidas), list(partidas.keys()))
    if nombre in caps:
        caps[nombre]["partidas"].update(partidas)
        caps[nombre]["subtotal"] += subtotal
        logger.debug("[ACUM] '%s' +%.2f € → acumulado=%.2f €",
                     nombre, subtotal, caps[nombre]["subtotal"])
    else:
        caps[nombre] = {"subtotal": subtotal, "partidas": dict(partidas)}
        logger.debug("[ACUM] '%s' nuevo → %.2f € (%d partidas)",
                     nombre, subtotal, len(partidas))


def ensamblar_obra_civil_aba(
    p: ParametrosProyecto,
    precios: dict,
    _aba_item: dict | None,
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
        _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", _mat)
        logger.debug("[ABA] Materiales ABA: %.2f € (excluidos de GG/BI)", _mat[0])

    _sub_aba = caps.get("OBRA CIVIL ABASTECIMIENTO", {}).get("subtotal", 0)
    logger.info("[ABA] SUBTOTAL CAP 01: %.2f €", _sub_aba)


def ensamblar_obra_civil_san(
    p: ParametrosProyecto,
    precios: dict,
    _san_item: dict | None,
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
        _acumular(caps, "OBRA CIVIL SANEAMIENTO", _mat_san)

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


def ensamblar_pavimentacion_aba(
    p: ParametrosProyecto,
    precios: dict,
    items_ci: dict,
    espesores: dict,
    caps: dict,
) -> None:
    """Capítulo 03 - Pavimentación Abastecimiento."""
    if not p.aba_activa:
        return

    logger.info("── CAP 03: PAVIMENTACIÓN ABA ──")
    logger.debug("[PAV-ABA] acerado_m2=%.2f bordillo_m=%.2f subbase_esp=%.3f",
                 p.pav_aba_acerado_m2, p.pav_aba_bordillo_m, p.subbase_aba_espesor_m)
    demo_m2_aba, demo_m_aba = _demo_items("ABA", precios)
    cat_demo_aba = precios.get("demolicion_aba", [])
    if cat_demo_aba:
        if p.pav_aba_acerado_m2 > 0 and demo_m2_aba is None:
            raise ValueError(
                "Hay superficie de acerado ABA a demoler pero demolicion_aba "
                "no tiene ningún item con unidad 'm2'."
            )
        if p.pav_aba_bordillo_m > 0 and demo_m_aba is None:
            raise ValueError(
                "Hay longitud de bordillo ABA a demoler pero demolicion_aba "
                "no tiene ningún item con unidad 'm'."
            )
    _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
              capitulo_demolicion(p.pav_aba_acerado_m2, demo_m2_aba,
                                  p.pav_aba_bordillo_m, demo_m_aba,
                                  factor_item1=1.2))   # Excel J7: precio×1.2
    _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
              capitulo_pavimentacion(p.pav_aba_acerado_m2, items_ci["pav_aba_acerado_item"],
                                     p.pav_aba_bordillo_m, items_ci["pav_aba_bordillo_item"],
                                     factor_item1=1.0))
    # Calzada ABA (demolición + reposición)
    if p.pav_aba_calzada_m2 > 0:
        demo_calzada_aba = next(
            (i for i in cat_demo_aba if "calzada" in i.get("label", "").lower()), None)
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_demolicion(p.pav_aba_calzada_m2, demo_calzada_aba,
                                      0, None))
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_pavimentacion(p.pav_aba_calzada_m2, items_ci["pav_aba_calzada_item"],
                                         0, items_ci["pav_aba_bordillo_item"],
                                         calzada_conversion=True,
                                         espesores=espesores))
    if p.subbase_aba_espesor_m > 0:
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_subbase(p.pav_aba_acerado_m2 + p.pav_aba_calzada_m2,
                                   p.subbase_aba_espesor_m, items_ci["subbase_aba_item"]))

    _sub_pav_aba = caps.get("PAVIMENTACIÓN ABASTECIMIENTO", {}).get("subtotal", 0)
    logger.info("[PAV-ABA] SUBTOTAL CAP 03: %.2f €", _sub_pav_aba)


def ensamblar_pavimentacion_san(
    p: ParametrosProyecto,
    precios: dict,
    items_ci: dict,
    espesores: dict,
    caps: dict,
) -> None:
    """Capítulo 04 - Pavimentación Saneamiento."""
    if not p.san_activa:
        return

    logger.info("── CAP 04: PAVIMENTACIÓN SAN ──")
    logger.debug("[PAV-SAN] calzada_m2=%.2f acera_m2=%.2f subbase_esp=%.3f",
                 p.pav_san_calzada_m2, p.pav_san_acera_m2, p.subbase_san_espesor_m)
    cat_demo_san = precios.get("demolicion_san", [])
    item_calzada = next(
        (i for i in cat_demo_san if "calzada" in i.get("label", "").lower()), None)
    item_acera = next(
        (i for i in cat_demo_san
         if "acerado" in i.get("label", "").lower()
         or "acera" in i.get("label", "").lower()), None)
    if cat_demo_san:
        if p.pav_san_calzada_m2 > 0 and item_calzada is None:
            raise ValueError(
                "Hay superficie de calzada SAN a demoler pero demolicion_san "
                "no tiene ningún item con 'calzada' en el label."
            )
        if p.pav_san_acera_m2 > 0 and item_acera is None:
            raise ValueError(
                "Hay superficie de acerado SAN a demoler pero demolicion_san "
                "no tiene ningún item con 'acerado' o 'acera' en el label."
            )
    _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
              capitulo_demolicion(p.pav_san_calzada_m2, item_calzada,
                                  p.pav_san_acera_m2, item_acera))
    _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
              capitulo_pavimentacion(p.pav_san_calzada_m2, items_ci["pav_san_calzada_item"],
                                     p.pav_san_acera_m2, items_ci["pav_san_acera_item"],
                                     calzada_conversion=True, espesores=espesores,
                                     factor_item1=1.0))
    if p.subbase_san_espesor_m > 0:
        _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
                  capitulo_subbase(p.pav_san_calzada_m2 + p.pav_san_acera_m2,
                                   p.subbase_san_espesor_m, items_ci["subbase_san_item"]))

    _sub_pav_san = caps.get("PAVIMENTACIÓN SANEAMIENTO", {}).get("subtotal", 0)
    logger.info("[PAV-SAN] SUBTOTAL CAP 04: %.2f €", _sub_pav_san)


def ensamblar_acometidas(
    p: ParametrosProyecto,
    precios: dict,
    caps: dict,
) -> None:
    """Capítulos 05-06 - Acometidas ABA y SAN."""
    if p.aba_activa:
        logger.info("── CAP 05: ACOMETIDAS ABA ──")
        acometidas_aba = precios["acometidas_aba_tipos"]
        tipo_aba = precios["acometida_aba_defecto"]
        if tipo_aba not in acometidas_aba:
            raise ValueError(
                f"El tipo de acometida ABA por defecto '{tipo_aba}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        factor_aba = float(precios.get("acometidas_aba_factores", {}).get(tipo_aba, 1.2))
        logger.debug("[ACOM-ABA] n=%d tipo=%s precio=%.2f factor=%.2f",
                     p.acometidas_aba_n, tipo_aba, acometidas_aba[tipo_aba], factor_aba)
        _acumular(caps, "ACOMETIDAS ABASTECIMIENTO",
                  capitulo_acometidas(p.acometidas_aba_n,
                                      acometidas_aba[tipo_aba],
                                      "Acometidas ABA", factor=factor_aba))

    if p.san_activa:
        logger.info("── CAP 06: ACOMETIDAS SAN ──")
        acometidas_san = precios["acometidas_san_tipos"]
        tipo_san = precios["acometida_san_defecto"]
        if tipo_san not in acometidas_san:
            raise ValueError(
                f"El tipo de acometida SAN por defecto '{tipo_san}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        factor_san = float(precios.get("acometidas_san_factores", {}).get(tipo_san, 1.0))
        logger.debug("[ACOM-SAN] n=%d tipo=%s precio=%.2f factor=%.2f",
                     p.acometidas_san_n, tipo_san, acometidas_san[tipo_san], factor_san)
        _acumular(caps, "ACOMETIDAS SANEAMIENTO",
                  capitulo_acometidas(p.acometidas_san_n,
                                      acometidas_san[tipo_san],
                                      "Acometidas SAN", factor=factor_san))


def ensamblar_seguridad_gestion(
    p: ParametrosProyecto,
    caps: dict,
    estado: dict,
) -> None:
    """Capítulos 07-08 - Seguridad y Salud / Gestión Ambiental."""
    _base_ss_keys = {
        "OBRA CIVIL ABASTECIMIENTO", "OBRA CIVIL SANEAMIENTO",
        "PAVIMENTACIÓN ABASTECIMIENTO", "PAVIMENTACIÓN SANEAMIENTO",
        "ACOMETIDAS ABASTECIMIENTO", "ACOMETIDAS SANEAMIENTO",
    }
    _suma_bruta = sum(c["subtotal"] for nombre, c in caps.items() if nombre in _base_ss_keys)
    base_ss = max(0.0, _suma_bruta - estado["excluir_ss"] - estado["materiales_total"])
    logger.info("── CAPS 07-08: S&S / GA ──")
    logger.debug("base_ss = suma_caps(%.2f) - excluir_ss(%.2f) - materiales(%.2f) = %.2f",
                 _suma_bruta, estado["excluir_ss"], estado["materiales_total"], base_ss)

    if p.pct_seguridad > 0:
        importe_ss = base_ss * p.pct_seguridad
        _acumular(caps, "SEGURIDAD Y SALUD",
                  (importe_ss, {"Seguridad y Salud": importe_ss}))

    if p.pct_servicios_afectados > 0:
        importe_sa = base_ss * p.pct_servicios_afectados
        _acumular(caps, "SEGURIDAD Y SALUD",
                  (importe_sa, {"Servicios afectados": importe_sa}))

    if p.pct_gestion > 0:
        importe_ga = base_ss * p.pct_gestion
        _acumular(caps, "GESTIÓN AMBIENTAL",
                  (importe_ga, {"Gestión ambiental": importe_ga}))
