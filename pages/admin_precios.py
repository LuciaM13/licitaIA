"""Página de administración de precios EMASESA."""

from __future__ import annotations

import copy

import pandas as pd
import streamlit as st

from src.db import cargar_todo
from src.precios import cargar_precios, guardar_precios
from src.diff_precios import calcular_diff


st.title("Administración de precios")


try:
    precios = cargar_todo()
except (ValueError, Exception) as e:
    st.error(
        f"No se pudieron cargar los precios: {e}\n\n"
        "Comprueba que la base de datos `precios.db` existe en la carpeta data/."
    )
    st.stop()

_pct_ci = float(precios.get("pct_ci", 1.0))

_errores_guardado: list[str] = []
_en_confirmacion = st.session_state.get("confirmar_guardado", False)

if "precios_originales" not in st.session_state or not _en_confirmacion:
    st.session_state["precios_originales"] = copy.deepcopy(precios)

if _en_confirmacion:
    precios = st.session_state.get("precios_pendientes", precios)


# ─── Helpers ─────────────────────────────────────────────────────────────

def _reset_confirmacion() -> None:
    """Limpia el estado de confirmación de guardado y fuerza rerun."""
    st.session_state["confirmar_guardado"] = False
    st.session_state.pop("precios_pendientes", None)
    st.session_state.pop("precios_originales", None)
    st.rerun()


def _validar_nan(edited: pd.DataFrame, titulo: str) -> None:
    filas_con_nan = edited[edited.isna().any(axis=1)]
    if not filas_con_nan.empty:
        _errores_guardado.append(f"**{titulo}**: {len(filas_con_nan)} fila(s) con campos vacíos.")


def _editar_catalogo(titulo: str, clave: str, columnas: dict, *,
                     disabled: bool = False,
                     nullable_cols: set[str] | None = None) -> None:
    st.subheader(titulo)
    df = pd.DataFrame(precios[clave])
    edited = st.data_editor(
        df,
        column_config=columnas,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{clave}",
        disabled=disabled,
    )
    if not disabled:
        _required_cols = [c for c in edited.columns if c not in (nullable_cols or set())]
        tiene_nan = edited[_required_cols].isna().any(axis=1).any()
        if tiene_nan:
            _validar_nan(edited[_required_cols], titulo)
        else:
            records = edited.to_dict("records")
            _INT_COLS = {"diametro_mm", "dn_min", "dn_max"}
            for row in records:
                # Normalizar NaN en columnas nullable a None (antes de cast int)
                for col in (nullable_cols or set()):
                    if col in row and pd.isna(row[col]):
                        row[col] = None
                # Cast columnas INTEGER del schema para evitar diffs espurios (100.0 vs 100)
                for col in _INT_COLS:
                    if col in row and row[col] is not None:
                        row[col] = int(row[col])
            precios[clave] = records


def _editar_dict(titulo: str, clave: str, col_key: str, col_val: str,
                 col_config: dict, *, num_rows: str = "dynamic",
                 disabled: bool = False) -> None:
    """Edita un catálogo almacenado como dict {clave: valor}."""
    st.subheader(titulo)
    df = pd.DataFrame(
        [{col_key: k, col_val: v} for k, v in precios[clave].items()]
    )
    edited = st.data_editor(
        df, column_config=col_config, num_rows=num_rows,
        use_container_width=True, key=f"editor_{clave}",
        disabled=disabled,
    )
    if not disabled:
        tiene_nan = edited.isna().any(axis=1).any()
        if tiene_nan:
            _validar_nan(edited, titulo)
            return
        filas_validas = [
            row for _, row in edited.iterrows()
            if str(row[col_key]).strip() != ""
        ]
        claves_vistas: set = set()
        claves_duplicadas: set = set()
        for row in filas_validas:
            k = row[col_key]
            if k in claves_vistas:
                claves_duplicadas.add(k)
            claves_vistas.add(k)
        if claves_duplicadas:
            _errores_guardado.append(
                f"**{titulo}**: claves duplicadas: {', '.join(str(k) for k in claves_duplicadas)}."
            )
        else:
            precios[clave] = {row[col_key]: row[col_val] for row in filas_validas}


# ─── Column configs reutilizables ────────────────────────────────────────

