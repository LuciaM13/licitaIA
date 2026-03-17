import streamlit as st
import pandas as pd

from datos import CATALOGO_ABA, CATALOGO_SAN, TIPOS_REURB
from calcular import calcular_presupuesto

st.set_page_config(
    page_title="LicitaIA",
    page_icon="📊",
    layout="wide",
)

def formato_euro(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown(
    """
    <style>
    :root {
        --bg: #f5f7fa;
        --card: #ffffff;
        --text: #1f2937;
        --muted: #6b7280;
        --border: #d1d5db;
        --primary: #1f3b5b;
        --primary-soft: #eaf0f6;
        --accent: #2f5d8a;
    }

    .stApp {
        background-color: var(--bg);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .hero {
        background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
        color: white;
        padding: 1.8rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(31, 59, 91, 0.15);
    }

    .hero h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.2px;
    }

    .hero p {
        margin-top: 0.45rem;
        margin-bottom: 0;
        font-size: 1rem;
        opacity: 0.95;
    }

    .section-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.25rem 1.25rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary);
        margin-bottom: 0.9rem;
    }

    .info-box {
        background: var(--primary-soft);
        border: 1px solid #d8e2ec;
        border-radius: 12px;
        padding: 1rem;
        color: var(--text);
        height: 100%;
    }

    .info-box h4 {
        margin: 0 0 0.35rem 0;
        color: var(--primary);
        font-size: 1rem;
    }

    .info-box p {
        margin: 0.2rem 0;
        color: var(--text);
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--border);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: var(--muted);
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: var(--primary);
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .small-note {
        color: var(--muted);
        font-size: 0.93rem;
        margin-top: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>LicitaIA</h1>
        <p>Herramienta de estimación presupuestaria para actuaciones de abastecimiento, saneamiento y reurbanización.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

aba_labels = [item["label"] for item in CATALOGO_ABA]
san_labels = [item["label"] for item in CATALOGO_SAN]
reurb_labels = [item["label"] for item in TIPOS_REURB]

with st.sidebar:
    st.markdown("## Parámetros de cálculo")
    st.markdown('<p class="small-note">Introduzca las magnitudes y seleccione las tipologías correspondientes.</p>', unsafe_allow_html=True)

    st.markdown("### Abastecimiento")
    metros_aba = st.number_input(
        "Longitud ABA (m)",
        min_value=0.0,
        value=100.0,
        step=10.0,
    )
    aba_label = st.selectbox(
        "Tipología ABA",
        aba_labels,
        index=6 if len(aba_labels) > 6 else 0,
    )

    st.markdown("### Saneamiento")
    metros_san = st.number_input(
        "Longitud SAN (m)",
        min_value=0.0,
        value=150.0,
        step=10.0,
    )
    san_label = st.selectbox(
        "Tipología SAN",
        san_labels,
        index=4 if len(san_labels) > 4 else 0,
    )

    st.markdown("### Reurbanización")
    reurb_label = st.selectbox(
        "Tipología de reurbanización",
        reurb_labels,
        index=0,
    )

    st.markdown("")
    calcular = st.button("Calcular presupuesto", use_container_width=True)

precios_aba = next(item for item in CATALOGO_ABA if item["label"] == aba_label)
precios_san = next(item for item in CATALOGO_SAN if item["label"] == san_label)
reurbanizacion = next(item for item in TIPOS_REURB if item["label"] == reurb_label)

if calcular:
    resultado = calcular_presupuesto(
        metros_aba=metros_aba,
        precios_aba=precios_aba,
        metros_san=metros_san,
        precios_san=precios_san,
        reurbanizacion=reurbanizacion,
    )

    st.markdown('<div class="section-title">Resumen ejecutivo</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Presupuesto total", formato_euro(resultado["total"]))
    m2.metric("PEM", formato_euro(resultado["pem"]))
    m3.metric("PBL sin IVA", formato_euro(resultado["pbl_sin_iva"]))

    st.markdown("")
    st.markdown('<div class="section-title">Parámetros seleccionados</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="info-box">
                <h4>Abastecimiento</h4>
                <p><strong>Tipología:</strong> {aba_label}</p>
                <p><strong>Longitud:</strong> {metros_aba:,.0f} m</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="info-box">
                <h4>Saneamiento</h4>
                <p><strong>Tipología:</strong> {san_label}</p>
                <p><strong>Longitud:</strong> {metros_san:,.0f} m</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="info-box">
                <h4>Reurbanización</h4>
                <p><strong>Tipología:</strong> {reurb_label}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown('<div class="section-title">Desglose económico</div>', unsafe_allow_html=True)

    etiquetas = {
        "obra_civil_aba": "Obra civil ABA",
        "obra_civil_san": "Obra civil SAN",
        "pavimentacion_aba": "Pavimentación ABA",
        "pavimentacion_san": "Pavimentación SAN",
        "acometidas_aba": "Acometidas ABA",
        "acometidas_san": "Acometidas SAN",
        "seguridad_salud": "Seguridad y salud",
        "gestion_ambiental": "Gestión ambiental",
        "pem": "PEM",
        "gastos_generales": "Gastos generales",
        "beneficio_industrial": "Beneficio industrial",
        "pbl_base": "PBL base",
        "margen_seguridad": "Margen de seguridad",
        "pbl_sin_iva": "PBL sin IVA",
        "iva": "IVA",
        "total": "Total",
    }

    filas = [
        {"Concepto": etiquetas.get(clave, clave), "Importe": valor}
        for clave, valor in resultado.items()
    ]

    df = pd.DataFrame(filas)
    df["Importe"] = df["Importe"].apply(formato_euro)

    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Instrucciones de uso</div>
            <p style="margin-bottom: 0.5rem;">
                Seleccione en la barra lateral las longitudes y tipologías correspondientes a abastecimiento,
                saneamiento y reurbanización.
            </p>
            <p style="margin-bottom: 0;">
                A continuación, pulse <strong>“Calcular presupuesto”</strong> para obtener el resumen económico
                y el desglose detallado de la estimación.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
