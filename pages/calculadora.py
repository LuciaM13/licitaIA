"""Página de cálculo de presupuestos EMASESA."""

from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from src.aplicacion.calcular_presupuesto import calcular_presupuesto
from src.domain.parametros import ParametrosProyecto
from src.ui.precios_cache import cargar_precios
from src.aplicacion.historial import guardar_presupuesto
from src.infraestructura.utils import euro, find_by_label, generar_texto_word, validar_parametros
from src.reglas.alertas_clips import generar_alertas_tecnicas
from src.reglas.normalizacion import regla_pct_manual
from src.ui.inputs import input_tuberia, input_subbase
from src.ui.materiales import format_material, opciones_material
from src.ui.session import claves as sk

logger = logging.getLogger(__name__)

# Defaults compartidos entre la pre-evaluación inline y los widgets (M3).
# Si se cambia el orden de opciones de los radios, actualizar estas constantes
# para que la pre-evaluación no diverja silenciosamente del widget.
_DEFAULT_INSTALACION = "enterrada"
_DEFAULT_DESMONTAJE = "none"


# ─── Cargar precios desde JSON ────────────────────────────────────────────────

try:
    precios = cargar_precios()
except ValueError as e:
    st.error(
        f"No se pudieron cargar los precios: {e}\n\n"
        "Ve a la página **Administración de precios** para corregirlo, "
        "o restaura una copia de seguridad de `precios.db`."
    )
    st.stop()

dui = precios["defaults_ui"]

CATALOGO_ABA = precios["catalogo_aba"]
CATALOGO_SAN = precios["catalogo_san"]
ACERADOS_ABA = precios["acerados_aba"]
ACERADOS_SAN = precios["acerados_san"]
BORDILLOS_REPOSICION = precios["bordillos_reposicion"]
CALZADAS_REPOSICION = precios["calzadas_reposicion"]

_listas_requeridas = {
    "acerados_aba": ACERADOS_ABA,
    "acerados_san": ACERADOS_SAN,
    "bordillos_reposicion": BORDILLOS_REPOSICION,
    "calzadas_reposicion": CALZADAS_REPOSICION,
}
_listas_vacias = [nombre for nombre, lista in _listas_requeridas.items() if not lista]
if _listas_vacias:
    st.error(
        "Los siguientes catálogos están vacíos y la calculadora no puede arrancar: "
        + ", ".join(f"`{n}`" for n in _listas_vacias)
        + "\n\nVe a **Administración de precios** para añadir al menos un elemento."
    )
    st.stop()

# ─── Cabecera ────────────────────────────────────────────────────────────────

st.title("Cálculo de presupuestos")


# ─── Selector de modo ──────────────────────────────────────────────────────

modo = st.radio(
    "Tipo de actuación",
    ["Solo Abastecimiento", "Solo Saneamiento", "Abastecimiento + Saneamiento"],
    horizontal=True,
    key="modo_actuacion",
)
incluir_aba = modo in ("Solo Abastecimiento", "Abastecimiento + Saneamiento")
incluir_san = modo in ("Solo Saneamiento", "Abastecimiento + Saneamiento")

_sec = 0  # Contador de secciones visibles


# ─── Helpers de UI ────────────────────────────────────────────────────────


def _mostrar_resultados(r: dict) -> None:
    st.markdown("## Resumen económico")

    if r.get("pct_seguridad_info", 0) > 0 or r.get("pct_gestion_info", 0) > 0:
        st.info(f"Seguridad y Salud representa el **{r['pct_seguridad_info']:.2f}%** del subtotal de obra · "
                f"Gestión Ambiental representa el **{r['pct_gestion_info']:.2f}%** del subtotal de obra")

    metrics = [
        ("PEM", r["pem"]),
        ("PBL sin IVA", r["pbl_sin_iva"]),
        ("IVA", r["iva"]),
        ("TOTAL", r["total"]),
    ]
    for col, (label, val) in zip(st.columns(len(metrics)), metrics):
        col.markdown(f"**{label}**\n\n### {euro(val)}")

    st.markdown("### Partidas de cada capítulo")
    for cap, info in r["capitulos"].items():
        with st.expander(f"{cap} · {euro(info['subtotal'])}"):
            df = pd.DataFrame([{"Partida": nombre, "Importe": euro(v)}
                               for nombre, v in info["partidas"].items() if v != 0])
            if df.empty:
                st.info("Sin partidas en este capítulo.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Bloque listo para copiar a Word")
    st.text_area("Texto del presupuesto", value=generar_texto_word(r), height=320)


