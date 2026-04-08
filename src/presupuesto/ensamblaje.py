"""
Ensamblaje del presupuesto — orquesta capítulos y resumen financiero.

Este es el único módulo que importa tanto de src.reglas como de src.presupuesto.capitulos.
La UI (pages/) solo llama a calcular_presupuesto() desde aquí.

Estructura de capítulos:
  01 OBRA CIVIL ABASTECIMIENTO   — excavación, tubería, arriñonado, entibación,
                                   valvulería, pozos, desmontaje, cánones
  02 OBRA CIVIL SANEAMIENTO      — idem + imbornales, pozos existentes SAN
  03 PAVIMENTACIÓN ABASTECIMIENTO — demolición + reposición acerado/bordillo + sub-base
  04 PAVIMENTACIÓN SANEAMIENTO   — demolición + reposición calzada/acera + sub-base
  05 ACOMETIDAS ABASTECIMIENTO
  06 ACOMETIDAS SANEAMIENTO
  07 SEGURIDAD Y SALUD           — % sobre base de obra (sin cánones/desmontaje)
  08 GESTIÓN AMBIENTAL           — % sobre base de obra (sin cánones/desmontaje)
  09 MATERIALES                  — suministro puro ABA (excluido de GG/BI)
"""

from __future__ import annotations

from typing import Any

from src.domain.parametros import ParametrosProyecto
from src.domain.financiero import calcular_resumen
from src.reglas.motor import resolver_decisiones
from src.presupuesto.capitulos import (
    capitulo_obra_civil,
    capitulo_pozos_registro,
    capitulo_valvuleria,
    capitulo_demolicion,
    capitulo_pavimentacion,
    capitulo_acometidas,
    capitulo_subbase,
    capitulo_desmontaje,
    capitulo_imbornales,
    capitulo_pozos_existentes,
    capitulo_canones,
)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _materiales_aba(
    longitud: float, item: dict, decisiones: dict
) -> tuple[float, dict] | None:
    """Suministro de material puro ABA (excluido de base GG/BI)."""
    partidas: dict[str, float] = {}

    precio_mat_m = float(item.get("precio_material_m", 0.0) or 0.0)
    factor_piezas = float(item.get("factor_piezas", 1.0))
    if precio_mat_m > 0:
        partidas[item["label"] + " (suministro)"] = longitud * precio_mat_m * factor_piezas

    for v in decisiones["valvuleria"]["items"]:
        intervalo = float(v.get("intervalo_m", 0))
        precio_mat = float(v.get("precio_material", 0.0) or 0.0)
        if intervalo <= 0 or precio_mat <= 0:
            continue
        n = longitud / intervalo
        partidas[v["label"] + " (material)"] = n * precio_mat * float(v.get("factor_piezas", 1.0))

    pozo_item = decisiones["pozo_registro"]["item"]
    if pozo_item is not None:
        precio_tapa_mat = float(pozo_item.get("precio_tapa_material", 0.0) or 0.0)
        intervalo_poz = float(pozo_item.get("intervalo", 0))
        if precio_tapa_mat > 0 and intervalo_poz > 0:
            partidas["Tapa pozo registro ABA (material)"] = (
                longitud / intervalo_poz) * precio_tapa_mat

    if not partidas:
        return None
    return sum(partidas.values()), partidas


def _demo_items(red: str, precios: dict) -> tuple[dict | None, dict | None]:
    """Extrae items de demolición por unidad (m2 y m) del catálogo."""
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


