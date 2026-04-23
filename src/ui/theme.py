"""
Theming corporativo EMASESA para LicitaIA.

Inyecta variables CSS de marca, tipografía Montserrat (titulares) y overrides
sobre componentes nativos de Streamlit (botones, métricas, sidebar, dataframes,
expanders, header) para alinear la UI con la identidad visual de EMASESA.

Procedencia de los colores:
- Verde #97D700 (Pantone 375 C) y cian #00A9E0 (Pantone 2995 C): logo oficial
  cropped-Logo_2024-300x300.png + emasesa.com (mapa.css) + vectorlogo.es
  (terciaria, no brandbook oficial).
- Variantes web #73BE00 / #1883B3: extraídas del CSS público de emasesa.com.
- Si EMASESA publica un brandbook oficial, verificar contra él y ajustar.

Llamada esperada: una sola vez en el entrypoint (app_licitaia.py), justo después
de st.set_page_config. La doc oficial de Streamlit confirma que el entrypoint
re-ejecuta en cada rerun de la app dentro del modelo st.navigation, así que la
inyección se vuelve a aplicar automáticamente en cada interacción.
"""

from __future__ import annotations

import streamlit as st

_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&display=swap');

:root {
  --emasesa-green: #97D700;
  --emasesa-green-dark: #73BE00;
  --emasesa-cyan: #00A9E0;
  --emasesa-cyan-dark: #1883B3;
  --ink: #1A1A1A;
  --ink-soft: #4A4A4A;
  --surface: #FFFFFF;
  --surface-alt: #F2F4F7;
  --border: #E4E7EC;
}

h1, h2, h3 {
  font-family: 'Montserrat', 'Inter', system-ui, sans-serif !important;
  font-weight: 700 !important;
  color: var(--ink) !important;
  letter-spacing: -0.01em;
}

.stApp .stButton > button {
  background-color: var(--emasesa-green);
  color: var(--ink) !important;
  font-weight: 600;
  border: 1px solid var(--emasesa-green-dark);
  border-radius: 8px;
  padding: 0.5rem 1.1rem;
  transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
}

.stApp .stButton > button:hover {
  background-color: var(--emasesa-green-dark);
  border-color: var(--emasesa-green-dark);
  color: var(--ink) !important;
}

.stApp .stButton > button:active {
  transform: translateY(1px);
}

.stApp .stDownloadButton > button,
.stApp .stFormSubmitButton > button {
  background-color: var(--emasesa-green);
  color: var(--ink) !important;
  font-weight: 600;
  border: 1px solid var(--emasesa-green-dark);
  border-radius: 8px;
}

.stApp .stDownloadButton > button:hover,
.stApp .stFormSubmitButton > button:hover {
  background-color: var(--emasesa-green-dark);
}

[data-testid="stMetric"] {
  background-color: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
}

[data-testid="stMetric"] [data-testid="stMetricLabel"] {
  color: var(--ink-soft);
  font-weight: 500;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-family: 'Montserrat', 'Inter', system-ui, sans-serif;
  font-weight: 700;
  color: var(--ink);
}

[data-testid="stSidebar"] {
  background-color: var(--surface-alt);
  border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] > div:first-child {
  padding-top: 0.75rem;
}

[data-testid="stHeader"] {
  background-color: var(--surface);
  border-bottom: 3px solid var(--emasesa-green);
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

[data-testid="stExpander"] {
  border: 1px solid var(--border);
  border-radius: 10px;
  background-color: var(--surface);
}

[data-testid="stExpander"] summary {
  font-weight: 600;
  color: var(--ink);
}

a, .stApp a {
  color: var(--emasesa-cyan-dark);
  text-decoration: none;
}

a:hover, .stApp a:hover {
  color: var(--emasesa-cyan);
  text-decoration: underline;
}

*:focus-visible {
  outline: 2px solid var(--emasesa-cyan) !important;
  outline-offset: 2px !important;
}
</style>
"""


def inject_global_styles() -> None:
    """Emite el bloque <style> con la identidad EMASESA. Idempotente."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
