
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st
from num2words import num2words

BASE_DIR = Path(__file__).resolve().parent

POSSIBLE_CATALOG_FILES = [
    "datos.csv",
    "catalogo_precios_limpio.csv",
    "240415_VALORACIÓN ACTUACIONES(S-BASE PRECIOS ABRIL-'24)).csv",
]

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
    "08": ("GESTIÓN AMBIENTAL", 12225.00),
}

CATALOG_CHAPTER_MAP = {
    "DEMOLICIONES Y PAVIMENTACIÓN": "03",
    "MOV. TIERRAS": "02",
    "OBRA CIVIL": "02",
    "OTROS": "08",
    "MATERIALES": "02",
}


def find_catalog_path() -> Path:
    for filename in POSSIBLE_CATALOG_FILES:
        path = BASE_DIR / filename
        if path.exists():
            return path
    raise FileNotFoundError(
        "No se ha encontrado el CSV de datos. Sube al repo uno de estos archivos: "
        + ", ".join(POSSIBLE_CATALOG_FILES)
    )


def euro(value: float) -> str:
    s = f"{float(value):,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def money_to_words_es(value: float) -> str:
    value = round(float(value), 2)
    entero = int(math.floor(value))
    centimos = int(round((value - entero) * 100))

    if centimos == 100:
        entero += 1
        centimos = 0

    texto = num2words(entero, lang="es")
    if centimos:
        texto_cent = num2words(centimos, lang="es")
        return f"{texto} euros con {texto_cent} céntimos"
    return f"{texto} euros"


def compute_summary(chapters: Dict[str, float]) -> Dict[str, float]:
    pem = round(sum(float(v) for v in chapters.values()), 2)
    gg = round(pem * GG_PCT, 2)
    bi = round(pem * BI_PCT, 2)
    pbl_sin_iva = round(pem + gg + bi, 2)
    iva = round(pbl_sin_iva * IVA_PCT, 2)
    total = round(pbl_sin_iva + iva, 2)
    return {
        "pem": pem,
        "gg": gg,
        "bi": bi,
        "pel": pbl_sin_iva,
        "iva": iva,
        "total": total,
    }


@st.cache_data
def load_catalog() -> pd.DataFrame:
    path = find_catalog_path()
    df = pd.read_csv(path)

    expected_cols = {"section", "subsection", "name", "unit", "price", "code", "comments"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"El CSV no tiene las columnas esperadas. Faltan: {', '.join(sorted(missing))}"
        )

    df = df.copy()
    df["section"] = df["section"].fillna("").astype(str)
    df["subsection"] = df["subsection"].fillna("").astype(str)
    df["name"] = df["name"].fillna("").astype(str)
    df["unit"] = df["unit"].fillna("").astype(str)
    df["code"] = df["code"].fillna("").astype(str)
    df["comments"] = df["comments"].fillna("").astype(str)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)

    df["display_name"] = (
        df["code"].where(df["code"].str.strip() != "", "SIN CÓDIGO")
        + " · "
        + df["name"]
        + " ("
        + df["unit"]
        + ")"
    )
    return df.reset_index(drop=True)


def render_summary_blocks(summary: Dict[str, float]) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("PEM", euro(summary["pem"]))
    col2.metric("Base sin IVA", euro(summary["pel"]))
    col3.metric("Total con IVA", euro(summary["total"]))

    st.markdown("---")
    st.markdown(f"**Presupuesto de Ejecución Material**  \n{euro(summary['pem'])}")
    st.markdown(f"**13 % Gastos Generales**  \n{euro(summary['gg'])}")
    st.markdown(f"**6 % Beneficio Industrial**  \n{euro(summary['bi'])}")
    st.markdown(f"**Presupuesto Base de Licitación excluido IVA**  \n{euro(summary['pel'])}")
    st.markdown(f"**21 % IVA**  \n{euro(summary['iva'])}")
    st.markdown(f"**Presupuesto Base de Licitación incluido IVA**  \n{euro(summary['total'])}")

    texto = money_to_words_es(summary["total"]).upper()
    st.info(
        "ASCIENDE EL PRESUPUESTO BASE DE LICITACIÓN A LA EXPRESADA CANTIDAD DE "
        f"{texto} ({euro(summary['total'])})."
    )


def render_chapter_output(chapters: Dict[str, float]) -> None:
    for chapter_id, (chapter_name, _) in CHAPTER_DEFAULTS.items():
        with st.container(border=True):
            st.markdown(f"**Capítulo: {chapter_id}**")
            st.markdown(chapter_name)
            st.markdown(f"### {euro(chapters[chapter_id])}")


st.set_page_config(
    page_title="LicitAIA · Calculadora de presupuesto",
    page_icon="💶",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetricValue"] {font-size: 1.55rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💶 LicitAIA · Calculadora de presupuesto")
st.caption("Aplicación en Streamlit basada únicamente en los datos del CSV y en el resumen de capítulos proporcionado.")

with st.sidebar:
    st.header("Configuración")
    mode = st.radio(
        "Modo de trabajo",
        ["Resumen por capítulos", "Detalle desde catálogo CSV"],
    )
    st.markdown("---")
    st.write("**Parámetros de cálculo**")
    st.write(f"- Gastos generales: {int(GG_PCT * 100)} %")
    st.write(f"- Beneficio industrial: {int(BI_PCT * 100)} %")
    st.write(f"- IVA: {int(IVA_PCT * 100)} %")

try:
    catalog = load_catalog()
except Exception as exc:
    st.error(f"No se ha podido cargar el catálogo: {exc}")
    st.stop()

