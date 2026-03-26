
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st
from num2words import num2words

BASE_DIR = Path(__file__).resolve().parent
CSV_CANDIDATES = [
    "datos.csv",
    "240415_VALORACIÓN ACTUACIONES(S-BASE PRECIOS ABRIL-'24)).csv",
    "catalogo_precios_limpio.csv",
]

# Datos tomados del documento de presupuesto/pliego
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


def find_csv_path() -> Path:
    for filename in CSV_CANDIDATES:
        path = BASE_DIR / filename
        if path.exists():
            return path
    raise FileNotFoundError(
        "No se encontró el CSV. Sube al repo uno de estos nombres: "
        + ", ".join(CSV_CANDIDATES)
    )


@st.cache_data
def load_catalog() -> pd.DataFrame:
    path = find_csv_path()
    df = pd.read_csv(path)

    expected_cols = {"section", "subsection", "name", "unit", "price", "code", "comments"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en el CSV: {', '.join(sorted(missing))}")

    df = df.copy()
    for col in ["section", "subsection", "name", "unit", "code", "comments"]:
        df[col] = df[col].fillna("").astype(str)

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
        "pbl_sin_iva": pbl_sin_iva,
        "iva": iva,
        "total": total,
    }


def default_chapter_amounts() -> Dict[str, float]:
    return {chapter_id: float(default_value) for chapter_id, (_, default_value) in CHAPTER_DEFAULTS.items()}