# ─── Valores por defecto para secciones no activas ─────────────────────────
aba_item = None
aba_longitud_m = 0.0
aba_profundidad_m = dui["aba_profundidad_m"]
pav_aba_acerado_m2 = 0.0
pav_aba_acerado_item = ACERADOS_ABA[0]
pav_aba_bordillo_m = 0.0
pav_aba_bordillo_item = BORDILLOS_REPOSICION[0]
pav_aba_calzada_m2 = 0.0
pav_aba_calzada_item = CALZADAS_REPOSICION[0]
acometidas_aba_n = 0

san_item = None
san_longitud_m = 0.0
san_profundidad_m = dui["san_profundidad_m"]
pav_san_calzada_m2 = 0.0
pav_san_calzada_item = CALZADAS_REPOSICION[0]
pav_san_acera_m2 = 0.0
pav_san_acera_item = ACERADOS_SAN[0]
acometidas_san_n = 0

# Defaults materiales a demoler (coinciden con ParametrosProyecto defaults).
# Sobreescritos por los selectboxes si la red está activa y la superficie > 0.
material_demo_bordillo_aba = "granitico"
material_demo_acerado_aba = "losa_hidraulica"
material_demo_calzada_aba = "aglomerado"
material_demo_acerado_san = "losa_hidraulica"
material_demo_calzada_san = "aglomerado"
subbase_aba_espesor = 0.0
subbase_aba_item = None
subbase_san_espesor = 0.0
subbase_san_item = None
# Defaults para variables que se definen más abajo en el formulario
# pero se necesitan aquí para la pre-evaluación inline.
# Streamlit persiste los valores en session_state tras el primer render.
# Las constantes _DEFAULT_* deben coincidir con la primera opción del radio
# correspondiente (M3).
instalacion_valvuleria = st.session_state.get(sk.INSTALACION_VALVULERIA, _DEFAULT_INSTALACION)
desmontaje_tipo = st.session_state.get(sk.DESMONTAJE_TIPO, _DEFAULT_DESMONTAJE)


# ─── Sección ABA ───────────────────────────────────────────────────────────

if incluir_aba:
    _sec += 1
    st.markdown(f"## {_sec}) Abastecimiento")
    aba_item, aba_longitud_m, aba_profundidad_m = input_tuberia(
        "ABAS", CATALOGO_ABA, dui["aba_longitud_m"], dui["aba_profundidad_m"])


# ─── Sección SAN ───────────────────────────────────────────────────────────

if incluir_san:
    _sec += 1
    st.markdown(f"## {_sec}) Saneamiento")
    san_item, san_longitud_m, san_profundidad_m = input_tuberia(
        "SAN", CATALOGO_SAN, dui["san_longitud_m"], dui["san_profundidad_m"])


# ─── Pavimentación ABA ─────────────────────────────────────────────────────

