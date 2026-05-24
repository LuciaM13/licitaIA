"""Dialog inline para crear nuevas variantes de catálogo desde la calculadora.

Hard-limit del framework: solo 1 ``@st.dialog`` puede invocarse por script
run. Este subpaquete expone una única función ``render_inline_create_dialog``
decorada con ``@st.dialog`` y dispatcha internamente por
``INLINE_CREATE_TARGET`` al sub-formulario que toque.

Frontera de capas: este módulo vive en ``src/ui/`` y SÍ puede importar
``streamlit``. El use case de inserción
(``insertar_variante_catalogo`` / ``insertar_calzada_con_espesor``) vive
en ``src/catalogo/editor/`` sin tocar Streamlit, según
``tests/test_fronteras_capas.py``.
"""

from __future__ import annotations

from src.ui.dialogs.inline_catalogo.dialog import render_inline_create_dialog

__all__ = ["render_inline_create_dialog"]
