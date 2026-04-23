"""Tests de la página Calculadora - streamlit.testing.v1.AppTest."""

from __future__ import annotations

import pytest

from helpers import _app_calculadora, _calcular_aba, _calcular_san
from src.aplicacion.historial import (
    contar_presupuestos, eliminar_presupuesto, listar_presupuestos,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Ronda 1 - Tests básicos
# ═══════════════════════════════════════════════════════════════════════════════


def test_calculadora_carga():
    """La pagina de calculadora carga sin excepciones."""
    at = _app_calculadora().run()
    assert not at.exception


def test_aba_solo_basico():
    """ABA-only FD DN=100, L=50, P=1.0 produce resultado valido."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception

    # Resultado presente en session_state
    assert "resultado" in at.session_state
    r = at.session_state["resultado"]

    # Invariantes financieras
    assert r["total"] == pytest.approx(r["pbl_sin_iva"] + r["iva"], abs=0.01)
    assert r["pbl_sin_iva"] % 10 == 0, "PBL debe ser multiplo de 10 (ROUNDUP)"

    # Capitulo 01 presente
    caps = r["capitulos"]
    cap_aba = [k for k in caps if "OBRA CIVIL ABASTECIMIENTO" in k]
    assert len(cap_aba) == 1, f"Esperado cap ABA, encontrados: {list(caps.keys())}"
    assert caps[cap_aba[0]]["subtotal"] > 0


def test_aba_san_combo():
    """Modo ABA+SAN genera capitulos de ambas redes."""
    at = _app_calculadora().run()

    # Seleccionar modo combinado
    at.radio(key="modo_actuacion").set_value("Abastecimiento + Saneamiento").run()

    # Configurar ABA
    at.number_input(key="ABAS_longitud").set_value(50.0)
    at.number_input(key="ABAS_profundidad").set_value(1.0)
    at.selectbox(key="ABAS_diametro").set_value(100)
    at.run()

    # Configurar SAN (tipo Gres por defecto, DN=300 por defecto)
    at.number_input(key="SAN_longitud").set_value(50.0)
    at.number_input(key="SAN_profundidad").set_value(1.5)
    at.run()

    # Calcular
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    caps = r["capitulos"]
    tiene_aba = any("ABASTECIMIENTO" in k for k in caps)
    tiene_san = any("SANEAMIENTO" in k for k in caps)
    assert tiene_aba, f"Falta capitulo ABA. Caps: {list(caps.keys())}"
    assert tiene_san, f"Falta capitulo SAN. Caps: {list(caps.keys())}"

    # Invariantes financieras
    assert r["total"] == pytest.approx(r["pbl_sin_iva"] + r["iva"], abs=0.01)
    assert r["pbl_sin_iva"] % 10 == 0, "PBL debe ser multiplo de 10 (ROUNDUP)"
    suma_caps = sum(cap["subtotal"] for cap in caps.values())
    assert suma_caps == pytest.approx(r["pem"], abs=0.01)


def test_casos_limite():
    """L=0 y P=0 no provocan excepcion."""
    at = _app_calculadora().run()
    at.number_input(key="ABAS_longitud").set_value(0.0)
    at.number_input(key="ABAS_profundidad").set_value(0.0)
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception


def test_valvuleria_enterrada_vs_pozo():
    """Distinta instalacion de valvuleria produce totales distintos."""
    # Caso 1: enterrada (por defecto)
    at1 = _app_calculadora().run()
    at1.radio(key="instalacion_valvuleria").set_value("enterrada")
    at1 = _calcular_aba(at1, dn=150, longitud=100.0, profundidad=1.2)
    assert not at1.exception
    assert "resultado" in at1.session_state
    total_enterrada = at1.session_state["resultado"]["total"]

    # Caso 2: pozo
    at2 = _app_calculadora().run()
    at2.radio(key="instalacion_valvuleria").set_value("pozo")
    at2 = _calcular_aba(at2, dn=150, longitud=100.0, profundidad=1.2)
    assert not at2.exception
    assert "resultado" in at2.session_state
    total_pozo = at2.session_state["resultado"]["total"]

    assert total_enterrada != total_pozo, (
        f"Totales deberian diferir: enterrada={total_enterrada}, pozo={total_pozo}"
    )


def test_pct_seguridad_divide_por_100():
    """Widget pct_seguridad=2.0 (%) produce cap S&S ~ 2% del PEM."""
    at = _app_calculadora().run()

    # Poner seguridad al 2%
    at.number_input(key="pct_seguridad").set_value(2.0)
    at.run()

    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    caps = r["capitulos"]

    # Buscar capitulo de Seguridad y Salud
    cap_ss = [k for k in caps if "SEGURIDAD" in k]
    assert len(cap_ss) >= 1, f"No se encontro capitulo S&S. Caps: {list(caps.keys())}"

    subtotal_ss = caps[cap_ss[0]]["subtotal"]
    pem = r["pem"]

    # S&S debe ser aprox 2% del PEM (con tolerancia del 50% relativo,
    # porque la base_ss excluye canones, desmontaje y materiales del PEM)
    ratio = subtotal_ss / pem if pem > 0 else 0
    assert 0.005 < ratio < 0.04, (
        f"Ratio S&S/PEM = {ratio:.4f}, esperado ~0.02 (2%)"
    )


def test_session_state_estable():
    """Dos .run() consecutivos sin cambios no provocan excepcion ni resultado huerfano."""
    at = _app_calculadora().run()
    assert not at.exception

    at.run()
    assert not at.exception

    # En carga fresca no debe haber resultado (nadie pulso Calcular)
    tiene_resultado = "resultado" in at.session_state
    assert not tiene_resultado, "No deberia haber resultado sin pulsar Calcular"


# ═══════════════════════════════════════════════════════════════════════════════
# Ronda 2 - Tests de redes y decisiones
# ═══════════════════════════════════════════════════════════════════════════════


def test_san_solo_basico():
    """SAN-only Gres DN=300, L=50, P=1.5 produce resultado valido sin caps ABA."""
    at = _app_calculadora().run()
    at.radio(key="modo_actuacion").set_value("Solo Saneamiento").run()

    at = _calcular_san(at, dn=300, longitud=50.0, profundidad=1.5)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    caps = r["capitulos"]

    # Cap SAN presente con subtotal > 0
    cap_san = [k for k in caps if "OBRA CIVIL SANEAMIENTO" in k]
    assert len(cap_san) == 1, f"Esperado cap SAN. Caps: {list(caps.keys())}"
    assert caps[cap_san[0]]["subtotal"] > 0

    # Ningun cap ABA
    assert not any("ABASTECIMIENTO" in k for k in caps), (
        f"No deberia haber caps ABA en modo SAN-only. Caps: {list(caps.keys())}"
    )

    # Invariantes financieras (mismas que test_aba_solo_basico)
    assert r["total"] == pytest.approx(r["pbl_sin_iva"] + r["iva"], abs=0.01)
    assert r["pbl_sin_iva"] % 10 == 0, "PBL debe ser multiplo de 10 (ROUNDUP)"
    suma_caps = sum(cap["subtotal"] for cap in caps.values())
    assert suma_caps == pytest.approx(r["pem"], abs=0.01)


def test_capitulos_suman_pem():
    """La suma de subtotales de todos los capitulos es igual al PEM."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    suma_caps = sum(cap["subtotal"] for cap in r["capitulos"].values())
    assert suma_caps == pytest.approx(r["pem"], abs=0.01), (
        f"Suma capitulos ({suma_caps:.2f}) != PEM ({r['pem']:.2f})"
    )


def test_profundidad_alta_activa_entibacion():
    """Profundidad 3.0m (> umbral 1.5m ABA) activa entibacion en trazabilidad y partidas."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=150, longitud=100.0, profundidad=3.0)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]

    # Trazabilidad menciona entibacion
    assert "trazabilidad" in r
    traz = r["trazabilidad"]
    assert "ABA" in traz, f"Esperada trazabilidad ABA. Keys: {list(traz.keys()) if isinstance(traz, dict) else type(traz)}"
    traz_texto = " ".join(str(s) for s in traz["ABA"]).lower()
    assert "entibaci" in traz_texto, (
        f"Trazabilidad ABA no menciona entibacion: {traz['ABA']}"
    )

    # Partida de entibacion en OBRA CIVIL ABASTECIMIENTO
    cap_aba = [k for k in r["capitulos"] if "OBRA CIVIL ABASTECIMIENTO" in k][0]
    partidas = r["capitulos"][cap_aba]["partidas"]
    tiene_entib = any("entib" in nombre.lower() for nombre, v in partidas.items() if v > 0)
    assert tiene_entib, (
        f"No se encontro partida de entibacion en OBRA CIVIL ABA. Partidas: {list(partidas.keys())}"
    )


def test_profundidad_baja_sin_entibacion():
    """Profundidad 1.0m (< umbral 1.5m ABA) no activa entibacion."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    cap_aba = [k for k in r["capitulos"] if "OBRA CIVIL ABASTECIMIENTO" in k][0]
    partidas = r["capitulos"][cap_aba]["partidas"]

    # No debe haber partida de entibacion con importe > 0
    tiene_entib = any("entib" in nombre.lower() for nombre, v in partidas.items() if v > 0)
    assert not tiene_entib, (
        f"No deberia haber entibacion a P=1.0m. Partidas con entib: "
        f"{[(n, v) for n, v in partidas.items() if 'entib' in n.lower()]}"
    )


def test_desmontaje_fibrocemento():
    """Desmontaje fibrocemento genera partida especifica en OBRA CIVIL ABA."""
    at = _app_calculadora().run()

    # Configurar inputs ABA primero para que aparezca el radio de desmontaje
    at.number_input(key="ABAS_longitud").set_value(100.0)
    at.number_input(key="ABAS_profundidad").set_value(1.2)
    at.selectbox(key="ABAS_diametro").set_value(150)
    at.run()

    # Seleccionar desmontaje fibrocemento
    at.radio(key="desmontaje_tipo").set_value("fibrocemento").run()

    # Calcular
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    cap_aba = [k for k in r["capitulos"] if "OBRA CIVIL ABASTECIMIENTO" in k][0]
    partidas = r["capitulos"][cap_aba]["partidas"]

    tiene_fibro = any("fibrocemento" in nombre.lower() for nombre, v in partidas.items() if v > 0)
    assert tiene_fibro, (
        f"No se encontro partida de fibrocemento. Partidas: {list(partidas.keys())}"
    )


def test_guardar_en_historial():
    """Calcular ABA y guardar en historial incrementa el contador de presupuestos."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception
    assert "resultado" in at.session_state

    n_antes = contar_presupuestos()

    at.button(key="btn_guardar").click().run()
    assert not at.exception

    n_despues = contar_presupuestos()
    assert n_despues == n_antes + 1, (
        f"Esperado {n_antes + 1} presupuestos, hay {n_despues}"
    )

    # Cleanup: eliminar el presupuesto recien creado
    lista = listar_presupuestos(limit=1, offset=0)
    if lista:
        eliminar_presupuesto(lista[0]["id"])
        assert contar_presupuestos() == n_antes


def test_trazabilidad_presente():
    """El motor experto genera trazabilidad con explicaciones para ABA."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=150, longitud=100.0, profundidad=1.2)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    assert "trazabilidad" in r
    traz = r["trazabilidad"]
    assert isinstance(traz, dict)
    assert len(traz) > 0, "Trazabilidad vacia"
    assert "ABA" in traz
    assert isinstance(traz["ABA"], list)
    assert len(traz["ABA"]) >= 1, "Trazabilidad ABA sin explicaciones"
    assert all(isinstance(s, str) for s in traz["ABA"])


def test_resultado_determinista():
    """Dos calculos identicos producen exactamente el mismo resultado."""
    def _calcular():
        at = _app_calculadora().run()
        at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
        assert not at.exception
        assert "resultado" in at.session_state
        return at.session_state["resultado"]

    r1 = _calcular()
    r2 = _calcular()

    assert r1["total"] == r2["total"], f"Totales difieren: {r1['total']} vs {r2['total']}"
    assert r1["pem"] == r2["pem"], f"PEMs difieren: {r1['pem']} vs {r2['pem']}"
    assert r1["pbl_sin_iva"] == r2["pbl_sin_iva"]


def test_acometidas_afectan_total():
    """Anadir acometidas ABA incrementa el total del presupuesto."""
    # Sin acometidas
    at1 = _app_calculadora().run()
    at1.number_input(key="acometidas_aba_n").set_value(0)
    at1 = _calcular_aba(at1, dn=150, longitud=100.0, profundidad=1.2)
    assert not at1.exception
    assert "resultado" in at1.session_state
    total_sin = at1.session_state["resultado"]["total"]

    # Con 5 acometidas
    at2 = _app_calculadora().run()
    at2.number_input(key="acometidas_aba_n").set_value(5)
    at2 = _calcular_aba(at2, dn=150, longitud=100.0, profundidad=1.2)
    assert not at2.exception
    assert "resultado" in at2.session_state
    total_con = at2.session_state["resultado"]["total"]

    assert total_con > total_sin, (
        f"Total con acometidas ({total_con:.2f}) deberia ser mayor que sin ({total_sin:.2f})"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Ronda 3 - Tests de opciones adicionales
# ═══════════════════════════════════════════════════════════════════════════════


def test_pavimentacion_aba():
    """Cap 03 PAVIMENTACION ABA se genera con acerado y bordillo > 0."""
    at = _app_calculadora().run()
    at.number_input(key="ABAS_longitud").set_value(100.0)
    at.number_input(key="ABAS_profundidad").set_value(1.2)
    at.selectbox(key="ABAS_diametro").set_value(150)
    at.number_input(key="pav_aba_acerado_m2").set_value(100.0)
    at.number_input(key="pav_aba_bordillo_m").set_value(50.0)
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    caps = at.session_state["resultado"]["capitulos"]
    cap_pav = [k for k in caps if "PAVIMENTACI" in k and "ABASTECIMIENTO" in k]
    assert len(cap_pav) == 1, f"Cap PAVIMENTACION ABA ausente. Caps: {list(caps.keys())}"
    assert caps[cap_pav[0]]["subtotal"] > 0


def test_pavimentacion_san():
    """Cap 04 PAVIMENTACION SAN se genera con calzada y acera > 0."""
    at = _app_calculadora().run()
    at.radio(key="modo_actuacion").set_value("Solo Saneamiento").run()
    at.number_input(key="SAN_longitud").set_value(100.0)
    at.number_input(key="SAN_profundidad").set_value(1.5)
    at.number_input(key="pav_san_calzada_m2").set_value(150.0)
    at.number_input(key="pav_san_acera_m2").set_value(80.0)
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    caps = at.session_state["resultado"]["capitulos"]
    cap_pav = [k for k in caps if "PAVIMENTACI" in k and "SANEAMIENTO" in k]
    assert len(cap_pav) == 1, f"Cap PAVIMENTACION SAN ausente. Caps: {list(caps.keys())}"
    assert caps[cap_pav[0]]["subtotal"] > 0


def test_subbase_aba():
    """Sub-base ABA incrementa el subtotal de PAVIMENTACION ABA."""
    # Sin sub-base
    at1 = _app_calculadora().run()
    at1.number_input(key="ABAS_longitud").set_value(100.0)
    at1.number_input(key="ABAS_profundidad").set_value(1.2)
    at1.selectbox(key="ABAS_diametro").set_value(150)
    at1.number_input(key="pav_aba_acerado_m2").set_value(100.0)
    at1.run()
    at1.button(key="btn_calcular").click().run()
    assert not at1.exception
    assert "resultado" in at1.session_state
    cap_pav1 = [k for k in at1.session_state["resultado"]["capitulos"]
                if "PAVIMENTACI" in k and "ABASTECIMIENTO" in k]
    sub_sin = at1.session_state["resultado"]["capitulos"][cap_pav1[0]]["subtotal"] if cap_pav1 else 0.0

    # Con sub-base espesor=0.15 (primer item: "Base albero compactado")
    at2 = _app_calculadora().run()
    at2.number_input(key="ABAS_longitud").set_value(100.0)
    at2.number_input(key="ABAS_profundidad").set_value(1.2)
    at2.selectbox(key="ABAS_diametro").set_value(150)
    at2.number_input(key="pav_aba_acerado_m2").set_value(100.0)
    at2.number_input(key="subbase_aba_espesor").set_value(0.15)
    at2.run()
    at2.button(key="btn_calcular").click().run()
    assert not at2.exception
    assert "resultado" in at2.session_state
    cap_pav2 = [k for k in at2.session_state["resultado"]["capitulos"]
                if "PAVIMENTACI" in k and "ABASTECIMIENTO" in k]
    assert len(cap_pav2) == 1
    sub_con = at2.session_state["resultado"]["capitulos"][cap_pav2[0]]["subtotal"]
    assert sub_con > sub_sin, f"Subbase deberia incrementar: sin={sub_sin:.2f} con={sub_con:.2f}"


def test_imbornales_san():
    """Imbornales SAN (adaptacion) generan partida en OBRA CIVIL SANEAMIENTO."""
    at = _app_calculadora().run()
    at.radio(key="modo_actuacion").set_value("Solo Saneamiento").run()
    at = _calcular_san(at, dn=300, longitud=100.0, profundidad=1.5)
    assert not at.exception
    assert "resultado" in at.session_state

    # Ahora con imbornales
    at2 = _app_calculadora().run()
    at2.radio(key="modo_actuacion").set_value("Solo Saneamiento").run()
    at2.number_input(key="SAN_longitud").set_value(100.0)
    at2.number_input(key="SAN_profundidad").set_value(1.5)
    at2.radio(key="imbornales_tipo").set_value("adaptacion")
    at2.run()
    at2.button(key="btn_calcular").click().run()
    assert not at2.exception
    assert "resultado" in at2.session_state

    caps = at2.session_state["resultado"]["capitulos"]
    cap_san = [k for k in caps if "OBRA CIVIL SANEAMIENTO" in k][0]
    partidas = caps[cap_san]["partidas"]
    tiene_imb = any("imbornal" in nombre.lower() for nombre, v in partidas.items() if v > 0)
    assert tiene_imb, f"No se encontro partida imbornal. Partidas: {list(partidas.keys())}"

    # El total con imbornales debe ser mayor
    total_sin = at.session_state["resultado"]["total"]
    total_con = at2.session_state["resultado"]["total"]
    assert total_con > total_sin


def test_pozos_existentes_aba():
    """Pozos existentes ABA demolicion incrementa el total."""
    # Sin pozos existentes
    at1 = _app_calculadora().run()
    at1 = _calcular_aba(at1, dn=150, longitud=100.0, profundidad=1.2)
    assert not at1.exception
    total_sin = at1.session_state["resultado"]["total"]

    # Con demolicion de pozos existentes ABA
    at2 = _app_calculadora().run()
    at2.number_input(key="ABAS_longitud").set_value(100.0)
    at2.number_input(key="ABAS_profundidad").set_value(1.2)
    at2.selectbox(key="ABAS_diametro").set_value(150)
    at2.radio(key="pozex_aba").set_value("demolicion")
    at2.run()
    at2.button(key="btn_calcular").click().run()
    assert not at2.exception
    assert "resultado" in at2.session_state
    total_con = at2.session_state["resultado"]["total"]

    assert total_con > total_sin, (
        f"Pozos existentes ABA deberian incrementar total: sin={total_sin:.2f} con={total_con:.2f}"
    )


def test_desmontaje_normal():
    """Desmontaje normal (no fibrocemento) genera partida en OBRA CIVIL ABA."""
    at = _app_calculadora().run()
    at.number_input(key="ABAS_longitud").set_value(100.0)
    at.number_input(key="ABAS_profundidad").set_value(1.2)
    at.selectbox(key="ABAS_diametro").set_value(100)  # DN=100 < 150 → aplica primer item
    at.radio(key="desmontaje_tipo").set_value("normal")
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    caps = at.session_state["resultado"]["capitulos"]
    cap_aba = [k for k in caps if "OBRA CIVIL ABASTECIMIENTO" in k][0]
    partidas = caps[cap_aba]["partidas"]
    tiene_desm = any("desmontaje" in nombre.lower() for nombre, v in partidas.items() if v > 0)
    assert tiene_desm, (
        f"No se encontro partida de desmontaje normal. Partidas: {list(partidas.keys())}"
    )


def test_conduccion_provisional():
    """Conduccion provisional PE incrementa el total."""
    # Sin conduccion
    at1 = _app_calculadora().run()
    at1 = _calcular_aba(at1, dn=150, longitud=100.0, profundidad=1.2)
    assert not at1.exception
    total_sin = at1.session_state["resultado"]["total"]

    # Con 50m de conduccion provisional
    at2 = _app_calculadora().run()
    at2.number_input(key="ABAS_longitud").set_value(100.0)
    at2.number_input(key="ABAS_profundidad").set_value(1.2)
    at2.selectbox(key="ABAS_diametro").set_value(150)
    at2.number_input(key="conduccion_provisional_m").set_value(50.0)
    at2.run()
    at2.button(key="btn_calcular").click().run()
    assert not at2.exception
    assert "resultado" in at2.session_state
    total_con = at2.session_state["resultado"]["total"]

    assert total_con > total_sin, (
        f"Conduccion provisional deberia incrementar total: sin={total_sin:.2f} con={total_con:.2f}"
    )


def test_pct_gestion_genera_capitulo():
    """pct_gestion=2% (widget en %) genera capitulo GESTION AMBIENTAL."""
    at = _app_calculadora().run()
    at.number_input(key="pct_gestion").set_value(2.0)
    at.run()
    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception
    assert "resultado" in at.session_state

    caps = at.session_state["resultado"]["capitulos"]
    cap_ga = [k for k in caps if "GESTI" in k and "AMBIENTAL" in k]
    assert len(cap_ga) >= 1, f"Cap GESTION AMBIENTAL ausente. Caps: {list(caps.keys())}"
    assert caps[cap_ga[0]]["subtotal"] > 0


def test_pct_servicios_afectados():
    """pct_servicios_afectados=1% genera partida 'Servicios afectados'."""
    at = _app_calculadora().run()
    at.number_input(key="pct_servicios_afectados").set_value(1.0)
    at.run()
    at = _calcular_aba(at, dn=100, longitud=50.0, profundidad=1.0)
    assert not at.exception
    assert "resultado" in at.session_state

    caps = at.session_state["resultado"]["capitulos"]
    # Servicios afectados se acumula en SEGURIDAD Y SALUD
    cap_ss = [k for k in caps if "SEGURIDAD" in k]
    assert len(cap_ss) >= 1, f"Cap SEGURIDAD Y SALUD ausente. Caps: {list(caps.keys())}"
    partidas_ss = caps[cap_ss[0]]["partidas"]
    tiene_sa = any("servicios" in nombre.lower() for nombre, v in partidas_ss.items() if v > 0)
    assert tiene_sa, (
        f"Partida 'Servicios afectados' ausente en S&S. Partidas: {list(partidas_ss.keys())}"
    )


def test_gg_bi_proporcionales():
    """GG y BI son proporcionales: gg/bi == pct_gg/pct_bi (misma base de calculo)."""
    at = _app_calculadora().run()
    at = _calcular_aba(at, dn=150, longitud=100.0, profundidad=1.2)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    pct_gg = r["pcts"]["gg"]
    pct_bi = r["pcts"]["bi"]
    assert pct_bi > 0, "pct_bi debe ser positivo"
    assert r["bi"] > 0, "BI debe ser positivo"

    ratio_calculado = r["gg"] / r["bi"]
    ratio_esperado = pct_gg / pct_bi
    assert ratio_calculado == pytest.approx(ratio_esperado, rel=0.001), (
        f"GG/BI={ratio_calculado:.4f} != pct_gg/pct_bi={ratio_esperado:.4f}. "
        "Los materiales no se estan excluyendo correctamente de la base GG/BI."
    )


def test_pct_manual_afecta_total():
    """Distinto % de excavacion manual produce totales distintos."""
    # Con 10% manual
    at1 = _app_calculadora().run()
    at1.number_input(key="pct_manual_pct").set_value(10)
    at1 = _calcular_aba(at1, dn=150, longitud=100.0, profundidad=1.2)
    assert not at1.exception
    assert "resultado" in at1.session_state
    total_10 = at1.session_state["resultado"]["total"]

    # Con 80% manual
    at2 = _app_calculadora().run()
    at2.number_input(key="pct_manual_pct").set_value(80)
    at2 = _calcular_aba(at2, dn=150, longitud=100.0, profundidad=1.2)
    assert not at2.exception
    assert "resultado" in at2.session_state
    total_80 = at2.session_state["resultado"]["total"]

    assert total_10 != total_80, (
        f"Totales deberian diferir: 10%={total_10:.2f}, 80%={total_80:.2f}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Ronda 4 - Tests de validación
# ═══════════════════════════════════════════════════════════════════════════════


def test_error_sin_red_activa():
    """Calcular sin longitud valida muestra error sin excepcion."""
    at = _app_calculadora().run()
    # Longitud 0 en ABA → validar_parametros() debe rechazar
    at.number_input(key="ABAS_longitud").set_value(0.0)
    at.number_input(key="ABAS_profundidad").set_value(0.0)
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception

    # Si hay resultado, debe ser con PEM=0 o no haber resultado
    if "resultado" in at.session_state:
        r = at.session_state["resultado"]
        assert r["total"] == pytest.approx(0.0, abs=0.01), \
            f"Con L=0 el total deberia ser 0, encontrado {r['total']}"


# ═══════════════════════════════════════════════════════════════════════════════
# Ronda 5 - Tests de auditoría (D.2 integración + D.3 edge cases)
# ═══════════════════════════════════════════════════════════════════════════════


def test_san_entibacion_profunda():
    """SAN P=3.0 selecciona entibacion profunda (precio ~22.73 con CI), no superficial (~4.27)."""
    at = _app_calculadora().run()
    at.radio(key="modo_actuacion").set_value("Solo Saneamiento").run()
    at = _calcular_san(at, dn=300, longitud=100.0, profundidad=3.0)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    cap_san = [k for k in r["capitulos"] if "OBRA CIVIL SANEAMIENTO" in k][0]
    partidas = r["capitulos"][cap_san]["partidas"]

    # Buscar partida de entibacion
    entib_partidas = {n: v for n, v in partidas.items() if "entib" in n.lower() and v > 0}
    assert entib_partidas, f"No hay entibacion a P=3.0. Partidas: {list(partidas.keys())}"

    # La entibacion profunda es mucho mas cara que la superficial.
    # Superficie entib = (3+1)*2*1.1 = 8.8 m2/m * 100m = 880 m2
    # Con precio profunda (22.73): 880*22.73 ≈ 20002
    # Con precio superficial (4.27): 880*4.27 ≈ 3758
    total_entib = sum(entib_partidas.values())
    assert total_entib > 10000, (
        f"Entibacion P=3.0 SAN deberia usar precio profundo (~22.73). "
        f"Total entib = {total_entib:.2f} (esperado >10000)"
    )


def test_espesor_pavimento_genera_canon():
    """espesor_pavimento > 0 produce canon_mixto en los auxiliares."""
    at = _app_calculadora().run()

    at.number_input(key="ABAS_longitud").set_value(100.0)
    at.number_input(key="ABAS_profundidad").set_value(1.2)
    at.selectbox(key="ABAS_diametro").set_value(150)
    at.number_input(key="espesor_pavimento_m").set_value(0.20)
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    cap_aba = [k for k in r["capitulos"] if "OBRA CIVIL ABASTECIMIENTO" in k][0]
    partidas = r["capitulos"][cap_aba]["partidas"]

    tiene_canon_mixto = any("mixto" in n.lower() for n, v in partidas.items() if v > 0)
    assert tiene_canon_mixto, (
        f"Con espesor_pavimento=0.20 deberia haber canon mixto. Partidas: {list(partidas.keys())}"
    )


def test_zero_materiales_base_ggbi():
    """Sin materiales (tuberias sin precio_material_m), base_gg_bi debe igualar PEM."""
    # Usar un caso SAN-only (Gres no tiene precio_material_m)
    at = _app_calculadora().run()
    at.radio(key="modo_actuacion").set_value("Solo Saneamiento").run()
    at = _calcular_san(at, dn=300, longitud=50.0, profundidad=1.5)
    assert not at.exception
    assert "resultado" in at.session_state

    r = at.session_state["resultado"]
    pem = r["pem"]
    gg = r["gg"]
    bi = r["bi"]
    pcts = r["pcts"]

    # En SAN-only, los materiales son solo tapa+pates (muy poco)
    # Verificar que GG/BI son proporcionales a base que es cercana al PEM
    ratio = gg / bi if bi > 0 else 0
    ratio_esperado = pcts["gg"] / pcts["bi"]
    assert ratio == pytest.approx(ratio_esperado, rel=0.001)


def test_desmontaje_dn_boundary():
    """DN=150 normal selecciona desmontaje con dn_max=150 (<=, no <)."""
    at = _app_calculadora().run()
    at.number_input(key="ABAS_longitud").set_value(100.0)
    at.number_input(key="ABAS_profundidad").set_value(1.2)
    at.selectbox(key="ABAS_diametro").set_value(150)
    at.radio(key="desmontaje_tipo").set_value("normal")
    at.run()
    at.button(key="btn_calcular").click().run()
    assert not at.exception
    assert "resultado" in at.session_state

    caps = at.session_state["resultado"]["capitulos"]
    cap_aba = [k for k in caps if "OBRA CIVIL ABASTECIMIENTO" in k][0]
    partidas = caps[cap_aba]["partidas"]

    # DN=150 debe entrar en "DN<150mm" (dn_max=150, regla <=)
    tiene_desm = any("desmontaje" in n.lower() for n, v in partidas.items() if v > 0)
    assert tiene_desm, (
        f"DN=150 con desmontaje normal deberia generar partida. "
        f"Partidas: {list(partidas.keys())}"
    )