if mode == "Resumen por capítulos":
    st.subheader("Resumen por capítulos")
    st.write(
        "Introduce o revisa los importes de cada capítulo. "
        "Los capítulos 07 y 08 se pueden activar o desactivar con casilla tipo S/N."
    )

    chapters: Dict[str, float] = {}
    left, right = st.columns(2)

    for idx, (chapter_id, (chapter_name, default_value)) in enumerate(CHAPTER_DEFAULTS.items()):
        container = left if idx % 2 == 0 else right
        with container:
            with st.container(border=True):
                st.markdown(f"**Capítulo {chapter_id}**")
                st.write(chapter_name)

                if chapter_id in {"07", "08"}:
                    enabled = st.checkbox(
                        f"Incluir {chapter_name}",
                        value=True,
                        key=f"enabled_{chapter_id}",
                    )
                    value = st.number_input(
                        "Importe (€)",
                        min_value=0.0,
                        value=float(default_value),
                        step=100.0,
                        disabled=not enabled,
                        key=f"chapter_{chapter_id}",
                    )
                    chapters[chapter_id] = float(value) if enabled else 0.0
                else:
                    value = st.number_input(
                        "Importe (€)",
                        min_value=0.0,
                        value=float(default_value),
                        step=100.0,
                        key=f"chapter_{chapter_id}",
                    )
                    chapters[chapter_id] = float(value)

                st.caption(f"Valor actual: {euro(chapters[chapter_id])}")

    summary = compute_summary(chapters)

    st.subheader("Resultado")
    render_chapter_output(chapters)
    render_summary_blocks(summary)

else:
    st.subheader("Detalle desde catálogo CSV")
    st.write(
        "Selecciona partidas del catálogo, filtra por sección y mete cantidades. "
        "Las partidas tipo S/N se activan con checkbox."
    )

    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        selected_sections = st.multiselect(
            "Filtrar por sección",
            sorted([s for s in catalog["section"].unique() if s]),
            default=[],
        )
    with filter_col2:
        search_text = st.text_input("Buscar por código o nombre", placeholder="Ej. 1.2.05, bordillo, zanja...")

    filtered = catalog.copy()
    if selected_sections:
        filtered = filtered[filtered["section"].isin(selected_sections)]
    if search_text.strip():
        q = search_text.strip().lower()
        filtered = filtered[
            filtered["display_name"].str.lower().str.contains(q)
            | filtered["comments"].str.lower().str.contains(q)
        ]

    st.caption(f"Partidas encontradas: {len(filtered)}")

    selected_ids = st.multiselect(
        "Selecciona partidas",
        options=list(filtered.index),
        format_func=lambda idx: filtered.loc[idx, "display_name"],
        placeholder="Elige una o varias partidas",
    )

    chapter_totals = {k: 0.0 for k in CHAPTER_DEFAULTS.keys()}
    detail_rows: List[dict] = []

    for idx in selected_ids:
        row = filtered.loc[idx]
        chapter_id = CATALOG_CHAPTER_MAP.get(str(row["section"]), "02")

        with st.container(border=True):
            st.markdown(f"**{row['display_name']}**")
            st.caption(f"Sección: {row['section']} · Subsección: {row['subsection']} · Capítulo estimado: {chapter_id}")

            if row["comments"].strip():
                with st.expander("Ver observaciones"):
                    st.write(row["comments"])

            apply_row = st.checkbox(
                "Aplicar esta partida (S/N)",
                value=True,
                key=f"apply_{idx}",
            )

            qty = 0.0
            if apply_row:
                default_qty = 1.0 if str(row["unit"]).lower() in {"ud", "%"} else 0.0
                step = 1.0 if str(row["unit"]).lower() in {"ud", "%"} else 0.5
                qty = st.number_input(
                    f"Cantidad [{row['unit']}]",
                    min_value=0.0,
                    value=float(default_qty),
                    step=float(step),
                    key=f"qty_{idx}",
                )

            amount = round(float(qty) * float(row["price"]), 2)
            chapter_totals[chapter_id] += amount

            c1, c2, c3 = st.columns(3)
            c1.metric("Precio unitario", euro(row["price"]))
            c2.metric("Cantidad", f"{qty:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            c3.metric("Importe", euro(amount))

            detail_rows.append(
                {
                    "Capítulo": chapter_id,
                    "Código": row["code"],
                    "Sección": row["section"],
                    "Subsección": row["subsection"],
                    "Partida": row["name"],
                    "Unidad": row["unit"],
                    "Precio unitario (€)": round(float(row["price"]), 2),
                    "Cantidad": round(float(qty), 2),
                    "Importe (€)": amount,
                }
            )

    with st.expander("Añadir importes manuales por capítulos no cubiertos por el CSV"):
        st.write(
            "El CSV no contiene todas las partidas necesarias para todos los capítulos. "
            "Aquí puedes completar importes sin salir de la aplicación."
        )
        adj_left, adj_right = st.columns(2)
        for idx, (chapter_id, (chapter_name, _)) in enumerate(CHAPTER_DEFAULTS.items()):
            target = adj_left if idx % 2 == 0 else adj_right
            with target:
                supplement = st.number_input(
                    f"Ajuste manual {chapter_id} · {chapter_name}",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    key=f"supp_{chapter_id}",
                )
                chapter_totals[chapter_id] += float(supplement)

    summary = compute_summary(chapter_totals)

    st.subheader("Desglose de partidas")
    if detail_rows:
        detail_df = pd.DataFrame(detail_rows)
        st.dataframe(detail_df, use_container_width=True, hide_index=True)
        csv_export = detail_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar desglose en CSV",
            data=csv_export,
            file_name="desglose_presupuesto.csv",
            mime="text/csv",
        )
    else:
        st.warning("Todavía no has seleccionado ninguna partida.")

    st.subheader("Resumen final")
    render_chapter_output(chapter_totals)
    render_summary_blocks(summary)