if incluir_aba:
    _sec += 1
    st.markdown(f"## {_sec}) Pavimentación abastecimiento")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        pav_aba_acerado_m2 = st.number_input("Pav ABAS · m² de acerado", min_value=0.0, value=dui["pav_aba_acerado_m2"], key="pav_aba_acerado_m2")
    with p2:
        pav_aba_acerado_label = st.selectbox("Pav ABAS · tipo de acerado", [x["label"] for x in ACERADOS_ABA], key="pav_aba_acerado_label")
    with p3:
        pav_aba_bordillo_m = st.number_input("Pav ABAS · longitud bordillo (m)", min_value=0.0, value=dui["pav_aba_bordillo_m"], key="pav_aba_bordillo_m")
    with p4:
        pav_aba_bordillo_label = st.selectbox("Pav ABAS · tipo de bordillo", [x["label"] for x in BORDILLOS_REPOSICION], key="pav_aba_bordillo_label")

    # Selectores de material a DEMOLER (distinto de la reposición de arriba).
    # Solo se muestran si hay cantidad > 0 para no saturar la UI.
    material_demo_acerado_aba = "losa_hidraulica"
    material_demo_bordillo_aba = "granitico"
    if pav_aba_acerado_m2 > 0 or pav_aba_bordillo_m > 0:
        d1, d2 = st.columns(2)
        with d1:
            if pav_aba_acerado_m2 > 0:
                _opts_acer_aba = opciones_material(precios, "demolicion_aba", "acerado", "m2")
                if _opts_acer_aba:
                    material_demo_acerado_aba = st.selectbox(
                        "Pav ABAS · material a demoler (acerado)", _opts_acer_aba,
                        format_func=format_material, key="material_demo_acerado_aba")
        with d2:
            if pav_aba_bordillo_m > 0:
                _opts_bord_aba = opciones_material(precios, "demolicion_aba", "bordillo", "m")
                if _opts_bord_aba:
                    material_demo_bordillo_aba = st.selectbox(
                        "Pav ABAS · material a demoler (bordillo)", _opts_bord_aba,
                        format_func=format_material, key="material_demo_bordillo_aba")

    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        pav_aba_calzada_m2 = st.number_input("Pav ABAS · m² de calzada", min_value=0.0, value=0.0, key="pav_aba_calzada_m2")
    with pc2:
        if pav_aba_calzada_m2 > 0:
            pav_aba_calzada_label = st.selectbox("Pav ABAS · tipo de calzada", [x["label"] for x in CALZADAS_REPOSICION], key="pav_aba_calzada_label")
        else:
            pav_aba_calzada_label = CALZADAS_REPOSICION[0]["label"]
    material_demo_calzada_aba = "aglomerado"
    with pc3:
        if pav_aba_calzada_m2 > 0:
            _opts_calz_aba = opciones_material(precios, "demolicion_aba", "calzada", "m2")
            if _opts_calz_aba:
                material_demo_calzada_aba = st.selectbox(
                    "Pav ABAS · material a demoler (calzada)", _opts_calz_aba,
                    format_func=format_material, key="material_demo_calzada_aba")
    try:
        pav_aba_acerado_item = find_by_label(ACERADOS_ABA, pav_aba_acerado_label)
        pav_aba_bordillo_item = find_by_label(BORDILLOS_REPOSICION, pav_aba_bordillo_label)
        pav_aba_calzada_item = find_by_label(CALZADAS_REPOSICION, pav_aba_calzada_label)
    except ValueError as e:
        st.error(f"Error en catálogo de materiales: {e}")
        st.stop()
    espesores = precios["espesores_calzada"]
    if pav_aba_calzada_m2 > 0 and pav_aba_calzada_item.get("unidad") == "m3":
        esp = espesores.get(pav_aba_calzada_item["label"])
        if esp is not None:
            st.info(f"Calzada {pav_aba_calzada_item['label']}: conversión automática m² → m³ con espesor {esp:.2f} m.")
        else:
            st.error(f"No existe espesor definido para '{pav_aba_calzada_item['label']}'. "
                     "Añádelo en la página de Administración de precios → Espesores de calzada.")
            st.stop()
    subbase_aba_espesor, subbase_aba_item = input_subbase(
        "ABA", precios.get("catalogo_subbases", []))


# ─── Pavimentación SAN ─────────────────────────────────────────────────────