def _acumular(caps: dict, nombre: str, resultado: tuple[float, dict] | None) -> None:
    if resultado is None:
        return
    subtotal, partidas = resultado
    if nombre in caps:
        caps[nombre]["partidas"].update(partidas)
        caps[nombre]["subtotal"] += subtotal
    else:
        caps[nombre] = {"subtotal": subtotal, "partidas": dict(partidas)}


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_presupuesto(p: ParametrosProyecto, precios: dict) -> dict[str, Any]:
    """
    Calcula el presupuesto completo para un proyecto EMASESA.

    Args:
        p: Parámetros del proyecto introducidos por el usuario.
        precios: Dict completo cargado desde SQLite (via infraestructura.precios).

    Returns:
        Dict con:
          - capitulos: dict numerado con subtotal y partidas de cada capítulo
          - pem, gg, bi, pbl_sin_iva, iva, total: resumen financiero
          - auxiliares: datos geométricos de ABA y SAN (para debug)
    """
    espesores = precios["espesores_calzada"]
    caps: dict[str, dict] = {}
    aux_aba = aux_san = None

    # Acumuladores para ajuste de base S&S y materiales
    _excluir_de_base_ss = 0.0   # Cánones + desmontaje (no entran en base S&S)
    _materiales_total = 0.0      # Materiales ABA (excluidos de GG/BI)

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULO 01 — OBRA CIVIL ABASTECIMIENTO
    # ═══════════════════════════════════════════════════════════════════════
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

        # Obra civil base (excavación, tubería, arriñonado, relleno, entibación)
        cap_aba, partidas_aba, aux_aba = capitulo_obra_civil(
            p.aba_longitud_m, p.aba_profundidad_m, p.aba_item, precios,
            pct_manual=p.pct_manual,
            espesor_pavimento_m=p.espesor_pavimento_m,
            entibacion_item=decisiones_aba["entibacion"]["item"],
        )
        _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", (cap_aba, partidas_aba))

        # Cánones (se muestran en obra civil pero se excluyen de base S&S)
        canon_aba = capitulo_canones(
            aux_aba.get("canon_tierras", 0.0),
            aux_aba.get("canon_mixto", 0.0),
        )
        _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", canon_aba)
        if canon_aba:
            _excluir_de_base_ss += canon_aba[0]

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
        if p.desmontaje_tipo != "none":
            _desm = capitulo_desmontaje(
                p.aba_longitud_m, precios,
                desmontaje_item=decisiones_aba["desmontaje"]["item"])
            _acumular(caps, "OBRA CIVIL ABASTECIMIENTO", _desm)
            if _desm:
                _excluir_de_base_ss += _desm[0]

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

        # Materiales ABA (excluidos de GG/BI, capítulo aparte)
        _mat = _materiales_aba(p.aba_longitud_m, p.aba_item, decisiones_aba)
        if _mat:
            _materiales_total += _mat[0]
            _acumular(caps, "MATERIALES", _mat)

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULO 02 — OBRA CIVIL SANEAMIENTO
    # ═══════════════════════════════════════════════════════════════════════
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

        cap_san, partidas_san, aux_san = capitulo_obra_civil(
            p.san_longitud_m, p.san_profundidad_m, p.san_item, precios,
            es_san=True,
            pct_manual=p.pct_manual,
            espesor_pavimento_m=p.espesor_pavimento_m,
            entibacion_item=decisiones_san["entibacion"]["item"],
        )
        _acumular(caps, "OBRA CIVIL SANEAMIENTO", (cap_san, partidas_san))

        canon_san = capitulo_canones(
            aux_san.get("canon_tierras", 0.0),
            aux_san.get("canon_mixto", 0.0),
        )
        _acumular(caps, "OBRA CIVIL SANEAMIENTO", canon_san)
        if canon_san:
            _excluir_de_base_ss += canon_san[0]

        # Pozos de registro SAN
        _acumular(caps, "OBRA CIVIL SANEAMIENTO",
                  capitulo_pozos_registro(
                      p.san_longitud_m, p.san_profundidad_m, p.san_diametro_mm, precios,
                      es_san=True,
                      pozo_item=decisiones_san["pozo_registro"]["item"]))

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

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULO 03 — PAVIMENTACIÓN ABASTECIMIENTO
    # ═══════════════════════════════════════════════════════════════════════
    if p.aba_activa:
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
                                      p.pav_aba_bordillo_m, demo_m_aba))
        _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                  capitulo_pavimentacion(p.pav_aba_acerado_m2, p.pav_aba_acerado_item,
                                         p.pav_aba_bordillo_m, p.pav_aba_bordillo_item))
        if p.subbase_aba_espesor_m > 0:
            _acumular(caps, "PAVIMENTACIÓN ABASTECIMIENTO",
                      capitulo_subbase(p.pav_aba_acerado_m2,
                                       p.subbase_aba_espesor_m, p.subbase_aba_item))

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULO 04 — PAVIMENTACIÓN SANEAMIENTO
    # ═══════════════════════════════════════════════════════════════════════
    if p.san_activa:
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
                  capitulo_pavimentacion(p.pav_san_calzada_m2, p.pav_san_calzada_item,
                                         p.pav_san_acera_m2, p.pav_san_acera_item,
                                         calzada_conversion=True, espesores=espesores,
                                         factor_calzada_san=1.5))
        if p.subbase_san_espesor_m > 0:
            _acumular(caps, "PAVIMENTACIÓN SANEAMIENTO",
                      capitulo_subbase(p.pav_san_calzada_m2 + p.pav_san_acera_m2,
                                       p.subbase_san_espesor_m, p.subbase_san_item))

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULO 05 — ACOMETIDAS ABASTECIMIENTO
    # ═══════════════════════════════════════════════════════════════════════
    if p.aba_activa:
        acometidas_aba = precios["acometidas_aba_tipos"]
        tipo_aba = precios["acometida_aba_defecto"]
        if tipo_aba not in acometidas_aba:
            raise ValueError(
                f"El tipo de acometida ABA por defecto '{tipo_aba}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        factor_aba = float(precios.get("acometidas_aba_factores", {}).get(tipo_aba, 1.2))
        _acumular(caps, "ACOMETIDAS ABASTECIMIENTO",
                  capitulo_acometidas(p.acometidas_aba_n,
                                      acometidas_aba[tipo_aba],
                                      "Acometidas ABA", factor=factor_aba))

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULO 06 — ACOMETIDAS SANEAMIENTO
    # ═══════════════════════════════════════════════════════════════════════
    if p.san_activa:
        acometidas_san = precios["acometidas_san_tipos"]
        tipo_san = precios["acometida_san_defecto"]
        if tipo_san not in acometidas_san:
            raise ValueError(
                f"El tipo de acometida SAN por defecto '{tipo_san}' no existe en el catálogo. "
                "Actualízalo en Administración de precios."
            )
        _acumular(caps, "ACOMETIDAS SANEAMIENTO",
                  capitulo_acometidas(p.acometidas_san_n,
                                      acometidas_san[tipo_san],
                                      "Acometidas SAN", factor=1.0))

    # ═══════════════════════════════════════════════════════════════════════
    # CAPÍTULOS 07-08 — SEGURIDAD Y SALUD / GESTIÓN AMBIENTAL
    # ═══════════════════════════════════════════════════════════════════════
    _base_ss_keys = {
        "OBRA CIVIL ABASTECIMIENTO", "OBRA CIVIL SANEAMIENTO",
        "PAVIMENTACIÓN ABASTECIMIENTO", "PAVIMENTACIÓN SANEAMIENTO",
        "ACOMETIDAS ABASTECIMIENTO", "ACOMETIDAS SANEAMIENTO",
    }
    base_ss = max(
        0.0,
        sum(c["subtotal"] for nombre, c in caps.items() if nombre in _base_ss_keys)
        - _excluir_de_base_ss,
    )

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

    # ── Numerar capítulos en orden de inserción ──────────────────────────────
    capitulos = {
        f"{i + 1:02d} {nombre}": datos
        for i, (nombre, datos) in enumerate(caps.items())
    }

    # ── Resumen financiero ───────────────────────────────────────────────────
    pem = sum(c["subtotal"] for c in capitulos.values())
    fin = calcular_resumen(
        pem=pem,
        materiales=_materiales_total,
        pct_gg=precios["pct_gg"],
        pct_bi=precios["pct_bi"],
        pct_iva=precios["pct_iva"],
    )

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
        "auxiliares": {"aba": aux_aba or {}, "san": aux_san or {}},
    }