_cols_tuberia = {
    "label": st.column_config.TextColumn("Nombre", required=True),
    "tipo": st.column_config.TextColumn("Tipo", required=True),
    "diametro_mm": st.column_config.NumberColumn("Diámetro (mm)", min_value=1, required=True),
    "precio_m": st.column_config.NumberColumn("S.yMontaje (€/m)", min_value=0.0, format="%.2f", required=True,
                                              help="Precio de suministro y montaje (sin factor piezas ni CI)"),
    "factor_piezas": st.column_config.NumberColumn("Factor piezas", min_value=1.0, format="%.2f", required=True,
                                                   help="FD=1.20 · PE=1.20 · Gres=1.35 · PVC=1.20 · HA=1.00 · HA+PE80=1.40"),
    "precio_material_m": st.column_config.NumberColumn("Material (€/m)", min_value=0.0, format="%.2f", required=True,
                                                       help="Precio suministro puro del material (sin montaje). Solo ABA. GG/BI no aplican sobre este importe."),
}

_cols_ancho = {
    "diametro_mm": st.column_config.NumberColumn("Diámetro (mm)", min_value=1, required=True),
    "ancho_m": st.column_config.NumberColumn("Ancho (m)", min_value=0.1, format="%.2f", required=True),
}

_cols_arrinonado = {
    "diametro_mm": st.column_config.NumberColumn("Diámetro (mm)", min_value=1, required=True),
    "espesor_m": st.column_config.NumberColumn("Espesor (m)", min_value=0.01, format="%.2f", required=True),
}

_cols_entibacion = {
    "label": st.column_config.TextColumn("Tipo", required=True),
    "precio_m2": st.column_config.NumberColumn("Precio (€/m²)", min_value=0.0, format="%.2f", required=True),
    "umbral_m": st.column_config.NumberColumn("Umbral prof. (m)", min_value=0.0, format="%.2f", required=True),
    "red": st.column_config.SelectboxColumn("Red", options=["ABA", "SAN"], required=False,
                                            help="Dejar vacío para ambas redes"),
}

_cols_pozos = {
    "label": st.column_config.TextColumn("Tipo", required=True),
    "precio": st.column_config.NumberColumn("Precio (€/ud)", min_value=0.0, format="%.2f", required=True),
    "intervalo": st.column_config.NumberColumn("Intervalo (m)", min_value=1, required=True),
    "red": st.column_config.SelectboxColumn("Red", options=["ABA", "SAN"], required=False,
                                            help="Dejar vacío para ambas redes"),
    "profundidad_max": st.column_config.NumberColumn("Prof. máx (m)", min_value=0.0, format="%.1f",
                                                     help="Vacío = sin límite"),
    "dn_max": st.column_config.NumberColumn("DN máx (mm)", min_value=1,
                                            help="Vacío = sin límite"),
    "precio_tapa": st.column_config.NumberColumn("Tapa (€/ud)", min_value=0.0, format="%.2f",
                                                help="Precio tapa de pozo. Se añade como partida en OBRA CIVIL."),
    "precio_tapa_material": st.column_config.NumberColumn("Tapa material (€/ud)", min_value=0.0, format="%.2f",
                                                         help="Precio suministro tapa (sin montaje). Para sección MATERIALES."),
}

_cols_valvuleria = {
    "label": st.column_config.TextColumn("Nombre", required=True),
    "tipo": st.column_config.TextColumn("Tipo", required=True),
    "dn_min": st.column_config.NumberColumn("DN mín (mm)", min_value=1, required=True),
    "dn_max": st.column_config.NumberColumn("DN máx (mm)", min_value=1, required=True),
    "precio": st.column_config.NumberColumn("Montaje (€/ud)", min_value=0.0, format="%.2f", required=True,
                                           help="Precio de instalación/montaje (sin factor piezas ni CI)"),
    "intervalo_m": st.column_config.NumberColumn("Intervalo (m)", min_value=1, required=True),
    "factor_piezas": st.column_config.NumberColumn("Factor piezas", min_value=1.0, format="%.2f", required=True,
                                                   help="Multiplicador por piezas especiales. Default ABA=1.20"),
    "precio_material": st.column_config.NumberColumn("Material (€/ud)", min_value=0.0, format="%.2f", required=True,
                                                    help="Precio suministro puro del material. GG/BI no aplican sobre este importe."),
}

