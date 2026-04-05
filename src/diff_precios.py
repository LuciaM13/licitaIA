"""Calcula las diferencias entre dos dicts de precios para la vista de confirmación."""

from __future__ import annotations


# Mapeo de claves JSON a nombres legibles en español
_NOMBRES_SECCION = {
    "pct_gg": "Gastos Generales",
    "pct_bi": "Beneficio Industrial",
    "pct_iva": "IVA",
    "factor_esponjamiento": "Factor esponjamiento",
    "pct_manual_defecto": "% Excavación manual",
    "catalogo_aba": "Tuberías ABA",
    "catalogo_san": "Tuberías SAN",
    "catalogo_valvuleria": "Valvulería ABA",
    "catalogo_entibacion": "Entibación",
    "catalogo_pozos": "Pozos de registro",
    "acerados_aba": "Acerados ABA",
    "acerados_san": "Acerados SAN",
    "bordillos_reposicion": "Bordillos",
    "calzadas_reposicion": "Calzadas",
    "espesores_calzada": "Espesores calzada",
    "excavacion": "Excavación",
    "anchos_zanja_aba": "Anchos zanja ABA",
    "anchos_zanja_san": "Anchos zanja SAN",
    "espesores_arrinonado_aba": "Espesores arriñonado ABA",
    "espesores_arrinonado_san": "Espesores arriñonado SAN",
    "demolicion_aba": "Demolición ABA",
    "demolicion_san": "Demolición SAN",
    "acometidas_aba_tipos": "Acometidas ABA",
    "acometidas_san_tipos": "Acometidas SAN",
    "acometida_aba_defecto": "Acometida ABA defecto",
    "acometida_san_defecto": "Acometida SAN defecto",
    "defaults_ui": "Valores por defecto",
}

_NOMBRES_DEFAULTS_UI = {
    "aba_longitud_m": "Longitud ABA (m)",
    "aba_profundidad_m": "Profundidad ABA (m)",
    "san_longitud_m": "Longitud SAN (m)",
    "san_profundidad_m": "Profundidad SAN (m)",
    "pav_aba_acerado_m2": "Acerado ABA (m²)",
    "pav_aba_bordillo_m": "Bordillo ABA (m)",
    "pav_san_calzada_m2": "Calzada SAN (m²)",
    "pav_san_acera_m2": "Acera SAN (m²)",
    "acometidas_n": "Nº acometidas",
    "importe_seguridad": "Seguridad y Salud (€)",
    "importe_gestion": "Gestión Ambiental (€)",
}

_NOMBRES_EXCAVACION = {
    "mec_hasta_25": "Mecánica ≤ umbral",
    "mec_mas_25": "Mecánica > umbral",
    "manual_hasta_25": "Manual ≤ umbral",
    "manual_mas_25": "Manual > umbral",
    "arrinonado": "Arriñonado",
    "relleno": "Relleno",
    "carga_mec": "Carga mecánica",
    "carga_manual": "Carga manual",
    "transporte": "Transporte",
    "canon_tierras": "Canon tierras",
    "umbral_profundidad_m": "Umbral profundidad (m)",
}

# Clave natural para comparar listas de dicts
_CLAVE_NATURAL = {
    "catalogo_aba": "label",
    "catalogo_san": "label",
    "catalogo_valvuleria": "label",
    "catalogo_entibacion": "label",
    "catalogo_pozos": "label",
    "acerados_aba": "label",
    "acerados_san": "label",
    "bordillos_reposicion": "label",
    "calzadas_reposicion": "label",
    "anchos_zanja_aba": "diametro_mm",
    "anchos_zanja_san": "diametro_mm",
    "espesores_arrinonado_aba": "diametro_mm",
    "espesores_arrinonado_san": "diametro_mm",
    "demolicion_aba": "label",
    "demolicion_san": "label",
}


def _delta_pct(old, new) -> str | None:
    """Calcula el porcentaje de cambio entre dos valores numéricos."""
    try:
        old_f, new_f = float(old), float(new)
    except (TypeError, ValueError):
        return None
    if old_f == 0:
        return None
    pct = (new_f - old_f) / abs(old_f) * 100
    return f"{pct:+.1f}%"


def _diff_escalares(seccion: str, old_val, new_val) -> list[dict]:
    """Compara dos valores escalares."""
    if old_val == new_val:
        return []
    return [{
        "seccion": _NOMBRES_SECCION.get(seccion, seccion),
        "tipo": "modificado",
        "campo": _NOMBRES_SECCION.get(seccion, seccion),
        "valor_anterior": old_val,
        "valor_nuevo": new_val,
        "delta_pct": _delta_pct(old_val, new_val) or "",
    }]


