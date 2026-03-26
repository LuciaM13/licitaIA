from __future__ import annotations
import os, sys
from typing import Dict, List
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from calcular import ParametrosProyecto, calcular_presupuesto
import datos as d

st.set_page_config(page_title="Cálculo de presupuestos", layout="wide")


def euro(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_por_label(catalogo: List[Dict], label: str) -> Dict:
    for item in catalogo:
        if item["label"] == label:
            return item
    return catalogo[0]


def opciones_por_familia(catalogo: List[Dict], familia: str) -> List[Dict]:
    return [x for x in catalogo if x.get("familia") == familia]

st.markdown("""
<style>
.main-card {background: linear-gradient(135deg,#153a5b 0%,#1f5f8b 100%); color:white; padding:22px; border-radius:14px; margin-bottom:18px;}
.soft-box {background:#f6f9fc; border:1px solid #dbe7f3; color:#000; padding:14px 16px; border-radius:12px; margin-bottom:12px;}
.note-box {background:#eef6ff; border-left:6px solid #1f5f8b; color:#000; padding:14px 16px; border-radius:10px; margin:10px 0 16px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-card">
<h2 style="margin-bottom:0.35rem;">Cálculo de presupuestos</h2>
<div style="font-size:1.03rem;">Versión estricta: solo usa partidas y precios que aparecen en el Excel y la estructura final del pliego para GG, BI, IVA, Seguridad y Salud y Gestión Ambiental. No calcula geometrías ni cantidades auxiliares: introduces directamente la cantidad en la unidad de cada partida.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="note-box">
<b>Cómo usar la página:</b><br>
1. Introduce solo las cantidades que ya tengas medidas en m, m², m³ o ud.<br>
2. En saneamiento, primero elige la familia y luego el diámetro para no mezclar opciones.<br>
3. El resultado sale ya desglosado por capítulos 01–08 y con un bloque listo para copiar a Word.
</div>
""", unsafe_allow_html=True)

# 1 Saneamiento
st.markdown("## 1) Obra civil saneamiento")
st.markdown('<div class="soft-box">Solo aparecen tuberías y elementos que sí tienen precio en el Excel.</div>', unsafe_allow_html=True)
familias_san = sorted({x['familia'] for x in d.CATALOGO_SAN})
col1, col2, col3 = st.columns(3)
with col1:
    familia_san = st.selectbox("Familia SAN", familias_san, help="Primero elige la familia del material de saneamiento.")
    opciones_san = opciones_por_familia(d.CATALOGO_SAN, familia_san)
    tipo_san = st.selectbox("Tipo SAN", [x['label'] for x in opciones_san], help="Ahora solo se muestran las opciones de esa familia.")
    qty_tuberia_san = st.number_input("Cantidad tubería SAN (m)", min_value=0.0, value=0.0)
with col2:
    usar_ovoide = st.checkbox("Añadir ovoide", value=False)
    tipo_ovoide = st.selectbox("Tipo ovoide", [x['label'] for x in d.CATALOGO_OVOIDE], disabled=not usar_ovoide)
    qty_ovoide = st.number_input("Cantidad ovoide (m)", min_value=0.0, value=0.0, disabled=not usar_ovoide)
with col3:
    tipo_pozo = st.selectbox("Tipo de pozo", [x['label'] for x in d.POZOS])
    qty_pozos = st.number_input("Nº pozos", min_value=0, value=0)
    tipo_imbornal = st.selectbox("Tipo de imbornal", [x['label'] for x in d.IMBORNALES])
    qty_imbornales = st.number_input("Nº imbornales", min_value=0, value=0)
    tipo_marco = st.selectbox("Tipo de marco", [x['label'] for x in d.MARCOS])
    qty_marcos = st.number_input("Nº marcos", min_value=0, value=0)
    qty_tapas_pozo = st.number_input("Nº tapas de pozo", min_value=0, value=0)
    qty_pates_pozo = st.number_input("Nº pates de pozo", min_value=0, value=0)

st.markdown("## 2) Movimiento de tierras")
st.markdown('<div class="soft-box">Introduce directamente los m³ o m² medidos para cada capítulo. No hay anchos, profundidades ni espesores calculados por la app.</div>', unsafe_allow_html=True)
aba_mt, san_mt = st.columns(2)
with aba_mt:
    st.markdown("### Capítulo 01 · ABASTECIMIENTO")
    qty_exc_mecanica_aba = st.number_input("Excavación mecánica ABA (m³)", min_value=0.0, value=0.0)
    tipo_exc_mec_aba = st.selectbox("Profundidad exc. mecánica ABA", ["<2,5m", ">2,5m"], key="t1")
    qty_exc_manual_aba = st.number_input("Excavación manual ABA (m³)", min_value=0.0, value=0.0)
    tipo_exc_man_aba = st.selectbox("Profundidad exc. manual ABA", ["<2,5m", ">2,5m"], key="t2")
    qty_entibacion_aba = st.number_input("Entibación ABA (m²)", min_value=0.0, value=0.0)
    tipo_ent_aba = st.selectbox("Tipo entibación ABA", ["<2,5m", ">2,5m"], key="t3")
    qty_carga_tierras_aba = st.number_input("Carga de tierras ABA (m³)", min_value=0.0, value=0.0)
    qty_transporte_tierras_aba = st.number_input("Transporte a vertedero ABA (m³)", min_value=0.0, value=0.0)
    qty_canon_tierras_aba = st.number_input("Canon vertido tierras ABA (m³)", min_value=0.0, value=0.0)
    qty_arena_aba = st.number_input("Arena ABA (m³)", min_value=0.0, value=0.0)
    qty_relleno_aba = st.number_input("Relleno albero ABA (m³)", min_value=0.0, value=0.0)
with san_mt:
    st.markdown("### Capítulo 02 · SANEAMIENTO")
    qty_exc_mecanica_san = st.number_input("Excavación mecánica SAN (m³)", min_value=0.0, value=0.0)
    tipo_exc_mec_san = st.selectbox("Profundidad exc. mecánica SAN", ["<2,5m", ">2,5m"], key="t4")
    qty_exc_manual_san = st.number_input("Excavación manual SAN (m³)", min_value=0.0, value=0.0)
    tipo_exc_man_san = st.selectbox("Profundidad exc. manual SAN", ["<2,5m", ">2,5m"], key="t5")
    qty_entibacion_san = st.number_input("Entibación SAN (m²)", min_value=0.0, value=0.0)
    tipo_ent_san = st.selectbox("Tipo entibación SAN", ["<2,5m", ">2,5m"], key="t6")
    qty_carga_tierras_san = st.number_input("Carga de tierras SAN (m³)", min_value=0.0, value=0.0)
    qty_transporte_tierras_san = st.number_input("Transporte a vertedero SAN (m³)", min_value=0.0, value=0.0)
    qty_canon_tierras_san = st.number_input("Canon vertido tierras SAN (m³)", min_value=0.0, value=0.0)
    qty_arena_san = st.number_input("Arena SAN (m³)", min_value=0.0, value=0.0)
    qty_relleno_san = st.number_input("Relleno albero SAN (m³)", min_value=0.0, value=0.0)

st.markdown("## 3) Pavimentación")
def bloque_pav(nombre: str, keypref: str):
    st.markdown(f"### {nombre}")
    c1,c2 = st.columns(2)
    with c1:
        tipo_dem_bordillo = st.selectbox(f"Tipo bordillo demolido {keypref}", [x['label'] for x in d.DEMOLICION_BORDILLO], key=f"db_{keypref}")
        qty_dem_bordillo = st.number_input(f"Demolición bordillo {keypref} (m)", min_value=0.0, value=0.0, key=f"qdb_{keypref}")
        tipo_dem_acerado = st.selectbox(f"Tipo acerado demolido {keypref}", [x['label'] for x in d.DEMOLICION_ACERADO], key=f"da_{keypref}")
        qty_dem_acerado = st.number_input(f"Demolición acerado {keypref} (m²)", min_value=0.0, value=0.0, key=f"qda_{keypref}")
        tipo_dem_calzada = st.selectbox(f"Tipo calzada demolida {keypref}", [x['label'] for x in d.DEMOLICION_CALZADA], key=f"dc_{keypref}")
        qty_dem_calzada = st.number_input(f"Demolición calzada {keypref} (m²)", min_value=0.0, value=0.0, key=f"qdc_{keypref}")
        qty_canon_mixto = st.number_input(f"Canon vertido mixto {keypref} (m³)", min_value=0.0, value=0.0, key=f"qcm_{keypref}")
    with c2:
        tipo_rep_acerado = st.selectbox(f"Tipo acerado a reponer {keypref}", [x['label'] for x in d.ACERADOS_REPOSICION], key=f"ra_{keypref}")
        qty_rep_acerado = st.number_input(f"Reposición acerado {keypref} (m²)", min_value=0.0, value=0.0, key=f"qra_{keypref}")
        tipo_rep_bordillo = st.selectbox(f"Tipo bordillo a reponer {keypref}", [x['label'] for x in d.BORDILLOS_REPOSICION], key=f"rb_{keypref}")
        qty_rep_bordillo = st.number_input(f"Reposición bordillo {keypref} (m)", min_value=0.0, value=0.0, key=f"qrb_{keypref}")
        qty_rep_adoquin = st.number_input(f"Reposición adoquín {keypref} (m²)", min_value=0.0, value=0.0, key=f"qado_{keypref}")
        qty_rep_rodadura = st.number_input(f"Capa de rodadura {keypref} (m³)", min_value=0.0, value=0.0, key=f"qrod_{keypref}")
        qty_rep_base_pav = st.number_input(f"Base de pavimento {keypref} (m³)", min_value=0.0, value=0.0, key=f"qbp_{keypref}")
        qty_rep_hormigon = st.number_input(f"Hormigón {keypref} (m³)", min_value=0.0, value=0.0, key=f"qhor_{keypref}")
        qty_rep_base_granular = st.number_input(f"Base granular {keypref} (m³)", min_value=0.0, value=0.0, key=f"qbg_{keypref}")
    return {
        'tipo_dem_bordillo': tipo_dem_bordillo, 'qty_dem_bordillo': qty_dem_bordillo,
        'tipo_dem_acerado': tipo_dem_acerado, 'qty_dem_acerado': qty_dem_acerado,
        'tipo_dem_calzada': tipo_dem_calzada, 'qty_dem_calzada': qty_dem_calzada,
        'qty_canon_mixto': qty_canon_mixto,
        'tipo_rep_acerado': tipo_rep_acerado, 'qty_rep_acerado': qty_rep_acerado,
        'tipo_rep_bordillo': tipo_rep_bordillo, 'qty_rep_bordillo': qty_rep_bordillo,
        'qty_rep_adoquin': qty_rep_adoquin, 'qty_rep_rodadura': qty_rep_rodadura,
        'qty_rep_base_pav': qty_rep_base_pav, 'qty_rep_hormigon': qty_rep_hormigon,
        'qty_rep_base_granular': qty_rep_base_granular,
    }
aba_pav = bloque_pav("Capítulo 03 · PAVIMENTACIÓN ABASTECIMIENTO", "aba")
san_pav = bloque_pav("Capítulo 04 · PAVIMENTACIÓN SANEAMIENTO", "san")
q_dem_arqueta = st.number_input("Demolición arqueta de imbornal SAN (ud)", min_value=0, value=0)
q_dem_imbornal_tub = st.number_input("Demolición imbornal y tubería SAN (ud)", min_value=0, value=0)

st.markdown("## 4) Acometidas")
ac1, ac2 = st.columns(2)
with ac1:
    fam_aco_aba = st.selectbox("Familia acometida ABA", sorted({x['familia'] for x in d.ACOMETIDAS}), key='faba')
    op_aba = opciones_por_familia(d.ACOMETIDAS, fam_aco_aba)
    tipo_aco_aba = st.selectbox("Tipo acometida ABA", [x['label'] for x in op_aba])
    qty_aco_aba = st.number_input("Nº acometidas ABA", min_value=0, value=0)
with ac2:
    fam_aco_san = st.selectbox("Familia acometida SAN", sorted({x['familia'] for x in d.ACOMETIDAS}), key='fsan')
    op_san = opciones_por_familia(d.ACOMETIDAS, fam_aco_san)
    tipo_aco_san = st.selectbox("Tipo acometida SAN", [x['label'] for x in op_san])
    qty_aco_san = st.number_input("Nº acometidas SAN", min_value=0, value=0)

st.markdown("## 5) Estructura final")
nivel_servicios = st.selectbox("Servicios afectados", [x['label'] for x in d.SERVICIOS_AFECTADOS])
st.markdown(f"Seguridad y Salud (PPTP): **{euro(d.IMPORTE_SS_PPTP)}**")
st.markdown(f"Gestión Ambiental (PPTP): **{euro(d.IMPORTE_GA_PPTP)}**")

if st.button("Calcular presupuesto", type="primary", use_container_width=True):
    p = ParametrosProyecto(
        qty_exc_mecanica_aba=qty_exc_mecanica_aba,
        precio_exc_mecanica_aba=d.EXCAVACION['mecanica_hasta_2_5_m3'] if tipo_exc_mec_aba == '<2,5m' else d.EXCAVACION['mecanica_mas_2_5_m3'],
        qty_exc_manual_aba=qty_exc_manual_aba,
        precio_exc_manual_aba=d.EXCAVACION['manual_hasta_2_5_m3'] if tipo_exc_man_aba == '<2,5m' else d.EXCAVACION['manual_mas_2_5_m3'],
        qty_entibacion_aba=qty_entibacion_aba,
        precio_entibacion_aba=d.EXCAVACION['entibacion_blindada_hasta_2_5_m2'] if tipo_ent_aba == '<2,5m' else d.EXCAVACION['entibacion_blindada_mas_2_5_m2'],
        qty_carga_tierras_aba=qty_carga_tierras_aba, precio_carga_tierras_aba=d.EXCAVACION['carga_tierras_m3'],
        qty_transporte_tierras_aba=qty_transporte_tierras_aba, precio_transporte_tierras_aba=d.EXCAVACION['transporte_vertedero_m3'],
        qty_canon_tierras_aba=qty_canon_tierras_aba, precio_canon_tierras_aba=d.EXCAVACION['canon_vertedero_tierras_m3'],
        qty_arena_aba=qty_arena_aba, precio_arena_aba=d.EXCAVACION['arena_m3'],
        qty_relleno_aba=qty_relleno_aba, precio_relleno_aba=d.EXCAVACION['relleno_albero_m3'],
        qty_tuberia_san=qty_tuberia_san, precio_tuberia_san=buscar_por_label(d.CATALOGO_SAN, tipo_san)['tuberia_m'],
        qty_ovoide=qty_ovoide, precio_ovoide=buscar_por_label(d.CATALOGO_OVOIDE, tipo_ovoide)['tuberia_m'],
        qty_exc_mecanica_san=qty_exc_mecanica_san,
        precio_exc_mecanica_san=d.EXCAVACION['mecanica_hasta_2_5_m3'] if tipo_exc_mec_san == '<2,5m' else d.EXCAVACION['mecanica_mas_2_5_m3'],
        qty_exc_manual_san=qty_exc_manual_san,
        precio_exc_manual_san=d.EXCAVACION['manual_hasta_2_5_m3'] if tipo_exc_man_san == '<2,5m' else d.EXCAVACION['manual_mas_2_5_m3'],
        qty_entibacion_san=qty_entibacion_san,
        precio_entibacion_san=d.EXCAVACION['entibacion_blindada_hasta_2_5_m2'] if tipo_ent_san == '<2,5m' else d.EXCAVACION['entibacion_blindada_mas_2_5_m2'],
        qty_carga_tierras_san=qty_carga_tierras_san, precio_carga_tierras_san=d.EXCAVACION['carga_tierras_m3'],
        qty_transporte_tierras_san=qty_transporte_tierras_san, precio_transporte_tierras_san=d.EXCAVACION['transporte_vertedero_m3'],
        qty_canon_tierras_san=qty_canon_tierras_san, precio_canon_tierras_san=d.EXCAVACION['canon_vertedero_tierras_m3'],
        qty_arena_san=qty_arena_san, precio_arena_san=d.EXCAVACION['arena_m3'],
        qty_relleno_san=qty_relleno_san, precio_relleno_san=d.EXCAVACION['relleno_albero_m3'],
        qty_pozos=qty_pozos, precio_pozo=buscar_por_label(d.POZOS, tipo_pozo)['precio_ud'],
        qty_imbornales=qty_imbornales, precio_imbornal=buscar_por_label(d.IMBORNALES, tipo_imbornal)['precio_ud'],
        qty_marcos=qty_marcos, precio_marco=buscar_por_label(d.MARCOS, tipo_marco)['precio_ud'],
        qty_tapas_pozo=qty_tapas_pozo, precio_tapa_pozo=d.MATERIALES_POZO_TAPA[0]['precio_ud'],
        qty_pates_pozo=qty_pates_pozo, precio_pate_pozo=d.MATERIALES_POZO_PATE[0]['precio_ud'],
        qty_dem_bordillo_aba=aba_pav['qty_dem_bordillo'], precio_dem_bordillo_aba=buscar_por_label(d.DEMOLICION_BORDILLO, aba_pav['tipo_dem_bordillo'])['precio_m'],
        qty_dem_acerado_aba=aba_pav['qty_dem_acerado'], precio_dem_acerado_aba=buscar_por_label(d.DEMOLICION_ACERADO, aba_pav['tipo_dem_acerado'])['precio_m2'],
        qty_dem_calzada_aba=aba_pav['qty_dem_calzada'], precio_dem_calzada_aba=buscar_por_label(d.DEMOLICION_CALZADA, aba_pav['tipo_dem_calzada'])['precio_m2'],
        qty_canon_mixto_aba=aba_pav['qty_canon_mixto'], precio_canon_mixto_aba=d.EXCAVACION['canon_vertedero_mixto_m3'],
        qty_rep_acerado_aba=aba_pav['qty_rep_acerado'], precio_rep_acerado_aba=buscar_por_label(d.ACERADOS_REPOSICION, aba_pav['tipo_rep_acerado'])['precio_m2'],
        qty_rep_bordillo_aba=aba_pav['qty_rep_bordillo'], precio_rep_bordillo_aba=buscar_por_label(d.BORDILLOS_REPOSICION, aba_pav['tipo_rep_bordillo'])['precio_m'],
        qty_rep_adoquin_aba=aba_pav['qty_rep_adoquin'], precio_rep_adoquin_aba=d.REPOSICION_CALZADA['adoquin_m2'],
        qty_rep_rodadura_aba=aba_pav['qty_rep_rodadura'], precio_rep_rodadura_aba=d.REPOSICION_CALZADA['rodadura_m3'],
        qty_rep_base_pavimento_aba=aba_pav['qty_rep_base_pav'], precio_rep_base_pavimento_aba=d.REPOSICION_CALZADA['base_pavimento_m3'],
        qty_rep_hormigon_aba=aba_pav['qty_rep_hormigon'], precio_rep_hormigon_aba=d.REPOSICION_CALZADA['hormigon_m3'],
        qty_rep_base_granular_aba=aba_pav['qty_rep_base_granular'], precio_rep_base_granular_aba=d.REPOSICION_CALZADA['base_granular_m3'],
        qty_dem_bordillo_san=san_pav['qty_dem_bordillo'], precio_dem_bordillo_san=buscar_por_label(d.DEMOLICION_BORDILLO, san_pav['tipo_dem_bordillo'])['precio_m'],
        qty_dem_acerado_san=san_pav['qty_dem_acerado'], precio_dem_acerado_san=buscar_por_label(d.DEMOLICION_ACERADO, san_pav['tipo_dem_acerado'])['precio_m2'],
        qty_dem_calzada_san=san_pav['qty_dem_calzada'], precio_dem_calzada_san=buscar_por_label(d.DEMOLICION_CALZADA, san_pav['tipo_dem_calzada'])['precio_m2'],
        qty_dem_arqueta_imbornal=q_dem_arqueta, precio_dem_arqueta_imbornal=d.REPOSICION_CALZADA['demolicion_arqueta_imbornal_ud'],
        qty_dem_imbornal_tuberia=q_dem_imbornal_tub, precio_dem_imbornal_tuberia=d.REPOSICION_CALZADA['demolicion_imbornal_tuberia_ud'],
        qty_canon_mixto_san=san_pav['qty_canon_mixto'], precio_canon_mixto_san=d.EXCAVACION['canon_vertedero_mixto_m3'],
        qty_rep_acerado_san=san_pav['qty_rep_acerado'], precio_rep_acerado_san=buscar_por_label(d.ACERADOS_REPOSICION, san_pav['tipo_rep_acerado'])['precio_m2'],
        qty_rep_bordillo_san=san_pav['qty_rep_bordillo'], precio_rep_bordillo_san=buscar_por_label(d.BORDILLOS_REPOSICION, san_pav['tipo_rep_bordillo'])['precio_m'],
        qty_rep_adoquin_san=san_pav['qty_rep_adoquin'], precio_rep_adoquin_san=d.REPOSICION_CALZADA['adoquin_m2'],
        qty_rep_rodadura_san=san_pav['qty_rep_rodadura'], precio_rep_rodadura_san=d.REPOSICION_CALZADA['rodadura_m3'],
        qty_rep_base_pavimento_san=san_pav['qty_rep_base_pav'], precio_rep_base_pavimento_san=d.REPOSICION_CALZADA['base_pavimento_m3'],
        qty_rep_hormigon_san=san_pav['qty_rep_hormigon'], precio_rep_hormigon_san=d.REPOSICION_CALZADA['hormigon_m3'],
        qty_rep_base_granular_san=san_pav['qty_rep_base_granular'], precio_rep_base_granular_san=d.REPOSICION_CALZADA['base_granular_m3'],
        qty_acometidas_aba=qty_aco_aba, precio_acometidas_aba=buscar_por_label(d.ACOMETIDAS, tipo_aco_aba)['precio_ud'],
        qty_acometidas_san=qty_aco_san, precio_acometidas_san=buscar_por_label(d.ACOMETIDAS, tipo_aco_san)['precio_ud'],
        pct_servicios_afectados=buscar_por_label(d.SERVICIOS_AFECTADOS, nivel_servicios)['pct'],
        importe_ss=d.IMPORTE_SS_PPTP,
        importe_ga=d.IMPORTE_GA_PPTP,
    )
    r = calcular_presupuesto(p)
    st.markdown('## 6) Resultado económico')
    m1,m2,m3,m4 = st.columns(4)
    m1.metric('PEM', euro(r['pem']))
    m2.metric('PBL sin IVA', euro(r['pbl_sin_iva']))
    m3.metric('IVA', euro(r['iva']))
    m4.metric('Total', euro(r['total']))
    caps = [
        ('01 OBRA CIVIL ABASTECIMIENTO', r['capitulo_01']),
        ('02 OBRA CIVIL SANEAMIENTO', r['capitulo_02']),
        ('03 PAVIMENTACIÓN ABASTECIMIENTO', r['capitulo_03']),
        ('04 PAVIMENTACIÓN SANEAMIENTO', r['capitulo_04']),
        ('05 ACOMETIDAS ABASTECIMIENTO', r['capitulo_05']),
        ('06 ACOMETIDAS SANEAMIENTO', r['capitulo_06']),
        ('07 SEGURIDAD Y SALUD', r['capitulo_07']),
        ('08 GESTIÓN AMBIENTAL', r['capitulo_08']),
    ]
    st.dataframe(pd.DataFrame([{'Capítulo':c, 'Subtotal':euro(v)} for c,v in caps]), use_container_width=True, hide_index=True)
    resumen = [
        ('Presupuesto de Ejecución Material', r['pem']),
        ('13 % Gastos Generales', r['gastos_generales']),
        ('6 % Beneficio Industrial', r['beneficio_industrial']),
        ('Presupuesto Base de Licitación excluido IVA', r['pbl_sin_iva']),
        ('21 % IVA', r['iva']),
        ('Presupuesto Base de Licitación incluido IVA', r['total']),
    ]
    st.dataframe(pd.DataFrame([{'Concepto':c, 'Importe':euro(v)} for c,v in resumen]), use_container_width=True, hide_index=True)
    st.text_area('Texto listo para copiar a Word', value=r['texto_word'].replace(',', 'X').replace('.', ',').replace('X', '.'), height=260)
else:
    st.info('Introduce las cantidades y pulsa “Calcular presupuesto”.')
