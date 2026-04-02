"""Página de administración de precios EMASESA."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.precios import cargar_precios, guardar_precios


st.title("Administración de precios")
st.caption("Modifica los precios y pulsa 'Guardar cambios'. "
           "Los nuevos precios se aplicarán en los próximos cálculos.")

precios = cargar_precios()


# ─── Porcentajes financieros ──────────────────────────────────────────────

st.subheader("Porcentajes financieros")
fc1, fc2, fc3 = st.columns(3)
with fc1:
    precios["pct_gg"] = st.number_input("Gastos Generales (%)", value=precios["pct_gg"] * 100, step=0.5) / 100
with fc2:
    precios["pct_bi"] = st.number_input("Beneficio Industrial (%)", value=precios["pct_bi"] * 100, step=0.5) / 100
with fc3:
    precios["pct_iva"] = st.number_input("IVA (%)", value=precios["pct_iva"] * 100, step=0.5) / 100


# ─── Helper para editar catálogos tabulares ───────────────────────────────

def _editar_catalogo(titulo: str, clave: str, columnas: dict) -> None:
    st.subheader(titulo)
    df = pd.DataFrame(precios[clave])
    edited = st.data_editor(
        df,
        column_config=columnas,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{clave}",
    )
    precios[clave] = edited.to_dict("records")


# ─── Catálogos de tuberías ────────────────────────────────────────────────

_cols_tuberia = {
    "label": st.column_config.TextColumn("Nombre", required=True),
    "tipo": st.column_config.TextColumn("Tipo", required=True),
    "diametro_mm": st.column_config.NumberColumn("Diámetro (mm)", min_value=1, required=True),
    "precio_m": st.column_config.NumberColumn("Precio (€/m)", min_value=0.0, format="%.2f", required=True),
}

_editar_catalogo("Tuberías Abastecimiento (ABA)", "catalogo_aba", _cols_tuberia)
_editar_catalogo("Tuberías Saneamiento (SAN)", "catalogo_san", _cols_tuberia)


# ─── Acerados ─────────────────────────────────────────────────────────────

_cols_material = {
    "label": st.column_config.TextColumn("Nombre", required=True),
    "unidad": st.column_config.TextColumn("Unidad", required=True),
    "precio": st.column_config.NumberColumn("Precio (€)", min_value=0.0, format="%.2f", required=True),
}

_editar_catalogo("Acerados Abastecimiento", "acerados_aba", _cols_material)
_editar_catalogo("Acerados Saneamiento", "acerados_san", _cols_material)
_editar_catalogo("Bordillos", "bordillos_reposicion", _cols_material)
_editar_catalogo("Calzadas", "calzadas_reposicion", _cols_material)


# ─── Espesores de calzada ─────────────────────────────────────────────────

st.subheader("Espesores de calzada (m)")
df_esp = pd.DataFrame(
    [{"material": k, "espesor_m": v} for k, v in precios["espesores_calzada"].items()]
)
edited_esp = st.data_editor(
    df_esp,
    column_config={
        "material": st.column_config.TextColumn("Material", required=True),
        "espesor_m": st.column_config.NumberColumn("Espesor (m)", min_value=0.01, format="%.2f", required=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_espesores",
)
precios["espesores_calzada"] = {row["material"]: row["espesor_m"] for _, row in edited_esp.iterrows()}


# ─── Excavación ───────────────────────────────────────────────────────────

st.subheader("Precios de excavación (€/m³)")
df_exc = pd.DataFrame(
    [{"concepto": k, "precio": v} for k, v in precios["excavacion"].items()]
)
edited_exc = st.data_editor(
    df_exc,
    column_config={
        "concepto": st.column_config.TextColumn("Concepto", disabled=True),
        "precio": st.column_config.NumberColumn("Precio (€)", min_value=0.0, format="%.2f", required=True),
    },
    use_container_width=True,
    key="editor_excavacion",
)
precios["excavacion"] = {row["concepto"]: row["precio"] for _, row in edited_exc.iterrows()}


# ─── Acometidas ───────────────────────────────────────────────────────────

st.subheader("Acometidas Abastecimiento (€/ud)")
df_aco_aba = pd.DataFrame(
    [{"tipo": k, "precio": v} for k, v in precios["acometidas_aba_tipos"].items()]
)
edited_aco_aba = st.data_editor(
    df_aco_aba,
    column_config={
        "tipo": st.column_config.TextColumn("Tipo", required=True),
        "precio": st.column_config.NumberColumn("Precio (€)", min_value=0.0, format="%.2f", required=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_acometidas_aba",
)
precios["acometidas_aba_tipos"] = {row["tipo"]: row["precio"] for _, row in edited_aco_aba.iterrows()}

st.subheader("Acometidas Saneamiento (€/ud)")
df_aco_san = pd.DataFrame(
    [{"tipo": k, "precio": v} for k, v in precios["acometidas_san_tipos"].items()]
)
edited_aco_san = st.data_editor(
    df_aco_san,
    column_config={
        "tipo": st.column_config.TextColumn("Tipo", required=True),
        "precio": st.column_config.NumberColumn("Precio (€)", min_value=0.0, format="%.2f", required=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_acometidas_san",
)
precios["acometidas_san_tipos"] = {row["tipo"]: row["precio"] for _, row in edited_aco_san.iterrows()}


# ─── Guardar ──────────────────────────────────────────────────────────────

st.divider()
if st.button("Guardar cambios", type="primary", use_container_width=True):
    guardar_precios(precios)
    st.success("Precios guardados correctamente.")