def _diff_dict_plano(seccion: str, old_d: dict, new_d: dict,
                     nombres: dict | None = None) -> list[dict]:
    """Compara dos dicts planos clave->valor."""
    cambios = []
    nombre_seccion = _NOMBRES_SECCION.get(seccion, seccion)
    all_keys = set(old_d) | set(new_d)
    for k in sorted(all_keys):
        nombre_campo = (nombres or {}).get(k, k)
        if k not in old_d:
            cambios.append({
                "seccion": nombre_seccion, "tipo": "añadido",
                "campo": nombre_campo,
                "valor_anterior": "—", "valor_nuevo": new_d[k], "delta_pct": "",
            })
        elif k not in new_d:
            cambios.append({
                "seccion": nombre_seccion, "tipo": "eliminado",
                "campo": nombre_campo,
                "valor_anterior": old_d[k], "valor_nuevo": "—", "delta_pct": "",
            })
        elif old_d[k] != new_d[k]:
            cambios.append({
                "seccion": nombre_seccion, "tipo": "modificado",
                "campo": nombre_campo,
                "valor_anterior": old_d[k], "valor_nuevo": new_d[k],
                "delta_pct": _delta_pct(old_d[k], new_d[k]) or "",
            })
    return cambios


def _diff_lista_dicts(seccion: str, old_list: list, new_list: list) -> list[dict]:
    """Compara dos listas de dicts usando la clave natural del catálogo."""
    cambios = []
    nombre_seccion = _NOMBRES_SECCION.get(seccion, seccion)
    key_field = _CLAVE_NATURAL.get(seccion, "label")

    old_by_key = {row[key_field]: row for row in old_list if key_field in row}
    new_by_key = {row[key_field]: row for row in new_list if key_field in row}

    all_keys = list(dict.fromkeys(
        [row[key_field] for row in old_list if key_field in row] +
        [row[key_field] for row in new_list if key_field in row]
    ))

    for k in all_keys:
        if k not in old_by_key:
            cambios.append({
                "seccion": nombre_seccion, "tipo": "añadido",
                "campo": "Nuevo elemento",
                "valor_anterior": "—",
                "valor_nuevo": str(k),
                "delta_pct": "",
            })
        elif k not in new_by_key:
            cambios.append({
                "seccion": nombre_seccion, "tipo": "eliminado",
                "campo": "Eliminado",
                "valor_anterior": str(k),
                "valor_nuevo": "—",
                "delta_pct": "",
            })
        elif old_by_key[k] != new_by_key[k]:
            # Encontrar qué campos cambiaron
            old_row, new_row = old_by_key[k], new_by_key[k]
            for field in sorted(set(old_row) | set(new_row)):
                if field == key_field:
                    continue
                ov = old_row.get(field)
                nv = new_row.get(field)
                if ov != nv:
                    cambios.append({
                        "seccion": nombre_seccion, "tipo": "modificado",
                        "campo": f"{k} → {field}",
                        "valor_anterior": ov,
                        "valor_nuevo": nv,
                        "delta_pct": _delta_pct(ov, nv) or "",
                    })
    return cambios


def calcular_diff(original: dict, nuevo: dict) -> list[dict]:
    """Retorna lista de cambios entre el estado original y el nuevo.

    Cada cambio es un dict con: seccion, tipo, campo, valor_anterior,
    valor_nuevo, delta_pct.
    """
    cambios: list[dict] = []

    for clave in sorted(set(original) | set(nuevo)):
        old_val = original.get(clave)
        new_val = nuevo.get(clave)

        if old_val == new_val:
            continue

        nombre = _NOMBRES_SECCION.get(clave, clave)

        # Clave añadida o eliminada de nivel superior
        if old_val is None:
            cambios.append({
                "seccion": nombre, "tipo": "añadido",
                "campo": nombre,
                "valor_anterior": "—",
                "valor_nuevo": f"({type(new_val).__name__})",
                "delta_pct": "",
            })
            continue
        if new_val is None:
            cambios.append({
                "seccion": nombre, "tipo": "eliminado",
                "campo": nombre,
                "valor_anterior": f"({type(old_val).__name__})",
                "valor_nuevo": "—",
                "delta_pct": "",
            })
            continue

        # Escalares (strings, números)
        if not isinstance(old_val, (dict, list)) and not isinstance(new_val, (dict, list)):
            cambios.extend(_diff_escalares(clave, old_val, new_val))

        # Dicts planos
        elif isinstance(old_val, dict) and isinstance(new_val, dict):
            if clave == "defaults_ui":
                nombres = _NOMBRES_DEFAULTS_UI
            elif clave == "excavacion":
                nombres = _NOMBRES_EXCAVACION
            else:
                nombres = None
            cambios.extend(_diff_dict_plano(clave, old_val, new_val, nombres))

        # Listas de dicts (catálogos)
        elif isinstance(old_val, list) and isinstance(new_val, list):
            cambios.extend(_diff_lista_dicts(clave, old_val, new_val))

        # Type mismatch (ej: dict→None, list→str)
        else:
            cambios.append({
                "seccion": nombre, "tipo": "modificado",
                "campo": f"{nombre} (tipo cambió)",
                "valor_anterior": str(old_val)[:80],
                "valor_nuevo": str(new_val)[:80],
                "delta_pct": "",
            })

    return cambios
