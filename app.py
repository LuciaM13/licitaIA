from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st
from num2words import num2words

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "catalogo_precios_limpio.csv"

GG_PCT = 0.13
BI_PCT = 0.06
IVA_PCT = 0.21

CHAPTER_DEFAULTS = {
    "01": ("OBRA CIVIL ABASTECIMIENTO", 54633.99),
    "02": ("OBRA CIVIL SANEAMIENTO", 63039.17),
    "03": ("PAVIMENTACIÓN ABASTECIMIENTO", 29472.47),
    "04": ("PAVIMENTACIÓN SANEAMIENTO", 34492.96),
    "05": ("ACOMETIDAS ABASTECIMIENTO", 17748.32),
    "06": ("ACOMETIDAS SANEAMIENTO", 22981.01),
    "07": ("SEGURIDAD Y SALUD", 8400.00),
    "08": ("GESTION AMBIENTAL", 12225.00),
}

CATALOG_CHAPTER_MAP = {
    "DEMOLICIONES Y PAVIMENTACIÓN": "03",
    "MOV. TIERRAS": "02",
    "OBRA CIVIL": "02",
    "OTROS": "08",
    "MATERIALES": "02",
}


def euro(value: float) -> str:
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def money_to_words_es(value: float) -> str:
    entero = int(math.floor(value))
    centimos = int(round((value - entero) * 100))
    texto = num2words(entero, lang="es")
    if centimos:
        texto_cent = num2words(centimos, lang="es")
        return f"{texto} euros con {texto_cent} céntimos"
    return f"{texto} euros"


@st.cache_data
def load_catalog() -> pd.DataFrame:
    df = pd.read_csv(CATALOG_PATH)
    df["display_name"] = (
        df["section"].fillna("")
        + " · "
        + df["subsection"].fillna("")
        + " · "
        + df["name"].fillna("")
        + " ("
        + df["unit"].fillna("")
        + ")"
    )
    return df


def compute_summary(chapters: Dict[str, float]) -> Dict[str, float]:
    pem = round(sum(chapters.values()), 2)
    gg = round(pem * GG_PCT, 2)
    bi = round(pem * BI_PCT, 2)
    pel = round(pem + gg + bi, 2)
    iva = round(pel * IVA_PCT, 2)
    total = round(pel + iva, 2)
    return {
        "pem": pem,
        "gg": gg,
        "bi": bi,
        "pel": pel,
        "iva": iva,
        "total": total,
    }


st.set_page_config(page_title="Calculadora de Presupuesto", layout="wide")
st.title("Calculadora de presupuesto de obra")
st.caption(
    "Proyecto en Streamlit basado únicamente en los datos proporcionados en el CSV y en el resumen del pliego."
)

mode = st.sidebar.radio(
    "Modo de trabajo",
    [
        "Resumen por capítulos",
        "Detalle desde catálogo CSV",
    ],
)

catalog = load_catalog()

