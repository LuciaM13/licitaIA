"""Cargador de YAMLs de parametros por proyecto -> ParametrosProyecto + MetaProyecto.

El YAML expone strings legibles (tipo: FD, dn: 150, label: "Aglomerado e=10 cm")
y este cargador hace lookup contra el dict precios_ci POST aplicar_ci(). Si un
lookup falla se lanza ValidationConfigError con mensaje accionable.
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

from src.modelo.parametros import ParametrosProyecto
from src.validacion_proyectos.tipos import MetaProyecto

logger = logging.getLogger(__name__)


_ALIAS_TIPO_TUBERIA = {
    "PE100": "PE-100",
    "PE 100": "PE-100",
    "PEAD": "PE-100",  # caveat: PEAD insertado = Relining; el cargador no lo distingue, hacerlo en el YAML via partidas_fuera_alcance
    "GRES": "Gres",
    "FD": "FD",
    "HORMIGON": "Hormigón",
    "HORMIGÓN": "Hormigón",
    "HACCH": "HACCH",
    "HA+PE80": "HA+PE80",
    "PVC": "PVC",
}


# Overrides Excel literal -> label canónico catálogo. Derivado de
# .planning/research/validacion/mapeo_labels.md (revisión humana).
_OVERRIDES_LABELS = {
    # Acerados (acerados_aba/_san)
    "Solado con baldosas de terrazo de 40x40 cm": "Baldosa terrazo 40x40",
    "Solado con baldosa hidráulica de 40x40x4": "Baldosa hidráulica 40x40x4",
    "Solado baldosa hidráulica tipo cigarrillo": "Baldosa cigarrillo",
    "Solado paso peatones hormigón granallada boton/direccional 40x60x4,9": "Baldosa granallada",
    # Calzadas (calzadas_reposicion)
    "Pavimento adoquín hormigón prefabricado 10x20x8": "Adoquín",
    "Pavimento adoquin hormigon prefabricado 10x20x8": "Adoquín",
    "Reposición Pavimento Calzada": "Aglomerado",
    "Demolición pavimento aglomerado y hormigón": "Aglomerado",
    "Demolición pavimento mezcla asfáltica": "Aglomerado",
    "Base hormigón en masa en firme de calzada": "Capa base pavimento",
    # Variantes sin acentos / formato del transcriptor
    "Baldosa hidraulica tipo cigarrillo 30x30": "Baldosa cigarrillo",
    "Baldosa hidraulica tipo cigarrillo": "Baldosa cigarrillo",
    "Baldosa hidraulica 40x40x4": "Baldosa hidráulica 40x40x4",
    "Baldosa hidraulica 40x40": "Baldosa hidráulica 40x40x4",
    "Hormigon bituminoso AC 16 surf S": "Aglomerado",
    "Hormigón bituminoso AC 16 surf S": "Aglomerado",
    "Adoquin": "Adoquín",
    # Bordillos (bordillos_reposicion)
    "Bordillo pref. hormigón bicapa 17x28x100": "Bordillo bicapa 17x28",
    "Bordillo pref. hormigón bicapa 10x20x100": "Bordillo bicapa 10x20",
    # Subbases (catalogo_subbases)
    "Base albero compactado": "Base albero compactado",
    "Base hormigón en masa en firmes de acerado": "Base hormigón acerado",
    "Base de zahorra": "Base albero compactado",
}


class ValidationConfigError(ValueError):
    """Error de configuracion al hidratar ParametrosProyecto desde YAML."""


def _resolver_por_label(label: str, lista_items: list[dict]) -> dict | None:
    if not label or not lista_items:
        return None
    label_norm = _OVERRIDES_LABELS.get(label, label)
    item = next((it for it in lista_items if it.get("label") == label_norm), None)
    if item is not None:
        return item
    mejor: dict | None = None
    mejor_score = 0.0
    for it in lista_items:
        cand = str(it.get("label", ""))
        if not cand:
            continue
        score = SequenceMatcher(None, label_norm, cand).ratio()
        if score > mejor_score:
            mejor_score = score
            mejor = it
    if mejor is not None and mejor_score >= 0.65:
        logger.warning(
            "[fuzzy] '%s' -> '%s' (score=%.2f)",
            label, mejor.get("label"), mejor_score,
        )
        return mejor
    return None


def _resolver_tuberia(
    tipo: str,
    dn: int,
    precios_ci: dict[str, Any],
    red: str,
) -> dict | None:
    """Busca un item de tuberia ABA o SAN por (tipo, diametro_mm)."""
    catalogo_key = "catalogo_aba" if red == "ABA" else "catalogo_san"
    catalogo = precios_ci.get(catalogo_key, [])
    tipo_norm = _ALIAS_TIPO_TUBERIA.get(tipo, tipo)
    item = next(
        (it for it in catalogo
         if it.get("tipo") == tipo_norm and int(it.get("diametro_mm", -1)) == int(dn)),
        None,
    )
    if item is not None:
        return item
    for variant in (tipo_norm.title(), tipo_norm.capitalize(), tipo_norm.upper(), tipo_norm.lower()):
        item = next(
            (it for it in catalogo
             if it.get("tipo") == variant and int(it.get("diametro_mm", -1)) == int(dn)),
            None,
        )
        if item is not None:
            return item
    return None


def _aba_to_params(bloque: dict[str, Any], precios_ci: dict[str, Any], expediente: str) -> dict:
    tipo = bloque.get("tipo")
    dn = bloque.get("dn")
    if tipo is None or dn is None:
        raise ValidationConfigError(
            f"[{expediente}] aba: faltan claves obligatorias 'tipo' y/o 'dn'"
        )
    item = _resolver_tuberia(str(tipo), int(dn), precios_ci, red="ABA")
    if item is None:
        raise ValidationConfigError(
            f"[{expediente}] aba: no se encuentra tuberia ABA tipo={tipo!r} dn={dn} "
            "en precios_ci['catalogo_aba']. Revisa el YAML o el catalogo."
        )
    return {
        "aba_item": item,
        "aba_longitud_m": float(bloque.get("longitud_m", 0.0)),
        "aba_profundidad_m": float(bloque.get("profundidad_m", 1.20)),
    }


def _san_to_params(bloque: dict[str, Any], precios_ci: dict[str, Any], expediente: str) -> dict:
    tipo = bloque.get("tipo")
    dn = bloque.get("dn")
    if tipo is None or dn is None:
        raise ValidationConfigError(
            f"[{expediente}] san: faltan claves obligatorias 'tipo' y/o 'dn'"
        )
    item = _resolver_tuberia(str(tipo), int(dn), precios_ci, red="SAN")
    if item is None:
        raise ValidationConfigError(
            f"[{expediente}] san: no se encuentra tuberia SAN tipo={tipo!r} dn={dn} "
            "en precios_ci['catalogo_san']."
        )
    return {
        "san_item": item,
        "san_longitud_m": float(bloque.get("longitud_m", 0.0)),
        "san_profundidad_m": float(bloque.get("profundidad_m", 1.60)),
    }


def _pav_aba_to_params(bloque: dict[str, Any], precios_ci: dict[str, Any], expediente: str) -> dict:
    out: dict[str, Any] = {
        "pav_aba_acerado_m2": float(bloque.get("acerado_m2", 0.0)),
        "pav_aba_bordillo_m": float(bloque.get("bordillo_m", 0.0)),
        "pav_aba_calzada_m2": float(bloque.get("calzada_m2", 0.0)),
    }
    label_acerado = bloque.get("acerado_label")
    if label_acerado:
        item = _resolver_por_label(label_acerado, precios_ci.get("acerados_aba", []))
        if item is None:
            raise ValidationConfigError(
                f"[{expediente}] pav_aba.acerado_label={label_acerado!r} no esta en acerados_aba."
            )
        out["pav_aba_acerado_item"] = item
    label_bordillo = bloque.get("bordillo_label")
    if label_bordillo:
        item = _resolver_por_label(label_bordillo, precios_ci.get("bordillos_reposicion", []))
        if item is None:
            raise ValidationConfigError(
                f"[{expediente}] pav_aba.bordillo_label={label_bordillo!r} no esta en bordillos_reposicion."
            )
        out["pav_aba_bordillo_item"] = item
    label_calzada = bloque.get("calzada_label")
    if label_calzada:
        item = _resolver_por_label(label_calzada, precios_ci.get("calzadas_reposicion", []))
        if item is None:
            raise ValidationConfigError(
                f"[{expediente}] pav_aba.calzada_label={label_calzada!r} no esta en calzadas_reposicion."
            )
        out["pav_aba_calzada_item"] = item
    return out


def _pav_san_to_params(bloque: dict[str, Any], precios_ci: dict[str, Any], expediente: str) -> dict:
    out: dict[str, Any] = {
        "pav_san_calzada_m2": float(bloque.get("calzada_m2", 0.0)),
        "pav_san_acera_m2": float(bloque.get("acera_m2", 0.0)),
    }
    label_calzada = bloque.get("calzada_label")
    if label_calzada:
        item = _resolver_por_label(label_calzada, precios_ci.get("calzadas_reposicion", []))
        if item is None:
            raise ValidationConfigError(
                f"[{expediente}] pav_san.calzada_label={label_calzada!r} no esta en calzadas_reposicion."
            )
        out["pav_san_calzada_item"] = item
    label_acera = bloque.get("acera_label")
    if label_acera:
        item = _resolver_por_label(label_acera, precios_ci.get("acerados_san", []))
        if item is None:
            raise ValidationConfigError(
                f"[{expediente}] pav_san.acera_label={label_acera!r} no esta en acerados_san."
            )
        out["pav_san_acera_item"] = item
    return out


def _subbase_to_params(
    bloque_aba: dict | None,
    bloque_san: dict | None,
    precios_ci: dict[str, Any],
    expediente: str,
) -> dict:
    out: dict[str, Any] = {}
    catalogo_sub = precios_ci.get("catalogo_subbases", [])
    if bloque_aba:
        label = bloque_aba.get("label")
        if label:
            item = _resolver_por_label(label, catalogo_sub)
            if item is None:
                raise ValidationConfigError(
                    f"[{expediente}] subbase_aba.label={label!r} no esta en catalogo_subbases."
                )
            out["subbase_aba_item"] = item
        out["subbase_aba_espesor_m"] = float(bloque_aba.get("espesor_m", 0.0))
    if bloque_san:
        label = bloque_san.get("label")
        if label:
            item = _resolver_por_label(label, catalogo_sub)
            if item is None:
                raise ValidationConfigError(
                    f"[{expediente}] subbase_san.label={label!r} no esta en catalogo_subbases."
                )
            out["subbase_san_item"] = item
        out["subbase_san_espesor_m"] = float(bloque_san.get("espesor_m", 0.0))
    return out


def cargar_parametros(
    yaml_path: Path | str,
    precios_ci: dict[str, Any],
) -> tuple[ParametrosProyecto, MetaProyecto]:
    yaml_path = Path(yaml_path)
    logger.info("cargar_parametros INICIO yaml=%s", yaml_path)
    with yaml_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    expediente = str(cfg.get("expediente", yaml_path.stem))
    nombre = str(cfg.get("nombre", expediente))
    parametros_cfg = cfg.get("parametros", {}) or {}

    kwargs: dict[str, Any] = {}

    aba_block = parametros_cfg.get("aba")
    if aba_block:
        kwargs.update(_aba_to_params(aba_block, precios_ci, expediente))

    san_block = parametros_cfg.get("san")
    if san_block:
        kwargs.update(_san_to_params(san_block, precios_ci, expediente))

    pav_aba = parametros_cfg.get("pavimentacion_aba")
    if pav_aba:
        kwargs.update(_pav_aba_to_params(pav_aba, precios_ci, expediente))

    pav_san = parametros_cfg.get("pavimentacion_san")
    if pav_san:
        kwargs.update(_pav_san_to_params(pav_san, precios_ci, expediente))

    sub_aba = parametros_cfg.get("subbase_aba")
    sub_san = parametros_cfg.get("subbase_san")
    if sub_aba or sub_san:
        kwargs.update(_subbase_to_params(sub_aba, sub_san, precios_ci, expediente))

    materiales = parametros_cfg.get("materiales_demo", {}) or {}
    if "bordillo_aba" in materiales:
        kwargs["material_demo_bordillo_aba"] = str(materiales["bordillo_aba"])
    if "acerado_aba" in materiales:
        kwargs["material_demo_acerado_aba"] = str(materiales["acerado_aba"])
    if "calzada_aba" in materiales:
        kwargs["material_demo_calzada_aba"] = str(materiales["calzada_aba"])
    if "acerado_san" in materiales:
        kwargs["material_demo_acerado_san"] = str(materiales["acerado_san"])
    if "calzada_san" in materiales:
        kwargs["material_demo_calzada_san"] = str(materiales["calzada_san"])

    acometidas = parametros_cfg.get("acometidas", {}) or {}
    kwargs["acometidas_aba_n"] = int(acometidas.get("aba_n", 0))
    kwargs["acometidas_san_n"] = int(acometidas.get("san_n", 0))

    obra = parametros_cfg.get("obra", {}) or {}
    if "pct_manual" in obra:
        kwargs["pct_manual"] = float(obra["pct_manual"])
    if "instalacion_valvuleria" in obra:
        kwargs["instalacion_valvuleria"] = str(obra["instalacion_valvuleria"])
    if "conduccion_provisional_m" in obra:
        kwargs["conduccion_provisional_m"] = float(obra["conduccion_provisional_m"])
    if "espesor_pavimento_m" in obra:
        kwargs["espesor_pavimento_m"] = float(obra["espesor_pavimento_m"])
    if "desmontaje_tipo" in obra:
        kwargs["desmontaje_tipo"] = str(obra["desmontaje_tipo"])
    if "pozos_existentes_aba" in obra:
        kwargs["pozos_existentes_aba"] = str(obra["pozos_existentes_aba"])
    if "pozos_existentes_san" in obra:
        kwargs["pozos_existentes_san"] = str(obra["pozos_existentes_san"])

    imbornales = parametros_cfg.get("imbornales", {}) or {}
    if "tipo" in imbornales:
        kwargs["imbornales_tipo"] = str(imbornales["tipo"])
    if "nuevo_label" in imbornales:
        kwargs["imbornales_nuevo_label"] = str(imbornales["nuevo_label"])

    porcentajes = parametros_cfg.get("porcentajes", {}) or {}
    if "pct_seguridad" in porcentajes:
        kwargs["pct_seguridad"] = float(porcentajes["pct_seguridad"])
    if "pct_gestion" in porcentajes:
        kwargs["pct_gestion"] = float(porcentajes["pct_gestion"])
    if "pct_servicios_afectados" in porcentajes:
        kwargs["pct_servicios_afectados"] = float(porcentajes["pct_servicios_afectados"])

    p = ParametrosProyecto(**kwargs)

    fuera = tuple(str(c) for c in cfg.get("capitulos_fuera_alcance", ()))
    notas = tuple(str(n) for n in cfg.get("notas", ()))
    tipo_obra = str(cfg.get("tipo_obra", "instalacion_nueva"))
    # Acepta lista de strings o lista de dicts {codigo, desc, importe, ...}
    _pfa_raw = cfg.get("partidas_fuera_alcance", ()) or ()
    partidas_fuera_alcance = tuple(
        (p["codigo"] if isinstance(p, dict) else str(p)) for p in _pfa_raw
    )
    meta = MetaProyecto(
        expediente=expediente,
        nombre=nombre,
        capitulos_fuera_alcance=fuera,
        notas=notas,
        tipo_obra=tipo_obra,
        partidas_fuera_alcance=partidas_fuera_alcance,
    )
    logger.info("cargar_parametros FIN expediente=%s aba_activa=%s san_activa=%s",
                expediente, p.aba_activa, p.san_activa)
    return p, meta