if incluir_san:
    _sec += 1
    st.markdown(f"## {_sec}) Pavimentación saneamiento")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        pav_san_calzada_m2 = st.number_input("Pav SAN · m² de calzada", min_value=0.0, value=dui["pav_san_calzada_m2"], key="pav_san_calzada_m2")
    with q2:
        pav_san_calzada_label = st.selectbox("Pav SAN · tipo de calzada", [x["label"] for x in CALZADAS_REPOSICION], key="pav_san_calzada_label")
    with q3:
        pav_san_acera_m2 = st.number_input("Pav SAN · m² de acera", min_value=0.0, value=dui["pav_san_acera_m2"], key="pav_san_acera_m2")
    with q4:
        pav_san_acera_label = st.selectbox("Pav SAN · tipo de acera", [x["label"] for x in ACERADOS_SAN], key="pav_san_acera_label")

    # Selectores de material a DEMOLER (independientes de reposición de arriba).
    material_demo_calzada_san = "aglomerado"
    material_demo_acerado_san = "losa_hidraulica"
    if pav_san_calzada_m2 > 0 or pav_san_acera_m2 > 0:
        dS1, dS2 = st.columns(2)
        with dS1:
            if pav_san_calzada_m2 > 0:
                _opts_calz_san = opciones_material(precios, "demolicion_san", "calzada", "m2")
                if _opts_calz_san:
                    material_demo_calzada_san = st.selectbox(
                        "Pav SAN · material a demoler (calzada)", _opts_calz_san,
                        format_func=format_material, key="material_demo_calzada_san")
        with dS2:
            if pav_san_acera_m2 > 0:
                _opts_acer_san = opciones_material(precios, "demolicion_san", "acerado", "m2")
                if _opts_acer_san:
                    material_demo_acerado_san = st.selectbox(
                        "Pav SAN · material a demoler (acera)", _opts_acer_san,
                        format_func=format_material, key="material_demo_acerado_san")
    try:
        pav_san_calzada_item = find_by_label(CALZADAS_REPOSICION, pav_san_calzada_label)
        pav_san_acera_item = find_by_label(ACERADOS_SAN, pav_san_acera_label)
    except ValueError as e:
        st.error(f"Error en catálogo de materiales: {e}")
        st.stop()
    espesores = precios["espesores_calzada"]
    if pav_san_calzada_m2 > 0 and pav_san_calzada_item["unidad"] == "m3":
        esp = espesores.get(pav_san_calzada_item["label"])
        if esp is not None:
            st.info(f"Calzada {pav_san_calzada_item['label']}: conversión automática m² → m³ con espesor {esp:.2f} m.")
        else:
            st.error(f"No existe espesor definido para '{pav_san_calzada_item['label']}'. "
                     "Añádelo en la página de Administración de precios → Espesores de calzada.")
            st.stop()
    subbase_san_espesor, subbase_san_item = input_subbase(
        "SAN", precios.get("catalogo_subbases", []))


# ─── Acometidas ─────────────────────────────────────────────────────────────

_sec += 1
st.markdown(f"## {_sec}) Acometidas")
c1, c2 = st.columns(2)
with c1:
    if incluir_aba:
        acometidas_aba_n = int(st.number_input("Nº acometidas ABA", min_value=0, value=int(dui["acometidas_n"]), key="acometidas_aba_n"))
with c2:
    if incluir_san:
        acometidas_san_n = int(st.number_input("Nº acometidas SAN", min_value=0, value=int(dui["acometidas_n"]), key="acometidas_san_n"))


# ─── Parámetros de obra ───────────────────────────────────────────────────

conduccion_provisional_m = 0.0
espesor_pavimento_m = 0.0
pct_servicios_afectados = 0.0
pozos_existentes_aba = "none"
pozos_existentes_san = "none"
imbornales_tipo = "none"
imbornales_nuevo_label = ""

_sec += 1
st.markdown(f"## {_sec}) Parámetros de obra")

# % excavación manual calculado por regla (profundidad máxima de las redes activas)
_prof_max = max(
    aba_profundidad_m if incluir_aba else 0.0,
    san_profundidad_m if incluir_san else 0.0,
)
_pct_manual_auto, _pct_manual_expl = regla_pct_manual(_prof_max) if _prof_max > 0 else (0.30, "Sin profundidad definida → 30%")

