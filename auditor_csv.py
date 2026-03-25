from __future__ import annotations

"""
auditor_csv.py
--------------
Herramientas para revisar el CSV de precios y comprobar hasta qué punto el modelo
actual de LicitaIA lo está cubriendo.

Qué comprueba:
- cuántas líneas de precio trae el CSV
- qué grupos o familias aparecen
- si esas familias están modeladas de forma directa, parcial o todavía no

Qué NO hace:
- no reconstruye una medición real completa
- no sustituye una base de precios descompuesta
"""

from pathlib import Path
from typing import Dict, List

import pandas as pd

from datos import CSV_GROUP_STATUS


def _precio_a_float(valor: object) -> float | None:
    """Convierte precios tipo '14,70' a float.

    Devuelve None si el valor no puede interpretarse como número.
    """
    if pd.isna(valor):
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def cargar_csv_precios(ruta_csv: str | Path) -> pd.DataFrame:
    """Lee el CSV de precios con la codificación esperable para este archivo."""
    df = pd.read_csv(ruta_csv, sep=";", encoding="cp1252")
    df = df.iloc[:, :6].copy()
    df.columns = ["Concepto", "Subconcepto", "Unidad", "Precio", "Codigo", "Comentarios"]
    df["Precio_num"] = df["Precio"].apply(_precio_a_float)
    return df


def resumir_csv(ruta_csv: str | Path) -> Dict[str, object]:
    """Resume el contenido del CSV y lo clasifica por grupos."""
    df = cargar_csv_precios(ruta_csv)

    # El CSV mezcla cabeceras de grupo y líneas con precio.
    # Vamos guardando el último grupo visto para asociarlo a las líneas posteriores.
    grupo_actual = None
    grupos: List[str | None] = []

    for _, fila in df.iterrows():
        if pd.notna(fila["Concepto"]) and pd.isna(fila["Precio_num"]):
            grupo_actual = str(fila["Concepto"]).strip()
        grupos.append(grupo_actual)

    df["Grupo"] = grupos
    precios = df[df["Precio_num"].notna()].copy()

    resumen = (
        precios.groupby("Grupo", dropna=False)
        .agg(lineas=("Precio_num", "size"), precio_min=("Precio_num", "min"), precio_max=("Precio_num", "max"))
        .reset_index()
        .sort_values("Grupo", na_position="last")
    )

    detalle_cobertura = []
    directos = parciales = no_cubiertos = 0

    for _, fila in resumen.iterrows():
        grupo = fila["Grupo"] if pd.notna(fila["Grupo"]) else "Sin grupo"
        estado, nota = CSV_GROUP_STATUS.get(grupo, ("no", "Grupo no contemplado todavía en el modelo simplificado."))

        if estado == "directo":
            directos += 1
        elif estado == "parcial":
            parciales += 1
        else:
            no_cubiertos += 1

        detalle_cobertura.append(
            {
                "Grupo": grupo,
                "Líneas con precio": int(fila["lineas"]),
                "Precio mínimo": float(fila["precio_min"]),
                "Precio máximo": float(fila["precio_max"]),
                "Cobertura": estado,
                "Comentario": nota,
            }
        )

    return {
        "lineas_con_precio": int(len(precios)),
        "grupos_detectados": int(resumen["Grupo"].notna().sum()),
        "grupos_directos": directos,
        "grupos_parciales": parciales,
        "grupos_no_cubiertos": no_cubiertos,
        "detalle": detalle_cobertura,
    }