if mode == "Resumen por capítulos":
    st.subheader("1) Introduce o confirma los importes por capítulo")
    st.write(
        "Este modo reproduce el formato del presupuesto final. Los capítulos 07 y 08 también se pueden activar con casillas tipo S/N."
    )

    chapters: Dict[str, float] = {}
    col1, col2 = st.columns(2)
    columns = [col1, col2]

    for idx, (chapter_id, (chapter_name, default_value)) in enumerate(CHAPTER_DEFAULTS.items()):
        with columns[idx % 2]:
            if chapter_id in {"07", "08"}:
                enabled = st.checkbox(
                    f"Activar capítulo {chapter_id} - {chapter_name}",
                    value=True,
                    key=f"enabled_{chapter_id}",
                )
                value = st.number_input(
                    f"Capítulo {chapter_id} · {chapter_name}",
                    min_value=0.0,
                    value=float(default_value),
                    step=100.0,
                    key=f"chapter_{chapter_id}",
                    disabled=not enabled,
                )
                chapters[chapter_id] = float(value) if enabled else 0.0
            else:
                value = st.number_input(
                    f"Capítulo {chapter_id} · {chapter_name}",
                    min_value=0.0,
                    value=float(default_value),
                    step=100.0,
                    key=f"chapter_{chapter_id}",
                )
                chapters[chapter_id] = float(value)

    summary = compute_summary(chapters)

    st.subheader("2) Resultado")
    for chapter_id, (chapter_name, _) in CHAPTER_DEFAULTS.items():
        st.markdown(f"**Capítulo: {chapter_id}**")
        st.markdown(chapter_name)
        st.markdown(euro(chapters[chapter_id]))
        st.write("")

    st.markdown("---")
    st.markdown(f"**Presupuesto de Ejecución Material**  
{euro(summary['pem'])}")
    st.markdown(f"**13 % Gastos Generales**  
{euro(summary['gg'])}")
    st.markdown(f"**6 % Beneficio Industrial**  
{euro(summary['bi'])}")
    st.markdown(f"**Presupuesto Base de Licitación excluido IVA**  
{euro(summary['pel'])}")
    st.markdown(f"**21 % IVA**  
{euro(summary['iva'])}")
    st.markdown(f"**Presupuesto Base de Licitación incluido IVA**  
{euro(summary['total'])}")

    texto = money_to_words_es(summary["total"]).upper()
    st.info(
        f"ASCIENDE EL PRESUPUESTO BASE DE LICITACIÓN A LA EXPRESADA CANTIDAD DE {texto} ({euro(summary['total'])})."
    )

else:
    st.subheader("1) Selección de partidas desde el catálogo del CSV")
    st.write(
        "En este modo eliges partidas del catálogo y asignas cantidades. El programa agrupa automáticamente las partidas por capítulo estimado."
    )

    selected_ids = st.multiselect(
        "Selecciona partidas",
        options=list(catalog.index),
        format_func=lambda idx: catalog.loc[idx, "display_name"],
    )

    chapter_totals = {k: 0.0 for k in CHAPTER_DEFAULTS.keys()}
    detail_rows: List[dict] = []

    if selected_ids:
        for idx in selected_ids:
            row = catalog.loc[idx]
            st.markdown("---")
            st.markdown(f"**{row['display_name']}**")
            if isinstance(row["comments"], str) and row["comments"].strip():
                st.caption(row["comments"])

            is_sn = st.checkbox(
                f"¿Aplicar esta partida? (S/N)",
                value=True,
                key=f"apply_{idx}",
            )
            qty = 0.0
            if is_sn:
                qty = st.number_input(
                    f"Cantidad [{row['unit']}]",
                    min_value=0.0,
                    value=1.0 if row["unit"] in {"ud", "%"} else 0.0,
                    step=1.0 if row["unit"] in {"ud", "%"} else 0.5,
                    key=f"qty_{idx}",
                )

            amount = round(float(qty) * float(row["price"]), 2)
            chapter_id = CATALOG_CHAPTER_MAP.get(str(row["section"]), "02")
            chapter_totals[chapter_id] += amount
            detail_rows.append(
                {
                    "Capítulo": chapter_id,
                    "Sección": row["section"],
                    "Subsección": row["subsection"],
                    "Partida": row["name"],
                    "Unidad": row["unit"],
                    "Precio unitario": row["price"],
                    "Cantidad": qty,
                    "Importe": amount,
                }
            )

    extra_chapters = st.expander("Añadir importes manuales por capítulos no cubiertos por el CSV")
    with extra_chapters:
        st.write(
            "El CSV no expone todas las partidas del abastecimiento. Aquí puedes completar capítulos faltantes sin salir del programa."
        )
        for chapter_id, (chapter_name, _) in CHAPTER_DEFAULTS.items():
            supplement = st.number_input(
                f"Ajuste manual capítulo {chapter_id} · {chapter_name}",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key=f"supp_{chapter_id}",
            )
            chapter_totals[chapter_id] += float(supplement)

    summary = compute_summary(chapter_totals)

    st.subheader("2) Desglose")
    if detail_rows:
        detail_df = pd.DataFrame(detail_rows)
        st.dataframe(detail_df, use_container_width=True)
    else:
        st.warning("Todavía no has seleccionado ninguna partida.")

    st.subheader("3) Resumen final")
    for chapter_id, (chapter_name, _) in CHAPTER_DEFAULTS.items():
        st.markdown(f"**Capítulo: {chapter_id}**")
        st.markdown(chapter_name)
        st.markdown(euro(chapter_totals[chapter_id]))
        st.write("")

    st.markdown("---")
    st.markdown(f"**Presupuesto de Ejecución Material**  
{euro(summary['pem'])}")
    st.markdown(f"**13 % Gastos Generales**  
{euro(summary['gg'])}")
    st.markdown(f"**6 % Beneficio Industrial**  
{euro(summary['bi'])}")
    st.markdown(f"**Presupuesto Base de Licitación excluido IVA**  
{euro(summary['pel'])}")
    st.markdown(f"**21 % IVA**  
{euro(summary['iva'])}")
    st.markdown(f"**Presupuesto Base de Licitación incluido IVA**  
{euro(summary['total'])}")

    texto = money_to_words_es(summary["total"]).upper()
    st.info(
        f"ASCIENDE EL PRESUPUESTO BASE DE LICITACIÓN A LA EXPRESADA CANTIDAD DE {texto} ({euro(summary['total'])})."
    )