# Sincronizar session_state antes del widget: Streamlit ignora `value=` cuando
# la key ya existe en session_state, por lo que hay que actualizar la clave
# directamente cuando la regla recalcula (B1).
_auto_pct_int = int(_pct_manual_auto * 100)
if st.session_state.get(sk.PCT_MANUAL_AUTO_LAST) != _auto_pct_int:
    st.session_state[sk.PCT_MANUAL_PCT] = _auto_pct_int
    st.session_state[sk.PCT_MANUAL_AUTO_LAST] = _auto_pct_int

o1, o2, o3 = st.columns(3)
with o1:
    pct_manual_pct = st.number_input(
        "% Excavación manual",
        min_value=0, max_value=100,
        step=5,
        key="pct_manual_pct")
with o2:
    pct_seguridad = st.number_input(
        "Seguridad y Salud (%)",
        min_value=0.0, max_value=20.0,
        value=dui["pct_seguridad"] * 100,
        step=0.5, format="%.1f",
        key="pct_seguridad") / 100.0
with o3:
    pct_gestion = st.number_input(
        "Gestión Ambiental (%)",
        min_value=0.0, max_value=20.0,
        value=dui["pct_gestion"] * 100,
        step=0.5, format="%.1f",
        key="pct_gestion") / 100.0

# Servicios Afectados y espesor pavimento en segunda fila
o4, o5 = st.columns(2)
with o4:
    pct_servicios_afectados = st.number_input(
        "Servicios Afectados (%)",
        min_value=0.0, max_value=10.0, value=0.0, step=0.5, format="%.1f",
        key="pct_servicios_afectados") / 100.0
with o5:
    _hay_demolicion = (
        (incluir_aba and (pav_aba_acerado_m2 > 0 or pav_aba_bordillo_m > 0 or pav_aba_calzada_m2 > 0)) or
        (incluir_san and (pav_san_calzada_m2 > 0 or pav_san_acera_m2 > 0))
    )
    if _hay_demolicion:
        espesor_pavimento_m = st.number_input(
            "Espesor pavimento demolido (m)",
            min_value=0.0, value=0.35, step=0.05, format="%.2f",
            key="espesor_pavimento_m")

if incluir_aba:
    conduccion_provisional_m = st.number_input(
        "Conducción provisional PE (m)",
        min_value=0.0, value=float(dui.get("conduccion_provisional_m", 0.0)),
        step=10.0,
        key="conduccion_provisional_m")

# ── Desmontaje tubería y pozos existentes ───────────────────────────────────
_cat_desmontaje = precios.get("catalogo_desmontaje", [])
_cat_imbornales = precios.get("catalogo_imbornales", [])
_cat_pozex = precios.get("catalogo_pozos_existentes", [])

if incluir_aba and _cat_desmontaje:
    o_d1, o_d2 = st.columns(2)
    with o_d1:
        desmontaje_tipo = st.radio(
            "Tubería existente a desmontar (ABA)",
            ["none", "normal", "fibrocemento"],
            format_func=lambda x: {"none": "No hay", "normal": "Desmontaje normal", "fibrocemento": "Demol. fibrocemento"}[x],
            horizontal=True, key="desmontaje_tipo")
    with o_d2:
        _pozex_aba_opts = [("none", "No hay")]
        if any(x["red"] == "ABA" and x["accion"] == "demolicion" for x in _cat_pozex):
            _pozex_aba_opts.append(("demolicion", "Demolición"))
        if any(x["red"] == "ABA" and x["accion"] == "anulacion" for x in _cat_pozex):
            _pozex_aba_opts.append(("anulacion", "Anulación"))
        if len(_pozex_aba_opts) > 1:
            pozos_existentes_aba = st.radio(
                "Pozos existentes ABA",
                [o[0] for o in _pozex_aba_opts],
                format_func=lambda x: dict(_pozex_aba_opts)[x],
                horizontal=True, key="pozex_aba")