def render_budget_view(chapters: Dict[str, float], summary: Dict[str, float]) -> None:
    st.markdown("## Vista previa del presupuesto")

    for chapter_id, (chapter_name, _) in CHAPTER_DEFAULTS.items():
        st.markdown(
            f"""
            <div style="text-align:center; padding:18px 10px;">
                <div style="font-size:22px; font-weight:700;">Capítulo: {chapter_id}</div>
                <div style="font-size:22px; margin-top:8px;">{chapter_name}</div>
                <div style="font-size:26px; font-weight:700; margin-top:10px;">{euro(chapters[chapter_id])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(f"### Presupuesto de Ejecución Material\n**{euro(summary['pem'])}**")
    st.markdown(f"### 13 % Gastos Generales\n**{euro(summary['gg'])}**")
    st.markdown(f"### 6 % Beneficio Industrial\n**{euro(summary['bi'])}**")
    st.markdown(f"### Presupuesto Base de Licitación excluido IVA\n**{euro(summary['pbl_sin_iva'])}**")
    st.markdown(f"### 21 % IVA\n**{euro(summary['iva'])}**")
    st.markdown(f"### Presupuesto Base de Licitación incluido IVA\n**{euro(summary['total'])}**")

    texto = money_to_words_es(summary["total"]).upper()
    st.info(
        "ASCIENDE EL PRESUPUESTO BASE DE LICITACIÓN A LA EXPRESADA CANTIDAD DE "
        f"{texto} ({euro(summary['total'])})."
    )


def chapter_select_options():
    options = ["No asignar"]
    for chapter_id, (chapter_name, _) in CHAPTER_DEFAULTS.items():
        options.append(f"{chapter_id} · {chapter_name}")
    return options


def chapter_key_from_option(option: str) -> str | None:
    if option == "No asignar":
        return None
    return option.split(" · ")[0]


st.set_page_config(page_title="LicitAIA", page_icon="💶", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 2rem;}
    .main-title {
        background: linear-gradient(135deg, #14324a, #234e70);
        color: white;
        padding: 1.3rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.2rem;
    }
    .soft-card {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 0.9rem 1rem;
    }
    div[data-testid="stMetricValue"] {font-size: 1.55rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-title">
        <h1 style="margin:0;">💶 LicitAIA</h1>
        <div style="margin-top:8px;">Calculadora de presupuesto basada solo en los datos del CSV y del documento de presupuesto.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    catalog = load_catalog()
except Exception as exc:
    st.error(f"No se pudo cargar el CSV: {exc}")
    st.stop()

with st.sidebar:
    st.header("Modo")
    mode = st.radio(
        "Selecciona cómo quieres trabajar",
        ["Resumen por capítulos", "Detalle desde CSV"],
    )
    st.markdown("---")
    st.write("**Fórmulas disponibles en el documento**")
    st.write(f"- Gastos Generales: {int(GG_PCT * 100)} %")
    st.write(f"- Beneficio Industrial: {int(BI_PCT * 100)} %")
    st.write(f"- IVA: {int(IVA_PCT * 100)} %")

if mode == "Resumen por capítulos":
    st.subheader("Editar importes por capítulo")
    st.caption("Aquí puedes partir de los importes del documento y ajustarlos manualmente.")

    chapters = {}
    c1, c2 = st.columns(2)

    for idx, (chapter_id, (chapter_name, default_value)) in enumerate(CHAPTER_DEFAULTS.items()):
        target_col = c1 if idx % 2 == 0 else c2
        with target_col:
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
                        "Importe",
                        min_value=0.0,
                        value=float(default_value),
                        step=100.0,
                        key=f"chapter_{chapter_id}",
                        disabled=not enabled,
                    )
                    chapters[chapter_id] = float(value) if enabled else 0.0
                else:
                    value = st.number_input(
                        "Importe",
                        min_value=0.0,
                        value=float(default_value),
                        step=100.0,
                        key=f"chapter_{chapter_id}",
                    )
                    chapters[chapter_id] = float(value)

    summary = compute_summary(chapters)

    m1, m2, m3 = st.columns(3)
    m1.metric("PEM", euro(summary["pem"]))
    m2.metric("PBL sin IVA", euro(summary["pbl_sin_iva"]))
    m3.metric("Total con IVA", euro(summary["total"]))

    render_budget_view(chapters, summary)

else:
    st.subheader("Detalle desde CSV")
    st.caption(
        "Añade solo las partidas que estén en el CSV. Luego asígnalas manualmente al capítulo que corresponda del presupuesto."
    )

    left, right = st.columns([1, 2])

    with left:
        section_options = ["Todas"] + sorted([s for s in catalog["section"].dropna().unique().tolist() if s])
        selected_section = st.selectbox("Filtrar por sección", section_options)
        search = st.text_input("Buscar partida", placeholder="Código, nombre o comentario")
        max_rows = st.slider("Número máximo de partidas a mostrar", min_value=10, max_value=80, value=25, step=5)

    filtered = catalog.copy()
    if selected_section != "Todas":
        filtered = filtered[filtered["section"] == selected_section]

    if search.strip():
        pattern = search.strip().lower()
        mask = (
            filtered["display_name"].str.lower().str.contains(pattern, na=False)
            | filtered["comments"].str.lower().str.contains(pattern, na=False)
            | filtered["subsection"].str.lower().str.contains(pattern, na=False)
        )
        filtered = filtered[mask]

    filtered = filtered.head(max_rows).copy()

    if filtered.empty:
        st.warning("No hay partidas con ese filtro.")
        st.stop()

    st.markdown("### Partidas")
    chapter_options = chapter_select_options()
    chapter_totals = {chapter_id: 0.0 for chapter_id in CHAPTER_DEFAULTS.keys()}
    detail_rows = []

    for idx, row in filtered.iterrows():
        with st.container(border=True):
            top1, top2 = st.columns([5, 1])
            with top1:
                st.markdown(f"**{row['display_name']}**")
                st.caption(f"Sección: {row['section']} · Subsección: {row['subsection']}")
                if row["comments"].strip():
                    st.caption(row["comments"])
            with top2:
                st.markdown(f"**{euro(row['price'])}**")

            a, b, c = st.columns([1, 1, 2])

            with a:
                apply_item = st.checkbox(
                    "S/N",
                    value=False,
                    key=f"apply_{idx}",
                    help="Marca la casilla si quieres incluir esta partida.",
                )
            with b:
                qty = st.number_input(
                    f"Cantidad {row['unit']}",
                    min_value=0.0,
                    value=1.0 if row["unit"] in {"ud", "%"} else 0.0,
                    step=1.0 if row["unit"] in {"ud", "%"} else 0.5,
                    key=f"qty_{idx}",
                    disabled=not apply_item,
                    label_visibility="visible",
                )
            with c:
                chapter_option = st.selectbox(
                    "Capítulo de destino",
                    chapter_options,
                    index=0,
                    key=f"chapter_map_{idx}",
                    disabled=not apply_item,
                )

            amount = round(float(qty) * float(row["price"]), 2) if apply_item else 0.0
            chapter_key = chapter_key_from_option(chapter_option)

            if apply_item and chapter_key:
                chapter_totals[chapter_key] += amount

            if apply_item:
                detail_rows.append(
                    {
                        "Código": row["code"],
                        "Partida": row["name"],
                        "Unidad": row["unit"],
                        "Precio unitario": euro(row["price"]),
                        "Cantidad": qty,
                        "Capítulo": chapter_key or "",
                        "Importe": euro(amount),
                    }
                )

    st.markdown("---")
    st.subheader("Resumen calculado")
    summary = compute_summary(chapter_totals)

    k1, k2, k3 = st.columns(3)
    k1.metric("PEM", euro(summary["pem"]))
    k2.metric("PBL sin IVA", euro(summary["pbl_sin_iva"]))
    k3.metric("Total con IVA", euro(summary["total"]))

    if detail_rows:
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no has marcado ninguna partida del CSV.")

    st.markdown("### Vista previa del presupuesto generado")
    render_budget_view(chapter_totals, summary)