_cols_material = {
    "label": st.column_config.TextColumn("Nombre", required=True),
    "unidad": st.column_config.TextColumn("Unidad", required=True),
    "precio": st.column_config.NumberColumn("Precio base (€)", min_value=0.0, format="%.2f", required=True,
                                            help="Precio sin costes indirectos"),
    "factor_ci": st.column_config.NumberColumn("Factor CI", min_value=0.01, format="%.2f", required=True,
                                               help="Coste indirecto. Precio final = Precio base × Factor CI"),
}

_cols_acometida = {
    "tipo": st.column_config.TextColumn("Tipo", required=True),
    "precio": st.column_config.NumberColumn("Precio (€)", min_value=0.0, format="%.2f", required=True),
}


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 1: Financiero y generales
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("Financiero y generales — GG, BI, IVA, esponjamiento, % manual"):
    st.caption("Porcentajes aplicados globalmente a todos los presupuestos: "
               "gastos generales, beneficio industrial, IVA y factor de esponjamiento de tierras.")
    st.divider()

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        precios["pct_gg"] = round(st.number_input(
            "Gastos Generales (%)",
            value=precios["pct_gg"] * 100, step=0.5,
            disabled=_en_confirmacion) / 100, 6)
    with fc2:
        precios["pct_bi"] = round(st.number_input(
            "Beneficio Industrial (%)",
            value=precios["pct_bi"] * 100, step=0.5,
            disabled=_en_confirmacion) / 100, 6)
    with fc3:
        precios["pct_iva"] = round(st.number_input(
            "IVA (%)",
            value=precios["pct_iva"] * 100, step=0.5,
            disabled=_en_confirmacion) / 100, 6)

    pg1, pg2, pg3 = st.columns(3)
    with pg1:
        precios["factor_esponjamiento"] = round(st.number_input(
            "Factor esponjamiento (canon vertido)",
            value=float(precios.get("factor_esponjamiento", 1.30)),
            step=0.05, min_value=1.0, format="%.2f",
            disabled=_en_confirmacion), 4)
    with pg2:
        precios["pct_manual_defecto"] = round(st.number_input(
            "% Excavación manual por defecto",
            value=float(precios.get("pct_manual_defecto", 0.30)) * 100,
            step=5.0, min_value=0.0, max_value=100.0,
            disabled=_en_confirmacion) / 100, 4)
    with pg3:
        precios["pct_ci"] = round(st.number_input(
            "Factor CI (Costes Indirectos)",
            value=float(precios.get("pct_ci", 1.0)),
            step=0.01, min_value=1.0, max_value=1.20, format="%.2f",
            disabled=_en_confirmacion), 4)

    precios["conduccion_provisional_precio_m"] = round(st.number_input(
        "Precio conducción provisional PE (€/m)",
        value=float(precios.get("conduccion_provisional_precio_m", 12.0)),
        step=0.5, min_value=0.0, format="%.2f",
        disabled=_en_confirmacion), 2)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 2: Tuberías
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("Tuberías — Catálogos ABA, SAN y valvulería"):
    st.caption("Precios unitarios de tuberías de abastecimiento (FD, PE-100), "
               "saneamiento (Gres, HA, PVC) y valvulería asociada a la red de abastecimiento.")
    st.divider()

    _editar_catalogo("Tuberías Abastecimiento (ABA)", "catalogo_aba", _cols_tuberia, disabled=_en_confirmacion)
    _editar_catalogo("Tuberías Saneamiento (SAN)", "catalogo_san", _cols_tuberia, disabled=_en_confirmacion)
    _editar_catalogo("Valvulería ABA", "catalogo_valvuleria", _cols_valvuleria,
                     disabled=_en_confirmacion, nullable_cols={"instalacion"})


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 3: Zanja y excavación
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("Zanja y excavación — Entibación, precios y pozos"):
    st.caption("Entibación, precios unitarios de excavación, umbral de profundidad y pozos de registro.")
    st.info(
        "**Anchos de zanja y espesores de arriñonado** se calculan automáticamente por fórmula "
        "del Excel EMASESA (ABA: IF(DN<250, 0.60m, 1.2×DN/1000+0.40m) · SAN: 1.2×DN/1000+1.50m), "
        "garantizando que al añadir cualquier tubería nueva el cálculo sea siempre correcto. "
        "No es necesario editarlos manualmente."
    )
    st.divider()

    _editar_catalogo("Entibación", "catalogo_entibacion", _cols_entibacion,
                     disabled=_en_confirmacion, nullable_cols={"red"})

    # Leer umbral sin mutar el dict original; pasar copia filtrada al editor
    _umbral_exc = float(precios["excavacion"].get("umbral_profundidad_m", 2.5))
    _exc_sin_umbral = {k: v for k, v in precios["excavacion"].items() if k != "umbral_profundidad_m"}
    precios["excavacion"] = _exc_sin_umbral
    _editar_dict("Precios de excavación (€/m³)", "excavacion", "concepto", "precio", {
        "concepto": st.column_config.TextColumn("Concepto", disabled=True),
        "precio": st.column_config.NumberColumn("Precio (€)", min_value=0.0, format="%.2f", required=True),
    }, num_rows="fixed", disabled=_en_confirmacion)

    st.subheader("Umbral de profundidad")
    precios["excavacion"]["umbral_profundidad_m"] = round(st.number_input(
        "Umbral de profundidad para precio excavación (m)",
        value=_umbral_exc,
        step=0.1, min_value=0.5, format="%.1f",
        help="Por encima de este umbral se aplica el precio de excavación > X m",
        disabled=_en_confirmacion), 2)

    _editar_catalogo("Pozos de registro", "catalogo_pozos", _cols_pozos, disabled=_en_confirmacion,
                     nullable_cols={"red", "profundidad_max", "dn_max"})


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 4: Pavimentación
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("Demolición - Precios de derribo de pavimento existente"):
    st.caption("Precios unitarios de demolición del pavimento existente antes de abrir la zanja. "
               "Las cantidades se toman de las superficies/longitudes de pavimentación.")
    st.divider()

    _editar_catalogo("Demolición Abastecimiento", "demolicion_aba", _cols_material, disabled=_en_confirmacion)
    _editar_catalogo("Demolición Saneamiento", "demolicion_san", _cols_material, disabled=_en_confirmacion)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 4b: Pavimentación
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("Pavimentación - Acerados, bordillos, calzadas y espesores"):
    st.caption("Materiales y precios para reposición de pavimento tras la obra: "
               "acerados, bordillos, calzadas y espesores de capas de calzada.")
    st.divider()

    _editar_catalogo("Acerados Abastecimiento", "acerados_aba", _cols_material, disabled=_en_confirmacion)
    _editar_catalogo("Acerados Saneamiento", "acerados_san", _cols_material, disabled=_en_confirmacion)
    _editar_catalogo("Bordillos", "bordillos_reposicion", _cols_material, disabled=_en_confirmacion)
    _editar_catalogo("Calzadas", "calzadas_reposicion", _cols_material, disabled=_en_confirmacion)

    _editar_dict("Espesores de calzada (m)", "espesores_calzada", "material", "espesor_m", {
        "material": st.column_config.TextColumn("Material", required=True),
        "espesor_m": st.column_config.NumberColumn("Espesor (m)", min_value=0.01, format="%.2f", required=True),
    }, disabled=_en_confirmacion)

    _editar_catalogo("Sub-bases pavimentación", "catalogo_subbases", {
        "label": st.column_config.TextColumn("Material", required=True),
        "precio_m3": st.column_config.NumberColumn("Precio (€/m³)", min_value=0.0, format="%.2f", required=True),
    }, disabled=_en_confirmacion)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 5: Acometidas