if incluir_san and (_cat_imbornales or _cat_pozex):
    q_i1, q_i2 = st.columns(2)
    with q_i1:
        if _cat_imbornales:
            _imb_opts = [("none", "No hay imbornales")]
            if any(x["tipo"] == "adaptacion" for x in _cat_imbornales):
                _imb_opts.append(("adaptacion", "Adaptación"))
            _nuevos = [x["label"] for x in _cat_imbornales if x["tipo"] == "nuevo"]
            if _nuevos:
                _imb_opts.append(("nuevo", "Nuevos"))
            imbornales_tipo = st.radio(
                "Imbornales SAN",
                [o[0] for o in _imb_opts],
                format_func=lambda x: dict(_imb_opts)[x],
                horizontal=True, key="imbornales_tipo")
            if imbornales_tipo == "nuevo" and _nuevos:
                imbornales_nuevo_label = st.selectbox("Tipo imbornal nuevo", _nuevos, key="imb_label")
    with q_i2:
        _pozex_san_opts = [("none", "No hay")]
        if any(x["red"] == "SAN" and x["accion"] == "demolicion" for x in _cat_pozex):
            _pozex_san_opts.append(("demolicion", "Demolición"))
        if any(x["red"] == "SAN" and x["accion"] == "anulacion" for x in _cat_pozex):
            _pozex_san_opts.append(("anulacion", "Anulación"))
        if len(_pozex_san_opts) > 1:
            pozos_existentes_san = st.radio(
                "Pozos existentes SAN",
                [o[0] for o in _pozex_san_opts],
                format_func=lambda x: dict(_pozex_san_opts)[x],
                horizontal=True, key="pozex_san")

if incluir_aba:
    instalacion_valvuleria = st.radio(
        "Instalación valvulería",
        [_DEFAULT_INSTALACION, "pozo"],
        horizontal=True,
        key="instalacion_valvuleria")
else:
    instalacion_valvuleria = _DEFAULT_INSTALACION


# ─── Validación técnica ───────────────────────────────────────────────────

_sec += 1
st.markdown(f"## {_sec}) Validación técnica")

_se_resultado = generar_alertas_tecnicas(
    aba_activa=incluir_aba,
    san_activa=incluir_san,
    aba_longitud_m=aba_longitud_m,
    aba_profundidad_m=aba_profundidad_m,
    san_profundidad_m=san_profundidad_m,
    aba_diametro_mm=int(aba_item["diametro_mm"]) if aba_item else 0,
    san_diametro_mm=int(san_item["diametro_mm"]) if san_item else 0,
    aba_tipo_tuberia=aba_item.get("tipo", "") if aba_item else "",
    acometidas_aba_n=acometidas_aba_n,
    acometidas_san_n=acometidas_san_n,
    desmontaje_tipo=desmontaje_tipo,
    pct_seguridad=pct_seguridad,
    pct_gestion=pct_gestion,
    pct_servicios_afectados=pct_servicios_afectados,
    conduccion_provisional_m=conduccion_provisional_m,
    pozos_existentes_aba=pozos_existentes_aba,
    pozos_existentes_san=pozos_existentes_san,
    instalacion_valvuleria=instalacion_valvuleria,
)
_etiquetas = _se_resultado["etiquetas"]
_alertas = _se_resultado["alertas"]

# ── Clasificación del proyecto (etiquetas del sistema experto) ──
# El orden de agenda de CLIPS no es reproducible entre ejecuciones, así
# que ordenamos por severidad descendente (alta → media → baja) y dentro
# del mismo nivel por nombre alfabético.
_ORDEN_SEVERIDAD = {"alta": 0, "media": 1, "baja": 2}
_COLOR_SEVERIDAD = {"alta": "red", "media": "orange", "baja": "blue"}

if _etiquetas:
    st.markdown("**Clasificación del proyecto:**")
    _etiquetas_ord = sorted(
        _etiquetas,
        key=lambda e: (_ORDEN_SEVERIDAD.get(e["severidad"], 9), e["nombre"]),
    )
    _chips = " ".join(
        f":{_COLOR_SEVERIDAD.get(e['severidad'], 'gray')}-background[{e['nombre']}]"
        for e in _etiquetas_ord
    )
    st.markdown(_chips)

# ── Alertas al licitador ──
if not _alertas:
    st.success("Sin alertas. El presupuesto está listo para calcular.")
