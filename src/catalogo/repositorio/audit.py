"""Audit log: helpers privados de diff y la API pública ``escribir_audit_evento``.

Pensado para ser invocado dentro de una transacción ya abierta: las
funciones reciben la ``conn`` y NO hacen commit. El caller
(``guardar_todo`` / ``insertar_fila_catalogo``) hace el commit final.
"""

from __future__ import annotations

import json


def _clave_audit(categoria: str, item) -> str:
    """Deriva una clave estable para identificar un ítem dentro de su categoría."""
    if isinstance(item, dict):
        # Listas de dicts: usar campos identificativos habituales
        for campo in ("label", "tipo", "clave"):
            if campo in item:
                return str(item[campo])
        return json.dumps(item, sort_keys=True, ensure_ascii=False)[:120]
    return str(item)


def _diff_categoria(categoria: str, antes, despues):
    """Devuelve lista de (clave, operacion, antes_json, despues_json).

    Compara dos colecciones (lista de dicts o dict plano) y emite un evento
    INSERT/UPDATE/DELETE por cada cambio lógico detectado.
    """
    eventos = []
    # Dict plano (excavacion, acometidas_*_tipos, espesores_calzada, defaults_ui)
    if isinstance(antes, dict) and not (antes and isinstance(next(iter(antes.values()), None), list)):
        claves = set(antes) | set(despues)
        for k in sorted(claves):
            a = antes.get(k)
            d = despues.get(k)
            if a == d:
                continue
            if k not in antes:
                eventos.append((categoria, str(k), "INSERT", None, json.dumps(d, ensure_ascii=False)))
            elif k not in despues:
                eventos.append((categoria, str(k), "DELETE", json.dumps(a, ensure_ascii=False), None))
            else:
                eventos.append((categoria, str(k), "UPDATE",
                                json.dumps(a, ensure_ascii=False),
                                json.dumps(d, ensure_ascii=False)))
        return eventos
    # Lista de dicts
    if isinstance(antes, list) and isinstance(despues, list):
        por_clave_antes = {_clave_audit(categoria, it): it for it in antes}
        por_clave_despues = {_clave_audit(categoria, it): it for it in despues}
        claves = set(por_clave_antes) | set(por_clave_despues)
        for k in sorted(claves):
            a = por_clave_antes.get(k)
            d = por_clave_despues.get(k)
            if a == d:
                continue
            if a is None:
                eventos.append((categoria, k, "INSERT", None, json.dumps(d, ensure_ascii=False)))
            elif d is None:
                eventos.append((categoria, k, "DELETE", json.dumps(a, ensure_ascii=False), None))
            else:
                eventos.append((categoria, k, "UPDATE",
                                json.dumps(a, ensure_ascii=False),
                                json.dumps(d, ensure_ascii=False)))
    return eventos


def _categorias_a_auditar():
    """Listas/dicts del dict `precios` que se auditan en audit_log."""
    return [
        "catalogo_aba", "catalogo_san", "catalogo_valvuleria",
        "catalogo_entibacion", "catalogo_pozos",
        "demolicion_aba", "demolicion_san",
        "acerados_aba", "acerados_san",
        "bordillos_reposicion", "calzadas_reposicion", "espesores_calzada",
        "excavacion", "acometidas_aba_tipos", "acometidas_san_tipos",
        "catalogo_subbases", "catalogo_desmontaje",
        "catalogo_imbornales", "catalogo_pozos_existentes",
    ]


def _escribir_audit_log(conn, eventos, actor):
    for categoria, clave, operacion, antes_json, despues_json in eventos:
        conn.execute(
            "INSERT INTO audit_log (categoria, clave, operacion, antes_json, despues_json, actor) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (categoria, clave, operacion, antes_json, despues_json, actor),
        )


def escribir_audit_evento(
    conn,
    categoria: str,
    clave: str,
    operacion: str,
    antes_json: str | None,
    despues_json: str | None,
    actor: str,
) -> None:
    """Escribe UNA fila en ``audit_log`` (wrapper público de 1 evento).

    Args:
        conn: conexión sqlite abierta (no se cierra aquí; el caller hace commit).
        categoria: nombre lógico del catálogo (e.g. ``"acerados"``).
        clave: identificador del item dentro de la categoría (label/tipo/...).
        operacion: ``"INSERT"``, ``"UPDATE"`` o ``"DELETE"``.
        antes_json: snapshot serializado pre-cambio (NULL en INSERT).
        despues_json: snapshot serializado post-cambio (NULL en DELETE).
        actor: identificador del actor para trazabilidad (e.g. ``"usuario_inline"``).

    Reutiliza el helper privado ``_escribir_audit_log`` con una lista de un
    solo evento; existe para que la capa de aplicación tenga una API pública
    de 1 fila sin invocar el helper privado del módulo.
    """
    _escribir_audit_log(
        conn,
        [(categoria, clave, operacion, antes_json, despues_json)],
        actor,
    )