# ═══════════════════════════════════════════════════════════════════════════════

def _editar_acometidas(red: str, clave_tipos: str, clave_defecto: str) -> None:
    """Renderiza editor de acometidas + selectbox de tipo por defecto para una red."""
    nombre = "Abastecimiento" if red == "ABA" else "Saneamiento"
    _editar_dict(f"Acometidas {nombre} (€/ud)", clave_tipos, "tipo", "precio",
                 _cols_acometida, disabled=_en_confirmacion)
    tipos = list(precios.get(clave_tipos, {}).keys())
    defecto = precios.get(clave_defecto, "")
    precios[clave_defecto] = st.selectbox(
        f"Tipo de acometida {red} por defecto",
        tipos,
        index=tipos.index(defecto) if defecto in tipos else 0,
        disabled=_en_confirmacion,
    ) if tipos else ""
    if not tipos:
        _errores_guardado.append(f"**Acometidas {red}**: el catálogo está vacío, no se puede definir tipo por defecto.")
    elif defecto and defecto not in tipos:
        st.warning(f"El tipo por defecto anterior '{defecto}' fue eliminado. "
                   "Se seleccionará el primero disponible.")


with st.expander("Desmontaje e Imbornales — Precios por tipo"):
    st.caption("Desmontaje de tuberías existentes ABA, imbornales SAN y precios de demolición/anulación de pozos existentes.")
    st.divider()

    _cols_desmontaje = {
        "label": st.column_config.TextColumn("Descripción", required=True),
        "dn_max": st.column_config.NumberColumn("DN máx (mm)", min_value=1, required=True),
        "precio_m": st.column_config.NumberColumn("Precio (€/m)", min_value=0.0, format="%.2f", required=True),
        "es_fibrocemento": st.column_config.CheckboxColumn("Fibrocemento"),
    }
    if precios.get("catalogo_desmontaje") is not None:
        _editar_catalogo("Desmontaje tubería ABA", "catalogo_desmontaje", _cols_desmontaje, disabled=_en_confirmacion)

    _cols_imbornales = {
        "label": st.column_config.TextColumn("Descripción", required=True),
        "precio": st.column_config.NumberColumn("Precio (€/ud)", min_value=0.0, format="%.2f", required=True),
        "tipo": st.column_config.SelectboxColumn("Tipo", options=["adaptacion", "nuevo"], required=True),
    }
    if precios.get("catalogo_imbornales") is not None:
        _editar_catalogo("Imbornales SAN", "catalogo_imbornales", _cols_imbornales, disabled=_en_confirmacion)

    _cols_pozex = {
        "red": st.column_config.SelectboxColumn("Red", options=["ABA", "SAN"], required=True),
        "accion": st.column_config.SelectboxColumn("Acción", options=["demolicion", "anulacion"], required=True),
        "precio": st.column_config.NumberColumn("Precio (€/ud)", min_value=0.0, format="%.2f", required=True),
        "intervalo_m": st.column_config.NumberColumn("Intervalo (m)", min_value=1, required=True),
    }
    if precios.get("catalogo_pozos_existentes") is not None:
        _editar_catalogo("Demolición/Anulación pozos existentes", "catalogo_pozos_existentes", _cols_pozex, disabled=_en_confirmacion)


