"""
Ensamblaje del presupuesto y resumen financiero.

Estructura oficial (hasta 9 capítulos):
  01  OBRA CIVIL ABASTECIMIENTO   — excavación, tubería, arriñonado, relleno,
                                    carga, transporte, entibación, pozos,
                                    valvulería, desmontaje, pozos existentes,
                                    conducción provisional, cánones
  02  OBRA CIVIL SANEAMIENTO      — ídem + imbornales, pozos existentes SAN
  03  PAVIMENTACIÓN ABASTECIMIENTO — demolición + reposición acerado/bordillo + sub-base
  04  PAVIMENTACIÓN SANEAMIENTO   — demolición + reposición calzada/acera + sub-base
  05  ACOMETIDAS ABASTECIMIENTO
  06  ACOMETIDAS SANEAMIENTO
  07  SEGURIDAD Y SALUD           — % sobre capítulos 01-06 (sin cánones/desmontaje)
  08  GESTIÓN AMBIENTAL           — % sobre capítulos 01-06 (sin cánones/desmontaje)
  09  MATERIALES                  — suministro puro ABA (excluido de GG/BI)

Resumen financiero (alineado con Excel EMASESA):
  PEM         = suma capítulos 01-09 (incluye materiales)
  base GG/BI  = PEM - MATERIALES     (Excel: GG/BI sobre J61, sin e)MATERIALES)
  GG          = base_GG/BI × pct_gg
  BI          = base_GG/BI × pct_bi
  PBL sin IVA = ROUNDUP((PEM + GG + BI) / 10) × 10
  IVA         = PBL × pct_iva
  TOTAL       = PBL + IVA
  Nota: PEM ya contiene materiales, solo se excluyen de la base GG/BI.
        Resultado = (PEM-mat)×(1+GG+BI) + mat = Excel J61+J62+J63+J64
"""

from __future__ import annotations

import math
from typing import Any

from src.config import ParametrosProyecto
from src.motor_experto import resolver_decisiones
from src.calcular import (
    capitulo_obra_civil_red,
    capitulo_pozos_registro,
    capitulo_valvuleria,
    capitulo_demolicion,
    capitulo_pavimentacion,
    capitulo_acometidas,
    capitulo_subbase,
    capitulo_desmontaje_tuberia,
    capitulo_imbornales,
    capitulo_pozos_existentes,
    capitulo_canones,
)


def _red_activa(item, longitud: float) -> bool:
    return item is not None and longitud > 0


def _merge(*resultados) -> tuple[float, dict] | None:
    """Fusiona varios resultados (subtotal, partidas) en uno solo.
    Ignora los None. Devuelve None si todos son None.
    """
    partidas: dict[str, float] = {}
    for res in resultados:
        if res is None:
            continue
        _, p = res
        for k, v in p.items():
            if k in partidas:
                partidas[k] += v
            else:
                partidas[k] = v
    if not partidas:
        return None
    return sum(partidas.values()), partidas


def _materiales_aba(longitud: float, item: dict,
                    decisiones_aba: dict) -> tuple[float, dict] | None:
    """Suministro puro ABA: tubería + valvulería + tapas. Se incluye en OBRA CIVIL ABA."""
    partidas: dict[str, float] = {}

    # 1. Tubería material — usa el item seleccionado directamente
    precio_mat_m = float(item.get("precio_material_m", 0.0) or 0.0)
    factor_piezas = float(item.get("factor_piezas", 1.0))
    if precio_mat_m > 0:
        partidas[item["label"] + " (suministro)"] = longitud * precio_mat_m * factor_piezas

    # 2. Valvulería material — usa los candidatos elegibles ya resueltos por el motor
    for v in decisiones_aba["valvuleria"]["items"]:
        intervalo = float(v.get("intervalo_m", 0))
        precio_mat = float(v.get("precio_material", 0.0) or 0.0)
        if intervalo <= 0 or precio_mat <= 0:
            continue
        n = longitud / intervalo
        partidas[v["label"] + " (material)"] = n * precio_mat * float(v.get("factor_piezas", 1.0))

    # 3. Tapa pozo registro material — usa el pozo ya seleccionado por el motor
    pozo_item = decisiones_aba["pozo_registro"]["item"]
    if pozo_item is not None:
        precio_tapa_mat = float(pozo_item.get("precio_tapa_material", 0.0) or 0.0)
        intervalo_poz = float(pozo_item.get("intervalo", 0))
        if precio_tapa_mat > 0 and intervalo_poz > 0:
            partidas["Tapa pozo registro ABA (material)"] = (longitud / intervalo_poz) * precio_tapa_mat

    if not partidas:
        return None
    return sum(partidas.values()), partidas


# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN FINANCIERO
# ═══════════════════════════════════════════════════════════════════════════════

def _resumen_financiero(capitulos: dict, pcts: dict,
                        materiales_excl_ggbi: float = 0.0) -> dict[str, Any]:
    """GG y BI sobre PEM sin materiales (Excel: J62-J63 sobre J61, sin e)MATERIALES)."""
    pem = sum(c["subtotal"] for c in capitulos.values())
    base_gg_bi = pem - materiales_excl_ggbi
    gg = base_gg_bi * pcts["gg"]
    bi = base_gg_bi * pcts["bi"]
    pbl_sin_iva = math.ceil((pem + gg + bi) / 10) * 10  # ROUNDUP a decena (Excel J66)
    iva = pbl_sin_iva * pcts["iva"]
    total = pbl_sin_iva + iva
    return {
        "pem": pem,
        "gg": gg,
        "bi": bi,
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def calcular_presupuesto(p: ParametrosProyecto, precios: dict) -> dict[str, Any]:
    pcts = {"gg": precios["pct_gg"], "bi": precios["pct_bi"], "iva": precios["pct_iva"]}
    espesores = precios["espesores_calzada"]

    aba_activa = _red_activa(p.aba_item, p.aba_longitud_m)
    san_activa = _red_activa(p.san_item, p.san_longitud_m)

    # Usamos dict sin número para acumular; se numeran al final
    _caps: dict[str, dict] = {}
    aux_aba = aux_san = None

    # ── Tracking para alinear con Excel EMASESA ──────────────────────────────
    # Cánones y desmontaje van en OBRA CIVIL (para display y GG/BI) pero se
    # excluyen del % de S&S (Excel: S&S = pct × (K12+K22+K38), sin d)OTROS)
    _excluir_de_base_ss = 0.0
    # Materiales se muestran en capítulo aparte y se excluyen de GG/BI
    # (Excel: materiales se suman DESPUÉS de GG/BI, no forman parte de J61)
    _materiales_total = 0.0

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _demo_items(red: str) -> tuple[dict | None, dict | None]:
        cat = precios.get(f"demolicion_{red.lower()}", [])
        by_unit: dict[str, dict] = {}
        for item in cat:
            u = item.get("unidad", "")
            if u in by_unit:
                raise ValueError(
                    f"El catálogo 'demolicion_{red.lower()}' tiene unidad duplicada '{u}'."
                )
            by_unit[u] = item
        return by_unit.get("m2"), by_unit.get("m")

    def _add(nombre: str, resultado: tuple[float, dict] | None) -> None:
        if resultado is None:
            return
        subtotal, partidas = resultado
        if nombre in _caps:
            _caps[nombre]["partidas"].update(partidas)
            _caps[nombre]["subtotal"] += subtotal
        else:
            _caps[nombre] = {"subtotal": subtotal, "partidas": dict(partidas)}

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 01 — OBRA CIVIL ABASTECIMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    if aba_activa:
        decisiones_aba = resolver_decisiones(
            tipo_tuberia=p.aba_item["tipo"],
            diametro_mm=int(p.aba_item["diametro_mm"]),
            red="ABA",
            profundidad=p.aba_profundidad_m,
            precios=precios,
            instalacion=p.instalacion_valvuleria,
            desmontaje_tipo=p.desmontaje_tipo,
        )

        # Excavación, tubería, arriñonado, relleno, carga, transporte, entibación
        cap_aba, partidas_aba, aux_aba = capitulo_obra_civil_red(
            p.aba_longitud_m, p.aba_profundidad_m, p.aba_item, precios,
            pct_manual=p.pct_manual,
            espesor_pavimento_m=p.espesor_pavimento_m,
            entibacion_item=decisiones_aba["entibacion"]["item"],
        )
        _add("OBRA CIVIL ABASTECIMIENTO", (cap_aba, partidas_aba))

        # Cánones (en obra civil para display/GG/BI, excluidos de base S&S)
        canon_aba = capitulo_canones(
            aux_aba.get("canon_tierras", 0.0),
            aux_aba.get("canon_mixto", 0.0),
        )
        _add("OBRA CIVIL ABASTECIMIENTO", canon_aba)
        if canon_aba is not None:
            _excluir_de_base_ss += canon_aba[0]

        # Pozos de registro
        _add("OBRA CIVIL ABASTECIMIENTO",
             capitulo_pozos_registro(p.aba_longitud_m, False, precios,
                                     profundidad=p.aba_profundidad_m,
                                     diametro_mm=int(p.aba_item["diametro_mm"]),
                                     pozo_item=decisiones_aba["pozo_registro"]["item"]))

        # Valvulería
        _add("OBRA CIVIL ABASTECIMIENTO",
             capitulo_valvuleria(p.aba_longitud_m, p.aba_item["diametro_mm"],
                                  precios, instalacion=p.instalacion_valvuleria,
                                  valvuleria_items=decisiones_aba["valvuleria"]["items"]))

        # Desmontaje tubería existente (en obra civil, excluido de base S&S)
        if p.desmontaje_tipo != "none":
            _desmontaje_res = capitulo_desmontaje_tuberia(
                p.aba_longitud_m, int(p.aba_item["diametro_mm"]),
                p.desmontaje_tipo, precios,
                desmontaje_item=decisiones_aba["desmontaje"]["item"])
            _add("OBRA CIVIL ABASTECIMIENTO", _desmontaje_res)
            if _desmontaje_res is not None:
                _excluir_de_base_ss += _desmontaje_res[0]

        # Pozos existentes ABA
        if p.pozos_existentes_aba != "none":
            _add("OBRA CIVIL ABASTECIMIENTO",
                 capitulo_pozos_existentes(p.aba_longitud_m, "ABA",
                                            p.pozos_existentes_aba, precios))

        # Conducción provisional
        if p.conduccion_provisional_m > 0:
            precio_cp = float(precios.get("conduccion_provisional_precio_m", 12.0))
            importe_cp = p.conduccion_provisional_m * precio_cp
            if importe_cp > 0:
                _add("OBRA CIVIL ABASTECIMIENTO",
                     (importe_cp, {"Conducción provisional PE": importe_cp}))

        # Materiales ABA — capítulo separado, excluido de base S&S y GG/BI
        # (Excel: e)MATERIALES se suma DESPUÉS de GG/BI, no entra en J61)
        _mat_res = _materiales_aba(p.aba_longitud_m, p.aba_item, decisiones_aba)
        if _mat_res is not None:
            _materiales_total += _mat_res[0]
            _add("MATERIALES", _mat_res)

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 02 — OBRA CIVIL SANEAMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    if san_activa:
        decisiones_san = resolver_decisiones(
            tipo_tuberia=p.san_item["tipo"],
            diametro_mm=int(p.san_item["diametro_mm"]),
            red="SAN",
            profundidad=p.san_profundidad_m,
            precios=precios,
            instalacion="enterrada",
            desmontaje_tipo="none",
        )

        cap_san, partidas_san, aux_san = capitulo_obra_civil_red(
            p.san_longitud_m, p.san_profundidad_m, p.san_item, precios,
            es_san=True, pct_manual=p.pct_manual,
            espesor_pavimento_m=p.espesor_pavimento_m,
            entibacion_item=decisiones_san["entibacion"]["item"],
        )
        _add("OBRA CIVIL SANEAMIENTO", (cap_san, partidas_san))

        # Cánones (en obra civil para display/GG/BI, excluidos de base S&S)
        canon_san = capitulo_canones(
            aux_san.get("canon_tierras", 0.0),
            aux_san.get("canon_mixto", 0.0),
        )
        _add("OBRA CIVIL SANEAMIENTO", canon_san)
        if canon_san is not None:
            _excluir_de_base_ss += canon_san[0]

        # Pozos de registro SAN
        _add("OBRA CIVIL SANEAMIENTO",
             capitulo_pozos_registro(p.san_longitud_m, True, precios,
                                     profundidad=p.san_profundidad_m,
                                     diametro_mm=int(p.san_item["diametro_mm"]),
                                     pozo_item=decisiones_san["pozo_registro"]["item"]))

        # Imbornales
        if p.imbornales_tipo != "none":
            _add("OBRA CIVIL SANEAMIENTO",
                 capitulo_imbornales(p.san_longitud_m, p.imbornales_tipo,
                                      p.imbornales_nuevo_label, precios))

        # Pozos existentes SAN
        if p.pozos_existentes_san != "none":
            _add("OBRA CIVIL SANEAMIENTO",
                 capitulo_pozos_existentes(p.san_longitud_m, "SAN",
                                            p.pozos_existentes_san, precios))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 03 — PAVIMENTACIÓN ABASTECIMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    if aba_activa:
        # Demolición ABA — validar que existen items cuando hay superficie
        demo_m2_aba, demo_m_aba = _demo_items("ABA")
        cat_aba_demo = precios.get("demolicion_aba", [])
        if cat_aba_demo:
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
        _add("PAVIMENTACIÓN ABASTECIMIENTO",
             capitulo_demolicion(p.pav_aba_acerado_m2, demo_m2_aba,
                                  p.pav_aba_bordillo_m, demo_m_aba))

        # Reposición acerado + bordillo
        _add("PAVIMENTACIÓN ABASTECIMIENTO",
             capitulo_pavimentacion(p.pav_aba_acerado_m2, p.pav_aba_acerado_item,
                                     p.pav_aba_bordillo_m, p.pav_aba_bordillo_item))

        # Sub-base ABA
        if p.subbase_aba_espesor_m > 0:
            _add("PAVIMENTACIÓN ABASTECIMIENTO",
                 capitulo_subbase(p.pav_aba_acerado_m2, p.subbase_aba_espesor_m,
                                   p.subbase_aba_item))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 04 — PAVIMENTACIÓN SANEAMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    if san_activa:
        # Demolición SAN — validar que existen items cuando hay superficie
        cat_san_demo = precios.get("demolicion_san", [])
        item_calzada = next((i for i in cat_san_demo if "calzada" in i.get("label", "").lower()), None)
        item_acera = next((i for i in cat_san_demo if "acerado" in i.get("label", "").lower() or
                           "acera" in i.get("label", "").lower()), None)
        if cat_san_demo:
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
        _add("PAVIMENTACIÓN SANEAMIENTO",
             capitulo_demolicion(p.pav_san_calzada_m2, item_calzada,
                                  p.pav_san_acera_m2, item_acera))

        # Reposición calzada + acera (SAN usa ×1.5 en espesores — Excel: 0.015 vs 0.01)
        _add("PAVIMENTACIÓN SANEAMIENTO",
             capitulo_pavimentacion(p.pav_san_calzada_m2, p.pav_san_calzada_item,
                                     p.pav_san_acera_m2, p.pav_san_acera_item,
                                     calzada_conversion=True, espesores=espesores,
                                     factor_calzada_san=1.5))

        # Sub-base SAN
        if p.subbase_san_espesor_m > 0:
            _add("PAVIMENTACIÓN SANEAMIENTO",
                 capitulo_subbase(p.pav_san_calzada_m2 + p.pav_san_acera_m2,
                                   p.subbase_san_espesor_m, p.subbase_san_item))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 05 — ACOMETIDAS ABASTECIMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    if aba_activa:
        acometidas_aba = precios["acometidas_aba_tipos"]
        _tipo_aba = precios["acometida_aba_defecto"]
        if _tipo_aba not in acometidas_aba:
            raise ValueError(
                f"El tipo de acometida ABA por defecto '{_tipo_aba}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        factor_aba = float(precios.get("acometidas_aba_factores", {}).get(_tipo_aba, 1.2))
        _add("ACOMETIDAS ABASTECIMIENTO",
             capitulo_acometidas(p.acometidas_aba_n, acometidas_aba[_tipo_aba],
                                  "Acometidas ABA", factor=factor_aba))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 06 — ACOMETIDAS SANEAMIENTO
    # ══════════════════════════════════════════════════════════════════════════
    if san_activa:
        acometidas_san = precios["acometidas_san_tipos"]
        _tipo_san = precios["acometida_san_defecto"]
        if _tipo_san not in acometidas_san:
            raise ValueError(
                f"El tipo de acometida SAN por defecto '{_tipo_san}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        _add("ACOMETIDAS SANEAMIENTO",
             capitulo_acometidas(p.acometidas_san_n, acometidas_san[_tipo_san],
                                  "Acometidas SAN", factor=1.0))

    # ══════════════════════════════════════════════════════════════════════════
    # Base S&S = suma de todos los capítulos de trabajo (OBRA CIVIL + PAV + ACOM)
    # ══════════════════════════════════════════════════════════════════════════
    _base_ss_keys = {
        "OBRA CIVIL ABASTECIMIENTO", "OBRA CIVIL SANEAMIENTO",
        "PAVIMENTACIÓN ABASTECIMIENTO", "PAVIMENTACIÓN SANEAMIENTO",
        "ACOMETIDAS ABASTECIMIENTO", "ACOMETIDAS SANEAMIENTO",
    }
    # Excel: S&S = pct × (K12+K22+K38) — sin cánones ni desmontaje (d)OTROS)
    base_ss = max(0.0,
                  sum(c["subtotal"] for nombre, c in _caps.items() if nombre in _base_ss_keys)
                  - _excluir_de_base_ss)

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO — SEGURIDAD Y SALUD
    # ══════════════════════════════════════════════════════════════════════════
    if p.pct_seguridad > 0:
        importe_ss = base_ss * p.pct_seguridad
        _add("SEGURIDAD Y SALUD", (importe_ss, {"Seguridad y Salud": importe_ss}))

    if p.pct_servicios_afectados > 0:
        importe_sa = base_ss * p.pct_servicios_afectados
        _add("SEGURIDAD Y SALUD", (importe_sa, {"Servicios afectados": importe_sa}))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO — GESTIÓN AMBIENTAL
    # ══════════════════════════════════════════════════════════════════════════
    if p.pct_gestion > 0:
        importe_ga = base_ss * p.pct_gestion
        _add("GESTIÓN AMBIENTAL", (importe_ga, {"Gestión ambiental": importe_ga}))

    # ── Numerar capítulos secuencialmente según orden de inserción ─────────────
    capitulos = {
        f"{i + 1:02d} {nombre}": datos
        for i, (nombre, datos) in enumerate(_caps.items())
    }

    # ── Resumen financiero ─────────────────────────────────────────────────────
    fin = _resumen_financiero(capitulos, pcts,
                              materiales_excl_ggbi=_materiales_total)

    return {
        "capitulos": capitulos,
        **fin,
        "pcts": pcts,
        "pct_seguridad_info": round(p.pct_seguridad * 100, 2),
        "pct_gestion_info": round(p.pct_gestion * 100, 2),
        "auxiliares": {"aba": aux_aba or {}, "san": aux_san or {}},
    }