else:
    for _alerta in _alertas:
        if _alerta["nivel"] == "error":
            st.error(_alerta["msg"])
        elif _alerta["nivel"] == "warning":
            st.warning(_alerta["msg"])
        else:
            st.info(_alerta["msg"])


# ─── Calcular presupuesto ─────────────────────────────────────────────────

if st.button("Calcular presupuesto", type="primary", use_container_width=True, key="btn_calcular"):
    p = ParametrosProyecto(
        aba_item=aba_item,
        aba_longitud_m=aba_longitud_m,
        aba_profundidad_m=aba_profundidad_m,
        san_item=san_item,
        san_longitud_m=san_longitud_m,
        san_profundidad_m=san_profundidad_m,
        pav_aba_acerado_m2=pav_aba_acerado_m2,
        pav_aba_acerado_item=pav_aba_acerado_item,
        pav_aba_bordillo_m=pav_aba_bordillo_m,
        pav_aba_bordillo_item=pav_aba_bordillo_item,
        pav_aba_calzada_m2=pav_aba_calzada_m2,
        pav_aba_calzada_item=pav_aba_calzada_item,
        pav_san_calzada_m2=pav_san_calzada_m2,
        pav_san_calzada_item=pav_san_calzada_item,
        pav_san_acera_m2=pav_san_acera_m2,
        pav_san_acera_item=pav_san_acera_item,
        acometidas_aba_n=acometidas_aba_n,
        acometidas_san_n=acometidas_san_n,
        pct_manual=pct_manual_pct / 100.0,
        conduccion_provisional_m=conduccion_provisional_m,
        instalacion_valvuleria=instalacion_valvuleria,
        pct_seguridad=pct_seguridad,
        pct_gestion=pct_gestion,
        subbase_aba_item=subbase_aba_item if incluir_aba else None,
        subbase_aba_espesor_m=subbase_aba_espesor if incluir_aba else 0.0,
        subbase_san_item=subbase_san_item if incluir_san else None,
        subbase_san_espesor_m=subbase_san_espesor if incluir_san else 0.0,
        espesor_pavimento_m=espesor_pavimento_m,
        pct_servicios_afectados=pct_servicios_afectados,
        desmontaje_tipo=desmontaje_tipo,
        pozos_existentes_aba=pozos_existentes_aba,
        pozos_existentes_san=pozos_existentes_san,
        imbornales_tipo=imbornales_tipo,
        imbornales_nuevo_label=imbornales_nuevo_label,
        material_demo_bordillo_aba=material_demo_bordillo_aba,
        material_demo_acerado_aba=material_demo_acerado_aba,
        material_demo_calzada_aba=material_demo_calzada_aba,
        material_demo_acerado_san=material_demo_acerado_san,
        material_demo_calzada_san=material_demo_calzada_san,
    )
    errores = validar_parametros(p)
    if errores:
        for e in errores:
            st.error(e)
        st.stop()

    try:
        with st.spinner("Calculando presupuesto…"):
            logger.info("▶ Usuario lanza cálculo de presupuesto")
            resultado = calcular_presupuesto(p, precios)
            st.session_state[sk.RESULTADO] = resultado
            logger.info("✓ Cálculo completado - TOTAL=%.2f €", resultado["total"])

            # Guardar en historial automáticamente
            _params_historial = {
                "modo": modo,
            }
            if incluir_aba and aba_item:
                _params_historial.update({
                    "aba_tuberia": aba_item.get("label", ""),
                    "aba_longitud_m": str(aba_longitud_m),
                    "aba_profundidad_m": str(aba_profundidad_m),
                    "aba_diametro_mm": str(aba_item.get("diametro_mm", "")),
                    "instalacion_valvuleria": instalacion_valvuleria,
                })
            if incluir_san and san_item:
                _params_historial.update({
                    "san_tuberia": san_item.get("label", ""),
                    "san_longitud_m": str(san_longitud_m),
                    "san_profundidad_m": str(san_profundidad_m),
                    "san_diametro_mm": str(san_item.get("diametro_mm", "")),
                })
            if incluir_aba:
                _params_historial.update({
                    "pav_aba_acerado_m2": str(pav_aba_acerado_m2),
                    "pav_aba_acerado_label": pav_aba_acerado_item.get("label", ""),
                    "pav_aba_bordillo_m": str(pav_aba_bordillo_m),
                    "pav_aba_bordillo_label": pav_aba_bordillo_item.get("label", ""),
                    "pav_aba_calzada_m2": str(pav_aba_calzada_m2),
                    "pav_aba_calzada_label": pav_aba_calzada_item.get("label", ""),
                    "acometidas_aba_n": str(acometidas_aba_n),
                    "conduccion_provisional_m": str(conduccion_provisional_m),
                    "pozos_existentes_aba": pozos_existentes_aba,
                    "subbase_aba_espesor_m": str(subbase_aba_espesor),
                })
            if incluir_san:
                _params_historial.update({
                    "pav_san_calzada_m2": str(pav_san_calzada_m2),
                    "pav_san_calzada_label": pav_san_calzada_item.get("label", ""),
                    "pav_san_acera_m2": str(pav_san_acera_m2),
                    "pav_san_acera_label": pav_san_acera_item.get("label", ""),
                    "acometidas_san_n": str(acometidas_san_n),
                    "pozos_existentes_san": pozos_existentes_san,
                    "imbornales_tipo": imbornales_tipo,
                    "imbornales_nuevo_label": imbornales_nuevo_label,
                    "subbase_san_espesor_m": str(subbase_san_espesor),
                })
            _params_historial.update({
                "pct_manual": str(pct_manual_pct / 100.0),
                "pct_seguridad": str(pct_seguridad),
                "pct_gestion": str(pct_gestion),
                "pct_servicios_afectados": str(pct_servicios_afectados),
                "espesor_pavimento_m": str(espesor_pavimento_m),
                "desmontaje_tipo": desmontaje_tipo,
            })

            # Descripción automática para el guardado
            _partes = []
            if incluir_aba and aba_item:
                _partes.append(f"ABA {aba_item.get('label', '')} {aba_longitud_m}m")
            if incluir_san and san_item:
                _partes.append(f"SAN {san_item.get('label', '')} {san_longitud_m}m")
            st.session_state[sk.HISTORIAL_DESC] = " + ".join(_partes) if _partes else modo
            st.session_state[sk.HISTORIAL_PARAMS] = _params_historial
            st.session_state[sk.HISTORIAL_PCT_CI] = float(precios.get("pct_ci", 1.0))

    except ValueError as e:
        logger.error("ValueError en cálculo: %s", e)
        st.session_state.pop(sk.RESULTADO, None)
        st.error(str(e))
        st.stop()
    except Exception as e:
        logger.exception("Error inesperado en cálculo de presupuesto")
        st.session_state.pop(sk.RESULTADO, None)
        st.error(
            f"Error inesperado: {type(e).__name__}: {e}\n\n"
            "Comprueba que todos los catálogos en Administración de precios "
            "están completos y no tienen campos vacíos."
        )
        st.stop()

if sk.RESULTADO in st.session_state:
    _mostrar_resultados(st.session_state[sk.RESULTADO])

    # ─── Guardar en historial ───────────────────────────────────────────
    st.markdown("---")
    if st.button("Guardar en historial", type="primary", use_container_width=True, key="btn_guardar"):
        try:
            guardar_presupuesto(
                st.session_state[sk.RESULTADO],
                st.session_state.get(sk.HISTORIAL_PARAMS, {}),
                descripcion=st.session_state.get(sk.HISTORIAL_DESC, ""),
                pct_ci=st.session_state.get(sk.HISTORIAL_PCT_CI, 1.0),
            )
            st.success("Presupuesto guardado en el historial.")
        except Exception as e:
            logger.error("Error al guardar en historial: %s", e, exc_info=True)
            st.error(f"Error al guardar: {e}")
else:
    st.info("Introduce los datos mínimos y pulsa 'Calcular presupuesto'.")
