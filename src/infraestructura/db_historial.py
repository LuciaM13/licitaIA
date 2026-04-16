"""CRUD del historial de presupuestos generados.

Separado de db.py para mantener el fichero principal por debajo de 500 líneas.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.infraestructura.db import conectar, _rows_to_dicts

logger = logging.getLogger(__name__)


def guardar_presupuesto(resultado: dict, parametros: dict[str, str],
                        descripcion: str = "",
                        pct_ci: float = 1.0,
                        path: str | Path | None = None) -> int:
    """Guarda un presupuesto generado en el historial.

    Args:
        resultado: dict devuelto por calcular_presupuesto() con claves
            capitulos, pem, gg, bi, pbl_sin_iva, iva, total, pcts.
        parametros: dict {clave: valor} con los inputs del usuario
            (ej: aba_longitud_m, san_tuberia, etc.). Valores como str.
        descripcion: texto libre opcional para identificar el presupuesto.
        path: ruta alternativa a la BD (para tests).

    Returns:
        id del presupuesto insertado.
    """
    with conectar(path) as conn:
        try:
            pcts = resultado.get("pcts", {})
            cursor = conn.execute(
                "INSERT INTO presupuestos "
                "(descripcion, pem, gg, bi, pbl_sin_iva, iva, total, "
                " pct_gg, pct_bi, pct_iva, pct_ci) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (descripcion,
                 float(resultado["pem"]),
                 float(resultado["gg"]),
                 float(resultado["bi"]),
                 float(resultado["pbl_sin_iva"]),
                 float(resultado["iva"]),
                 float(resultado["total"]),
                 float(pcts.get("gg", 0)),
                 float(pcts.get("bi", 0)),
                 float(pcts.get("iva", 0)),
                 float(pct_ci),
                 ))
            presupuesto_id = cursor.lastrowid

            # Capítulos y partidas
            for orden, (cap_nombre, cap_info) in enumerate(
                    resultado.get("capitulos", {}).items(), start=1):
                cur_cap = conn.execute(
                    "INSERT INTO presupuesto_capitulos "
                    "(presupuesto_id, capitulo, subtotal, orden) VALUES (?,?,?,?)",
                    (presupuesto_id, cap_nombre,
                     float(cap_info.get("subtotal", 0)), orden))
                capitulo_id = cur_cap.lastrowid
                for desc_partida, importe in cap_info.get("partidas", {}).items():
                    conn.execute(
                        "INSERT INTO presupuesto_partidas "
                        "(capitulo_id, descripcion, importe) VALUES (?,?,?)",
                        (capitulo_id, desc_partida, float(importe)))

            # Parámetros de entrada
            for clave, valor in parametros.items():
                conn.execute(
                    "INSERT INTO presupuesto_parametros "
                    "(presupuesto_id, clave, valor) VALUES (?,?,?)",
                    (presupuesto_id, clave, str(valor)))

            # Trazabilidad (decisiones del sistema experto)
            trazabilidad = resultado.get("trazabilidad", {})
            for red, explicaciones in trazabilidad.items():
                for orden, frase in enumerate(explicaciones):
                    conn.execute(
                        "INSERT INTO presupuesto_trazabilidad "
                        "(presupuesto_id, red, orden, explicacion) VALUES (?,?,?,?)",
                        (presupuesto_id, red, orden, frase))

            conn.commit()
            logger.info("guardar_presupuesto OK - id=%d total=%.2f desc='%s'",
                        presupuesto_id, resultado["total"], descripcion[:60])
            return presupuesto_id

        except Exception as e:
            logger.error("Error en guardar_presupuesto: %s", e, exc_info=True)
            conn.rollback()
            raise


def listar_presupuestos(limit: int = 50, offset: int = 0,
                        path: str | Path | None = None) -> list[dict]:
    """Devuelve lista resumida de presupuestos ordenados por fecha desc."""
    with conectar(path) as conn:
        cursor = conn.execute(
            "SELECT id, creado_en, descripcion, pem, total "
            "FROM presupuestos ORDER BY creado_en DESC LIMIT ? OFFSET ?",
            (limit, offset))
        return _rows_to_dicts(cursor)


def obtener_presupuesto(presupuesto_id: int,
                        path: str | Path | None = None) -> dict | None:
    """Carga un presupuesto completo con capítulos, partidas y parámetros."""
    with conectar(path) as conn:
        # Cabecera
        row = conn.execute(
            "SELECT * FROM presupuestos WHERE id = ?", (presupuesto_id,)
        ).fetchone()
        if row is None:
            return None
        resultado = {k: row[k] for k in row.keys()}

        # Capítulos + partidas
        capitulos = {}
        for cap_row in conn.execute(
                "SELECT id, capitulo, subtotal, orden "
                "FROM presupuesto_capitulos WHERE presupuesto_id = ? ORDER BY orden",
                (presupuesto_id,)):
            partidas = {}
            for p_row in conn.execute(
                    "SELECT descripcion, importe FROM presupuesto_partidas "
                    "WHERE capitulo_id = ? ORDER BY id",
                    (cap_row["id"],)):
                partidas[p_row["descripcion"]] = p_row["importe"]
            capitulos[cap_row["capitulo"]] = {
                "subtotal": cap_row["subtotal"],
                "partidas": partidas,
            }
        resultado["capitulos"] = capitulos

        # Parámetros
        params = {}
        for p_row in conn.execute(
                "SELECT clave, valor FROM presupuesto_parametros "
                "WHERE presupuesto_id = ? ORDER BY clave",
                (presupuesto_id,)):
            params[p_row["clave"]] = p_row["valor"]
        resultado["parametros"] = params

        # Trazabilidad (decisiones del sistema experto)
        trazabilidad: dict[str, list[str]] = {}
        for t_row in conn.execute(
                "SELECT red, explicacion FROM presupuesto_trazabilidad "
                "WHERE presupuesto_id = ? ORDER BY red, orden",
                (presupuesto_id,)):
            trazabilidad.setdefault(t_row["red"], []).append(t_row["explicacion"])
        resultado["trazabilidad"] = trazabilidad

        return resultado


def eliminar_presupuesto(presupuesto_id: int,
                         path: str | Path | None = None) -> bool:
    """Elimina un presupuesto y sus datos asociados (CASCADE). Retorna True si existía."""
    with conectar(path) as conn:
        cursor = conn.execute(
            "DELETE FROM presupuestos WHERE id = ?", (presupuesto_id,))
        conn.commit()
        eliminado = cursor.rowcount > 0
        if eliminado:
            logger.info("eliminar_presupuesto OK - id=%d", presupuesto_id)
        else:
            logger.warning("eliminar_presupuesto - id=%d no encontrado", presupuesto_id)
        return eliminado


def contar_presupuestos(path: str | Path | None = None) -> int:
    """Retorna el número total de presupuestos en el historial."""
    with conectar(path) as conn:
        return conn.execute("SELECT COUNT(*) FROM presupuestos").fetchone()[0]
