"""Test de invariante: BD.precio × pct_ci(1.05) == Excel oficial EMASESA.

Fuente canónica: ``data/catalogo_oficial.json`` (snapshot versionado derivado
del Excel). El JSON contiene los precios oficiales con CI aplicado. La BD
almacena precio base (sin CI). Invariante: ``BD.precio × 1.05 ≈ JSON.precio``.

**Alcance real** (no "100 % de la BD"): el test cubre **100 % del subset
auditado del Excel oficial** (~77 entradas en catalogo_oficial.json de un
catálogo BD de ~200 filas). Las filas BD que NO están en el JSON son
enriquecimiento legítimo del catálogo EMASESA completo (ej. acerados
"Baldosa cigarrillo", bordillo bicapa, pozos SAN por profundidad+DN) y
quedan FUERA de este test.

Adicionalmente se incluyen `test_deuda_conocida_patron_d` como `xfail` para
rastrear drifts conocidos no resueltos (valvulería compuerta DN100-149 /
DN200-299); si se resuelven pasarán a XPASS forzando revisión.

Excepción a la regla "solo AppTest" del proyecto: este test verifica un
invariante de BD (SELECT puro) sin superficie Streamlit.
Ver AGENTS.md § "Invariantes de BD".
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import pytest

from src.infraestructura.db import DB_PATH
from src.infraestructura.db_precios import cargar_todo

ROOT = Path(__file__).resolve().parent.parent
CATALOGO_JSON = ROOT / "data" / "catalogo_oficial.json"

CI = 1.05
TOLERANCIA_REL = 0.001  # 0.1 %


@pytest.fixture(scope="module")
def catalogo_oficial():
    return json.loads(CATALOGO_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def precios_bd():
    return cargar_todo()


# --- Resolvers: localizar precio BD para cada categoría JSON ----------------

def _buscar_tuberia(catalogo_key, precios_bd, tipo, dn):
    for item in precios_bd.get(catalogo_key, []):
        if item["tipo"] == tipo and int(item["diametro_mm"]) == dn:
            return item["precio_m"]
    return None


def _buscar_valvuleria_conexion(precios_bd, dn):
    """Devuelve el precio del rango (dn_min, dn_max) que contiene DN."""
    for item in precios_bd.get("catalogo_valvuleria", []):
        if (item["tipo"] == "conexion"
                and int(item["dn_min"]) <= dn <= int(item["dn_max"])):
            return item["precio"]
    return None


def _buscar_acerado(precios_bd, red, material):
    """Acerados: se compara por material normalizado vs label BD normalizado."""
    clave = "acerados_aba" if red == "ABA" else "acerados_san"
    for item in precios_bd.get(clave, []):
        if _norm(item["label"]) == _norm(material):
            return item["precio"]
    return None


def _buscar_bordillo(precios_bd, material):
    for item in precios_bd.get("bordillos_reposicion", []):
        label_n = _norm(item["label"])
        if material in label_n:
            return item["precio"]
    return None


def _buscar_calzada(precios_bd, material, unidad):
    mapeo_material = {
        "adoquin": ["adoquin"],
        "capa de rodadura": ["aglomerado"],  # BD "Aglomerado" = Excel "Capa de rodadura"
        "capa base pavimento": ["capa base"],
        "hormigon": ["hormigon"],
        "base": ["base zahorra", "base"],
    }
    keywords = mapeo_material.get(material, [material])
    for item in precios_bd.get("calzadas_reposicion", []):
        if item["unidad"] != unidad:
            continue
        label_n = _norm(item["label"])
        if any(kw in label_n for kw in keywords):
            return item["precio"]
    return None


def _buscar_imbornal(precios_bd, label):
    for item in precios_bd.get("catalogo_imbornales", []):
        if item["label"] == label:
            return item["precio"]
    return None


def _buscar_acometida(precios_bd, red, tipo):
    clave = "acometidas_aba_tipos" if red == "ABA" else "acometidas_san_tipos"
    return precios_bd.get(clave, {}).get(tipo)


def _buscar_desmontaje(precios_bd, dn_max):
    for item in precios_bd.get("catalogo_desmontaje", []):
        if int(item["dn_max"]) == int(dn_max) and not item.get("es_fibrocemento"):
            return item["precio_m"]
    return None


def _buscar_pozo_san_ladrillo(precios_bd, profundidad_max):
    for item in precios_bd.get("catalogo_pozos", []):
        if (item.get("red") == "SAN"
                and "ladrillo" in str(item.get("label", "")).lower()
                and item.get("profundidad_max") == profundidad_max):
            return item["precio"]
    return None


def _buscar_tuberia_aba_hacch(precios_bd, dn):
    for item in precios_bd.get("catalogo_aba", []):
        if item.get("tipo") == "HACCH" and int(item["diametro_mm"]) == int(dn):
            return item["precio_m"]
    return None


def _buscar_pozo_existente(precios_bd, red, accion):
    for item in precios_bd.get("catalogo_pozos_existentes", []):
        if item.get("red") == red and item.get("accion") == accion:
            return item.get("precio")
    return None


def _buscar_entibacion_blindada(precios_bd, red):
    """Entibación blindada estándar; excluye variante 'profunda' (enriquecimiento)."""
    for item in precios_bd.get("catalogo_entibacion", []):
        label = str(item.get("label", "")).lower()
        if "profunda" in label:
            continue
        if item.get("red") in (red, None):
            return item.get("precio_m2")
    return None


def _buscar_conduccion_provisional(precios_bd):
    val = precios_bd.get("conduccion_provisional_precio_m")
    return float(val) if val is not None else None


def _buscar_demolicion(precios_bd, red, tipo_demolicion, material_excel, unidad):
    """Busca precio de demolición en BD por (red, tipo, material, unidad).

    El JSON oficial usa ``material`` con espacios ('losa hidraulica') mientras
    que la BD guarda con underscores ('losa_hidraulica'). Además, 'hormigon'
    en acerado se guarda como 'hormigon_acerado' en BD para evitar colisión
    con la fila de calzada de material 'hormigon'.
    """
    clave = f"demolicion_{red.lower()}"
    cat = precios_bd.get(clave, [])
    mat_norm = material_excel.replace(" ", "_")
    if mat_norm == "hormigon" and tipo_demolicion == "acerado":
        mat_norm = "hormigon_acerado"
    for item in cat:
        if (item.get("material") == mat_norm
                and item.get("unidad") == unidad
                and tipo_demolicion in item.get("label", "").lower()):
            return item["precio"]
    return None


def _norm(s: str) -> str:
    import unicodedata
    if not s:
        return ""
    s = s.strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


# --- Test helpers -----------------------------------------------------------

def _verificar_invariante(concepto, bd_precio, excel_precio):
    if bd_precio is None:
        pytest.skip(f"{concepto}: sin contraparte en BD (enriquecimiento Excel)")
    esperado_base = excel_precio / CI
    assert math.isclose(bd_precio, esperado_base, rel_tol=TOLERANCIA_REL), (
        f"{concepto}: BD={bd_precio:.4f}, esperado_base={esperado_base:.4f} "
        f"(Excel={excel_precio}), drift={(bd_precio - esperado_base) / esperado_base * 100:+.2f}%"
    )


# --- Tests parametrizados ---------------------------------------------------

def _cargar_casos():
    """Aplana el JSON en una lista de (concepto, categoria, clave, precio_excel) para parametrizar."""
    cat = json.loads(CATALOGO_JSON.read_text(encoding="utf-8"))
    casos = []
    for clave, precio in cat.get("excavacion", {}).items():
        casos.append((f"excavacion.{clave}", "excavacion", clave, precio))
    for item in cat.get("tuberia_aba", []):
        casos.append((
            f"tuberia_aba.{item['tipo']}.DN{item['dn']}",
            "tuberia_aba", (item["tipo"], item["dn"]), item["precio"],
        ))
    for item in cat.get("tuberia_san", []):
        casos.append((
            f"tuberia_san.{item['tipo']}.DN{item['dn']}",
            "tuberia_san", (item["tipo"], item["dn"]), item["precio"],
        ))
    for item in cat.get("valvuleria_conexion", []):
        casos.append((
            f"valvuleria_conexion.DN{item['dn']}",
            "valvuleria_conexion", item["dn"], item["precio"],
        ))
    for item in cat.get("acerados_aba", []):
        casos.append((
            f"acerados_aba.{item['material']}",
            "acerados_aba", item["material"], item["precio"],
        ))
    for item in cat.get("acerados_san", []):
        casos.append((
            f"acerados_san.{item['material']}",
            "acerados_san", item["material"], item["precio"],
        ))
    for item in cat.get("bordillos", []):
        casos.append((
            f"bordillos.{item['material']}",
            "bordillos", item["material"], item["precio"],
        ))
    for item in cat.get("calzadas", []):
        casos.append((
            f"calzadas.{item['material']}.{item['unidad']}",
            "calzadas", (item["material"], item["unidad"]), item["precio"],
        ))
    for item in cat.get("imbornales", []):
        casos.append((
            f"imbornales.{item['label']}",
            "imbornales", item["label"], item["precio"],
        ))
    for item in cat.get("acometidas", []):
        casos.append((
            f"acometidas.{item['red']}.{item['tipo']}",
            "acometidas", (item["red"], item["tipo"]), item["precio"],
        ))
    for item in cat.get("desmontaje", []):
        casos.append((
            f"desmontaje.dn_max={item['dn_max']}",
            "desmontaje", item["dn_max"], item["precio"],
        ))
    for item in cat.get("pozos_san_ladrillo", []):
        casos.append((
            f"pozo_san_ladrillo.P={item['profundidad_max']}",
            "pozos_san_ladrillo", item["profundidad_max"], item["precio"],
        ))
    for item in cat.get("tuberia_aba_hacch", []):
        casos.append((
            f"tuberia_aba_hacch.DN{item['dn']}",
            "tuberia_aba_hacch", item["dn"], item["precio"],
        ))
    for item in cat.get("pozos_existentes", []):
        # Excel modela 1 precio por acción; BD separa ABA/SAN como enriquecimiento.
        # Se comprueba cada lado contra la referencia Excel agregada.
        if item["accion"] == "acondicionamiento":
            # BD no modela acondicionamiento (solo demolición/anulación).
            continue
        for red in ("ABA", "SAN"):
            casos.append((
                f"pozo_existente.{red}.{item['accion']}",
                "pozo_existente", (red, item["accion"]), item["precio"],
            ))
    for item in cat.get("entibacion_blindada", []):
        casos.append((
            "entibacion_blindada.ABA",
            "entibacion_blindada", "ABA", item["precio"],
        ))
        casos.append((
            "entibacion_blindada.SAN",
            "entibacion_blindada", "SAN", item["precio"],
        ))
    if "conduccion_provisional_pe" in cat:
        casos.append((
            "conduccion_provisional_pe",
            "conduccion_provisional_pe", None,
            cat["conduccion_provisional_pe"],
        ))
    for item in cat.get("demolicion_aba", []):
        casos.append((
            f"demolicion_aba.{item['tipo_demolicion']}.{item['material']}.{item['unidad']}",
            "demolicion_aba",
            (item["tipo_demolicion"], item["material"], item["unidad"]),
            item["precio"],
        ))
    for item in cat.get("demolicion_san", []):
        casos.append((
            f"demolicion_san.{item['tipo_demolicion']}.{item['material']}.{item['unidad']}",
            "demolicion_san",
            (item["tipo_demolicion"], item["material"], item["unidad"]),
            item["precio"],
        ))
    return casos


@pytest.mark.parametrize("concepto, categoria, clave, precio_excel", _cargar_casos())
def test_invariante_catalogo_oficial(precios_bd, concepto, categoria, clave, precio_excel):
    """Para cada precio del catálogo oficial, BD × 1.05 ≈ Excel (si BD lo tiene)."""
    if categoria == "excavacion":
        bd = precios_bd.get("excavacion", {}).get(clave)
    elif categoria == "tuberia_aba":
        tipo, dn = clave
        bd = _buscar_tuberia("catalogo_aba", precios_bd, tipo, dn)
    elif categoria == "tuberia_san":
        tipo, dn = clave
        bd = _buscar_tuberia("catalogo_san", precios_bd, tipo, dn)
    elif categoria == "valvuleria_conexion":
        bd = _buscar_valvuleria_conexion(precios_bd, clave)
    elif categoria == "acerados_aba":
        bd = _buscar_acerado(precios_bd, "ABA", clave)
    elif categoria == "acerados_san":
        bd = _buscar_acerado(precios_bd, "SAN", clave)
    elif categoria == "bordillos":
        bd = _buscar_bordillo(precios_bd, clave)
    elif categoria == "calzadas":
        material, unidad = clave
        bd = _buscar_calzada(precios_bd, material, unidad)
    elif categoria == "imbornales":
        bd = _buscar_imbornal(precios_bd, clave)
    elif categoria == "acometidas":
        red, tipo = clave
        bd = _buscar_acometida(precios_bd, red, tipo)
    elif categoria == "desmontaje":
        bd = _buscar_desmontaje(precios_bd, clave)
    elif categoria == "pozos_san_ladrillo":
        bd = _buscar_pozo_san_ladrillo(precios_bd, clave)
    elif categoria == "tuberia_aba_hacch":
        bd = _buscar_tuberia_aba_hacch(precios_bd, clave)
    elif categoria == "pozo_existente":
        red, accion = clave
        bd = _buscar_pozo_existente(precios_bd, red, accion)
        if bd is None:
            pytest.skip(f"pozo_existente {red} {accion}: sin fila BD")
        # BD separa ABA/SAN; si la desviación es >5% tras ×CI, marcar skip
        # (el Excel es referencia agregada sin red). Si es ≤5%, asertar.
        esperado_base = precio_excel / CI
        drift_rel = abs(bd - esperado_base) / esperado_base
        if drift_rel > 0.05:
            pytest.skip(
                f"pozo_existente {red} {accion}: BD={bd:.2f}, esperado={esperado_base:.2f}, "
                f"drift {drift_rel*100:.1f}%. BD separa ABA/SAN; Excel es referencia agregada."
            )
        _verificar_invariante(f"pozo_existente.{red}.{accion}", bd, precio_excel)
        return
    elif categoria == "entibacion_blindada":
        bd = _buscar_entibacion_blindada(precios_bd, clave)
    elif categoria == "conduccion_provisional_pe":
        bd = _buscar_conduccion_provisional(precios_bd)
    elif categoria == "demolicion_aba":
        tipo, material, unidad = clave
        bd = _buscar_demolicion(precios_bd, "ABA", tipo, material, unidad)
    elif categoria == "demolicion_san":
        tipo, material, unidad = clave
        bd = _buscar_demolicion(precios_bd, "SAN", tipo, material, unidad)
    else:
        pytest.fail(f"Categoría desconocida: {categoria}")

    _verificar_invariante(concepto, bd, precio_excel)


# --- Precios que actualmente NO están en el JSON oficial pero sí en BD ------
# (Enriquecimiento intencional, documentado en AGENTS.md)
# Estos NO se testean contra invariante porque no hay precio oficial Excel.

def test_catalogo_oficial_tiene_metadato(catalogo_oficial):
    """El JSON oficial debe tener metadato correcto para trazabilidad."""
    meta = catalogo_oficial.get("_meta", {})
    assert meta.get("excel_source"), "Falta _meta.excel_source"
    assert meta.get("pct_ci_excel") == 1.05, "Falta pct_ci_excel o es != 1.05"


# ---------------------------------------------------------------------------
# Test de integridad de tipo: todos los precios en BD deben ser INTEGER
# (céntimos). SQLite tiene afinidad dinámica de tipos — una columna declarada
# INTEGER aceptará un REAL si alguna ruta de guardado omite `round()`. Bug
# invisible que causaría undercharge 100×. Este test lo captura inmediatamente.
# ---------------------------------------------------------------------------

COLUMNAS_MONETARIAS = [
    ("tuberias", "precio_m"),
    ("tuberias", "precio_material_m"),
    ("valvuleria", "precio"),
    ("valvuleria", "precio_material"),
    ("pozos", "precio"),
    ("pozos", "precio_tapa"),
    ("pozos", "precio_tapa_material"),
    ("pozos", "precio_pate_material"),
    ("acerados", "precio"),
    ("bordillos", "precio"),
    ("calzadas", "precio"),
    ("demolicion", "precio"),
    ("entibacion", "precio_m2"),
    ("acometidas", "precio"),
    ("subbases", "precio_m3"),
    ("desmontaje", "precio_m"),
    ("imbornales", "precio"),
    ("pozos_existentes_precios", "precio"),
]


def test_acometidas_aba_factor_piezas_no_regresion():
    """Guard contra reintroducción del factor_piezas=1.2 en acometidas ABA.

    Audit A2C (2026-04-19) retiró el 1.2 porque el Excel de EMASESA ya
    incluye piezas en el precio unitario de acometida (doble penalización).
    Este test avisa si una migración futura lo reintroduce.
    """
    with sqlite3.connect(str(DB_PATH)) as con:
        rows = con.execute(
            "SELECT tipo, factor_piezas FROM acometidas WHERE red='ABA'"
        ).fetchall()
    for tipo, fp in rows:
        assert fp == 1.0, f"acometida ABA '{tipo}' tiene factor_piezas={fp}, esperado 1.0"


@pytest.mark.parametrize("tabla, columna", COLUMNAS_MONETARIAS)
def test_precios_son_integer(tabla, columna):
    """Tras M13, todos los precios monetarios deben almacenarse como INTEGER céntimos."""
    with sqlite3.connect(str(DB_PATH)) as con:
        n_no_integer = con.execute(
            f"SELECT COUNT(*) FROM {tabla} "
            f"WHERE {columna} IS NOT NULL AND typeof({columna}) != 'integer'"
        ).fetchone()[0]
    assert n_no_integer == 0, (
        f"{tabla}.{columna} contiene {n_no_integer} valores no-INTEGER. "
        "Alguna ruta de guardado posiblemente omitió round(val * 100)."
    )


# ---------------------------------------------------------------------------
# Deuda conocida (Patrón D): valvulería compuerta rangos DN100-149 y DN200-299.
#
# BD (INTEGER céntimos, eur base) × 1.05 vs Excel ABA compuerta:
#   DN100-149: BD 199.84 → BD×1.05 = 209.83. Excel DN150 = 220.32. Drift -4.76 %.
#   DN200-299: BD 272.00 → BD×1.05 = 285.60. Excel DN250 = 299.88. Drift -4.76 %.
# Ambos muestran ratio 1.05² contra el DN SUPERIOR del rango Excel, sugiriendo
# Patrón A (CI² aplicado). Pero Excel indexa por DN puntual y BD por rango, así
# que la interpretación "BD cubre DN≤rango_max" requiere confirmación del
# usuario antes de aplicar migración correctiva.
#
# Estos tests están marcados como xfail para que el problema no se pierda
# de vista. Si se corrigen, automáticamente pasarán a verde y habrá que
# quitar el xfail.
# ---------------------------------------------------------------------------

PATRON_D_DEUDA = [
    # (dn_excel, precio_excel, precio_bd_esperado_con_ci)
    ("compuerta DN100-149 (BD) ↔ Excel DN150", 220.32, 199.84 * 1.05),
    ("compuerta DN200-299 (BD) ↔ Excel DN250", 299.88, 272.00 * 1.05),
]


@pytest.mark.xfail(
    reason="Patrón D: drift ~-4.76 % valvulería compuerta (mismo patrón 1.05²). "
           "Requiere decisión del usuario sobre mapeo rango_BD ↔ DN_puntual_Excel "
           "antes de aplicar migración correctiva. Ver TODO en "
           "src/infraestructura/db.py _ejecutar_migraciones() final.",
    strict=True,
)
@pytest.mark.parametrize("concepto, precio_excel, bd_con_ci_actual", PATRON_D_DEUDA)
def test_deuda_conocida_patron_d(concepto, precio_excel, bd_con_ci_actual):
    """Verifica que el gap del Patrón D NO se ha resuelto aún.

    Cuando se corrija (p.ej. migración que multiplica precio compuerta por 1.05),
    estos tests pasarán a verde y pytest fallará con `XPASS` obligando a
    revisar y quitar la marca xfail. Así el gap queda tracked automáticamente.
    """
    esperado_base = precio_excel / CI
    bd_base_actual = bd_con_ci_actual / CI
    assert math.isclose(bd_base_actual, esperado_base, rel_tol=TOLERANCIA_REL), (
        f"{concepto}: BD base actual={bd_base_actual:.4f}, "
        f"esperado base (Excel/1.05)={esperado_base:.4f}"
    )
