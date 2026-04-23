"""Constantes de claves de ``st.session_state`` usadas por las páginas.

Cualquier clave que se acceda desde más de un punto (otro fichero, otro
rerun, otro bloque condicional) se declara aquí. Evita la clase de bugs
típica de Streamlit donde un typo en un string no lanza ``KeyError``
sino que devuelve ``None`` silenciosamente.

Las claves que son puramente ``key=`` de un widget Streamlit (leídas solo
por el propio widget en el mismo rerun) pueden quedar como literales; no
aportan riesgo porque el framework las maneja.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Calculadora — flujo de cálculo de presupuesto
# ---------------------------------------------------------------------------

INSTALACION_VALVULERIA = "instalacion_valvuleria"
DESMONTAJE_TIPO = "desmontaje_tipo"
PCT_MANUAL_PCT = "pct_manual_pct"
PCT_MANUAL_AUTO_LAST = "_pct_manual_auto_last"

RESULTADO = "resultado"
"""Último ``ResultadoPresupuesto`` calculado. Persiste entre reruns para
que el botón "Guardar en historial" encuentre el dict sin recalcular."""

HISTORIAL_DESC = "_historial_desc"
HISTORIAL_PARAMS = "_historial_params"
HISTORIAL_PCT_CI = "_historial_pct_ci"


# ---------------------------------------------------------------------------
# Admin precios — flujo de edición con confirmación
# ---------------------------------------------------------------------------

CONFIRMAR_GUARDADO = "confirmar_guardado"
PRECIOS_ORIGINALES = "precios_originales"
PRECIOS_PENDIENTES = "precios_pendientes"
CONFIRMAR_DRIFT_CRITICO = "confirmar_drift_critico"


# ---------------------------------------------------------------------------
# Historial — paginación y detalle
# ---------------------------------------------------------------------------

HIST_PAGE = "hist_page"
VER_DETALLE_ID = "ver_detalle_id"
