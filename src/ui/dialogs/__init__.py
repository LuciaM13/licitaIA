"""Subpaquete de diálogos Streamlit reutilizables.

Cada módulo expone como mucho UNA función decorada con ``@st.dialog``
(hard-limit del framework: 1 dialog por script run). El despacho a
sub-formularios distintos se hace dentro del propio dialog.
"""