with st.expander("Acometidas - Tipos y precios ABA/SAN"):
    st.caption("Tipos de acometida disponibles y sus precios unitarios, "
               "tanto para abastecimiento como para saneamiento.")
    st.divider()

    _editar_acometidas("ABA", "acometidas_aba_tipos", "acometida_aba_defecto")
    _editar_acometidas("SAN", "acometidas_san_tipos", "acometida_san_defecto")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDER 6: Valores por defecto
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("Valores por defecto - Mediciones e importes iniciales del formulario"):
    st.caption("Valores que aparecen pre-rellenados en la calculadora de presupuestos. "
               "Ajústalos a los valores típicos de tu zona de trabajo.")
    st.divider()

    _dui = precios["defaults_ui"]

    st.markdown("**Geometría de tramo**")
    d1, d2 = st.columns(2)
    with d1:
        _dui["aba_longitud_m"] = st.number_input(
            "Longitud ABA por defecto (m)", value=float(_dui["aba_longitud_m"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["san_longitud_m"] = st.number_input(
            "Longitud SAN por defecto (m)", value=float(_dui["san_longitud_m"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
    with d2:
        _dui["aba_profundidad_m"] = st.number_input(
            "Profundidad ABA por defecto (m)", value=float(_dui["aba_profundidad_m"]),
            min_value=0.0, step=0.1, format="%.2f", disabled=_en_confirmacion)
        _dui["san_profundidad_m"] = st.number_input(
            "Profundidad SAN por defecto (m)", value=float(_dui["san_profundidad_m"]),
            min_value=0.0, step=0.1, format="%.2f", disabled=_en_confirmacion)
    st.divider()

    st.markdown("**Superficies y acometidas**")
    d3, d4 = st.columns(2)
    with d3:
        _dui["pav_aba_acerado_m2"] = st.number_input(
            "Acerado ABA por defecto (m²)", value=float(_dui["pav_aba_acerado_m2"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["pav_san_calzada_m2"] = st.number_input(
            "Calzada SAN por defecto (m²)", value=float(_dui["pav_san_calzada_m2"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["acometidas_n"] = int(st.number_input(
            "Nº acometidas por defecto", value=int(_dui["acometidas_n"]),
            min_value=0, step=1, disabled=_en_confirmacion))
    with d4:
        _dui["pav_aba_bordillo_m"] = st.number_input(
            "Bordillo ABA por defecto (m)", value=float(_dui["pav_aba_bordillo_m"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
        _dui["pav_san_acera_m2"] = st.number_input(
            "Acera SAN por defecto (m²)", value=float(_dui["pav_san_acera_m2"]),
            min_value=0.0, step=10.0, disabled=_en_confirmacion)
    st.divider()

    st.markdown("**Porcentajes de obra**")
    d5, d6 = st.columns(2)
    with d5:
        _dui["pct_seguridad"] = round(st.number_input(
            "Seguridad y Salud por defecto (%)", value=float(_dui["pct_seguridad"]) * 100,
            min_value=0.0, max_value=20.0, step=0.5, format="%.1f",
            disabled=_en_confirmacion) / 100, 4)
    with d6:
        _dui["pct_gestion"] = round(st.number_input(
            "Gestión Ambiental por defecto (%)", value=float(_dui["pct_gestion"]) * 100,
            min_value=0.0, max_value=20.0, step=0.5, format="%.1f",
            disabled=_en_confirmacion) / 100, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# GUARDAR
# ═══════════════════════════════════════════════════════════════════════════════

st.divider()

if "confirmar_guardado" not in st.session_state:
    st.session_state["confirmar_guardado"] = False

_bloquear_guardado = bool(_errores_guardado)
if _errores_guardado:
    st.error("No se puede guardar: hay campos vacíos en los editores.\n\n"
             + "\n".join(f"- {e}" for e in _errores_guardado))

if not st.session_state["confirmar_guardado"]:
    if st.button("Guardar cambios", type="primary", use_container_width=True, disabled=_bloquear_guardado):
        st.session_state["confirmar_guardado"] = True
        st.session_state["precios_pendientes"] = copy.deepcopy(precios)
        st.rerun()
else:
    # Calcular diff entre snapshot original y los cambios pendientes
    try:
        _original = st.session_state["precios_originales"]
        _cambios = calcular_diff(_original, precios)
    except (ValueError, KeyError, OSError) as _diff_err:
        _cambios = None
        st.warning(f"No se pudo calcular el detalle de cambios: {_diff_err}")

    if _cambios is None:
        # Diff falló — permitir guardar sin revisión o volver
        st.info("Puedes guardar sin revisar los cambios o volver para corregir.")
        col_guardar, col_volver = st.columns(2)
        with col_guardar:
            if st.button("Guardar sin revisar", type="primary", use_container_width=True, disabled=_bloquear_guardado):
                try:
                    guardar_precios(precios)
                    cargar_precios.clear()
                    st.success("Precios guardados correctamente.")
                    _reset_confirmacion()
                except ValueError as e:
                    st.error(str(e))
        with col_volver:
            if st.button("Volver", use_container_width=True):
                _reset_confirmacion()
    elif len(_cambios) == 0:
        st.info("No hay cambios que guardar.")
        if st.button("Volver", use_container_width=True):
            _reset_confirmacion()
    else:
        with st.expander(f"Cambios pendientes ({len(_cambios)} modificaciones)", expanded=True):
            # Agrupar cambios por sección
            _secciones: dict[str, list] = {}
            for c in _cambios:
                _secciones.setdefault(c["seccion"], []).append(c)
            for sec_nombre, sec_cambios in _secciones.items():
                st.caption(f"{sec_nombre} — {len(sec_cambios)} cambio(s)")
                _df_cambios = pd.DataFrame([
                    {"Campo": c["campo"], "Anterior": c["valor_anterior"],
                     "Nuevo": c["valor_nuevo"]}
                    for c in sec_cambios
                ])
                st.dataframe(_df_cambios, use_container_width=True, hide_index=True)

        col_si, col_no = st.columns(2)
        with col_si:
            if st.button("Sí, guardar", type="primary", use_container_width=True, disabled=_bloquear_guardado):
                try:
                    guardar_precios(precios)
                    cargar_precios.clear()
                    st.success("Precios guardados correctamente.")
                    _reset_confirmacion()
                except ValueError as e:
                    st.error(str(e))
        with col_no:
            if st.button("Cancelar", use_container_width=True):
                _reset_confirmacion()
