from datos import CATALOGO_ABA, CATALOGO_SAN, TIPOS_REURB
from calcular import calcular_presupuesto

DEFAULT_ABA   = 6     # índice catálogo ABA
DEFAULT_SAN   = 4     # índice catálogo SAN
DEFAULT_REURB = 0     # índice tipo reurbanización

st.set_page_config(page_title="LicitaIA")
st.title("LicitaIA")

resultado = calcular_presupuesto(
    metros_aba=100,
    precios_aba=CATALOGO_ABA[DEFAULT_ABA],
    metros_san=150,
    precios_san=CATALOGO_SAN[DEFAULT_SAN],
    reurbanizacion=TIPOS_REURB[DEFAULT_REURB],
)

st.subheader("Resultado del cálculo")
for clave, valor in resultado.items():
    st.write(f"**{clave}**: {valor:,.2f} €")
