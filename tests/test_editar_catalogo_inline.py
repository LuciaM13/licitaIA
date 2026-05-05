"""Tests del use case de creación inline de partidas (Phase 3, Plan 01).

Cubren dos capas:

  - ``src.infraestructura.db_precios.insertar_fila_catalogo`` y
    ``escribir_audit_evento`` (helpers públicos de INSERT-único, Tarea 1).
  - ``src.aplicacion.editar_catalogo.insertar_variante_catalogo``
    (use case con validaciones, Tarea 2).

Los tests usan una BD temporal por test (``tmp_path`` + ``shutil.copy``)
para no contaminar ``data/precios.db``. No importan ``streamlit`` (los
modulos bajo prueba son use cases puros).

Excepción a la regla "solo AppTest": estos tests cubren un use case sin
superficie Streamlit; pytest unitarios son la herramienta correcta.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parent.parent
_BD_REAL = _REPO_ROOT / "data" / "precios.db"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bd_temporal(tmp_path: Path) -> Path:
    """Copia ``data/precios.db`` a ``tmp_path`` y devuelve la ruta nueva.

    Cada test recibe una BD aislada; los INSERTs no contaminan la BD real
    ni se filtran entre tests.
    """
    destino = tmp_path / "precios.db"
    shutil.copy(_BD_REAL, destino)
    return destino


# ---------------------------------------------------------------------------
# Tarea 1 - infraestructura: insertar_fila_catalogo + escribir_audit_evento
# ---------------------------------------------------------------------------

def test_1_insertar_fila_catalogo_ok(bd_temporal: Path):
    """INSERT en ``acerados`` con item valido -> devuelve lastrowid > 0."""
    from src.infraestructura.db_precios import insertar_fila_catalogo

    item = {"red": "ABA", "label": "test_acerado_a", "unidad": "m2", "precio": 12.34}
    nuevo_id = insertar_fila_catalogo("acerados", item, path=bd_temporal)

    assert isinstance(nuevo_id, int)
    assert nuevo_id > 0

    with sqlite3.connect(str(bd_temporal)) as conn:
        fila = conn.execute(
            "SELECT id, red, label, unidad, precio FROM acerados WHERE id=?",
            (nuevo_id,),
        ).fetchone()
    assert fila is not None
    assert fila[1] == "ABA"
    assert fila[2] == "test_acerado_a"
    assert fila[3] == "m2"


def test_2_insertar_fila_catalogo_persiste_centimos(bd_temporal: Path):
    """El precio en EUR se persiste como INTEGER centimos (precio*100)."""
    from src.infraestructura.db_precios import insertar_fila_catalogo

    item = {"red": "ABA", "label": "test_centimos", "unidad": "m2", "precio": 12.34}
    nuevo_id = insertar_fila_catalogo("acerados", item, path=bd_temporal)

    with sqlite3.connect(str(bd_temporal)) as conn:
        precio_persistido = conn.execute(
            "SELECT precio FROM acerados WHERE id=?", (nuevo_id,),
        ).fetchone()[0]

    # 12.34 EUR -> 1234 centimos. NO 1295.7 (eso seria pre-multiplicar por 1.05).
    assert precio_persistido == 1234, (
        f"Esperaba 1234 centimos (BASE EMASESA); obtuvo {precio_persistido}. "
        "El use case NO debe pre-multiplicar por 1.05; el CI lo aplica el cargador."
    )


def test_3_insertar_fila_catalogo_tabla_no_permitida(bd_temporal: Path):
    """Tablas fuera del whitelist inline rechazan con ValueError legible."""
    from src.infraestructura.db_precios import insertar_fila_catalogo

    with pytest.raises(ValueError) as exc:
        insertar_fila_catalogo(
            "presupuestos",
            {"descripcion": "x", "pem": 1.0},
            path=bd_temporal,
        )
    assert "no editable inline" in str(exc.value).lower()


def test_4_escribir_audit_evento_anade_una_fila(bd_temporal: Path):
    """``escribir_audit_evento`` escribe exactamente +1 fila en audit_log."""
    from src.infraestructura.db.connection import conectar
    from src.infraestructura.db_precios import escribir_audit_evento

    with sqlite3.connect(str(bd_temporal)) as conn:
        antes = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    payload = {"red": "ABA", "label": "test_audit", "unidad": "m2", "precio": 9.99}
    with conectar(bd_temporal) as conn:
        escribir_audit_evento(
            conn,
            categoria="acerados",
            clave="test_audit",
            operacion="INSERT",
            antes_json=None,
            despues_json=json.dumps(payload, ensure_ascii=False),
            actor="usuario_inline",
        )
        conn.commit()

    with sqlite3.connect(str(bd_temporal)) as conn:
        despues = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        ultima = conn.execute(
            "SELECT categoria, clave, operacion, antes_json, despues_json, actor "
            "FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert despues == antes + 1
    assert ultima[0] == "acerados"
    assert ultima[1] == "test_audit"
    assert ultima[2] == "INSERT"
    assert ultima[3] is None
    assert ultima[5] == "usuario_inline"
    assert json.loads(ultima[4])["label"] == "test_audit"


# ---------------------------------------------------------------------------
# Tarea 2 - aplicacion: insertar_variante_catalogo (validaciones + use case)
# ---------------------------------------------------------------------------

def test_5_insertar_variante_catalogo_ok_acerados(bd_temporal: Path, monkeypatch):
    """Caso feliz: acerados ABA con item valido -> id int + audit +1 fila."""
    from src.infraestructura.db.connection import DB_PATH as MOD_DB_PATH  # noqa
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    with sqlite3.connect(str(bd_temporal)) as conn:
        audit_antes = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    item = {"label": "test_t5", "unidad": "m2", "precio": 18.39}
    nuevo_id = insertar_variante_catalogo(
        "acerados", red="ABA", item=item, actor="usuario_inline",
    )

    assert isinstance(nuevo_id, int)
    assert nuevo_id > 0

    with sqlite3.connect(str(bd_temporal)) as conn:
        fila = conn.execute(
            "SELECT red, label, unidad, precio FROM acerados WHERE id=?",
            (nuevo_id,),
        ).fetchone()
        audit_despues = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        ultima_audit = conn.execute(
            "SELECT actor, operacion FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert fila[0] == "ABA"
    assert fila[1] == "test_t5"
    assert fila[2] == "m2"
    assert fila[3] == 1839  # 18.39 EUR -> 1839 centimos
    assert audit_despues == audit_antes + 1
    assert ultima_audit[0] == "usuario_inline"
    assert ultima_audit[1] == "INSERT"


def test_6_validacion_label_vacio(bd_temporal: Path, monkeypatch):
    """label vacio en tabla cuya unicidad incluye label -> ValueError."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "acerados", red="ABA",
            item={"label": "", "unidad": "m2", "precio": 5.0},
        )
    assert "label" in str(exc.value).lower()


def test_7_validacion_precio_no_positivo(bd_temporal: Path, monkeypatch):
    """precio <= 0 -> ValueError con mensaje que menciona 'precio'."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "acerados", red="ABA",
            item={"label": "test_p0", "unidad": "m2", "precio": 0},
        )
    assert "precio" in str(exc.value).lower()


def test_8a_duplicado_tuberias(bd_temporal: Path, monkeypatch):
    """tuberias: dos INSERT con mismo (red, label) -> el segundo lanza."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    base = {"label": "tubo_dup_X", "tipo": "PE-100",
            "diametro_mm": 90, "precio_m": 12.0}
    insertar_variante_catalogo("tuberias", red="ABA", item=dict(base))

    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "tuberias", red="ABA",
            item={**base, "precio_m": 13.0},  # precio diferente, misma clave
        )
    assert "ya existe" in str(exc.value).lower()


def test_8b_duplicado_acometidas(bd_temporal: Path, monkeypatch):
    """acometidas: clave (red, tipo). Sin label."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    insertar_variante_catalogo(
        "acometidas", red="ABA",
        item={"tipo": "T1_dup", "precio": 100.0},
    )
    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "acometidas", red="ABA",
            item={"tipo": "T1_dup", "precio": 200.0},
        )
    assert "ya existe" in str(exc.value).lower()


def test_8c_duplicado_bordillos_solo_label(bd_temporal: Path, monkeypatch):
    """bordillos: unicidad (label,). Misma label distinto unidad -> dup."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    insertar_variante_catalogo(
        "bordillos", red=None,
        item={"label": "bord_dup_X", "unidad": "m", "precio": 10.0},
    )
    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "bordillos", red=None,
            item={"label": "bord_dup_X", "unidad": "ud", "precio": 11.0},
        )
    assert "ya existe" in str(exc.value).lower()


def test_8d_pozos_no_chequea_duplicado(bd_temporal: Path, monkeypatch):
    """pozos: _CLAVES_UNICIDAD vacia -> el use case no lanza por duplicado."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    item1 = {"label": "pozo_dup_X", "precio": 100.0, "intervalo": 1.0}
    item2 = {"label": "pozo_dup_X", "precio": 110.0, "intervalo": 2.0}

    id1 = insertar_variante_catalogo("pozos", red=None, item=dict(item1))
    id2 = insertar_variante_catalogo("pozos", red=None, item=dict(item2))

    assert id1 != id2
    assert id1 > 0 and id2 > 0


def test_9a_red_obligatoria_para_tuberias(bd_temporal: Path, monkeypatch):
    """tuberias en _TABLAS_CON_RED: red=None -> ValueError."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "tuberias", red=None,
            item={"label": "t9a", "tipo": "PE-100",
                  "diametro_mm": 90, "precio_m": 10.0},
        )
    msg = str(exc.value).lower()
    assert "red" in msg and "tuberias" in msg


def test_9b_red_prohibida_para_valvuleria(bd_temporal: Path, monkeypatch):
    """valvuleria fuera de _TABLAS_CON_RED: red != None -> ValueError."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    with pytest.raises(ValueError) as exc:
        insertar_variante_catalogo(
            "valvuleria", red="ABA",
            item={"label": "v9b", "tipo": "valv", "dn_min": 50, "dn_max": 100,
                  "precio": 100.0, "intervalo_m": 50.0},
        )
    msg = str(exc.value).lower()
    assert "valvuleria" in msg
    assert "no admite red" in msg or "no admite" in msg


def test_9c_acometidas_red_obligatoria_ok(bd_temporal: Path, monkeypatch):
    """acometidas exige red; con red valida e item valido -> OK (no lanza)."""
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    nuevo_id = insertar_variante_catalogo(
        "acometidas", red="ABA",
        item={"tipo": "t9c_unico", "precio": 50.0},
    )
    assert isinstance(nuevo_id, int) and nuevo_id > 0


def test_10_precio_centimos_no_doble_conversion(bd_temporal: Path, monkeypatch):
    """precio=18.39 EUR -> 1839 centimos en BD (NO 18 * 100 * 1.05 = 1890).

    Confirma que el use case persiste BASE; el CI lo aplica el cargador.
    """
    from src.infraestructura.db import connection as conn_mod
    monkeypatch.setattr(conn_mod, "DB_PATH", bd_temporal)

    from src.aplicacion.editar_catalogo import insertar_variante_catalogo

    nuevo_id = insertar_variante_catalogo(
        "acerados", red="ABA",
        item={"label": "test10", "unidad": "m2", "precio": 18.39},
    )
    with sqlite3.connect(str(bd_temporal)) as conn:
        precio_db = conn.execute(
            "SELECT precio FROM acerados WHERE id=?", (nuevo_id,),
        ).fetchone()[0]
    assert precio_db == 1839, (
        f"Esperaba 1839 centimos (BASE), obtuvo {precio_db}. "
        "Indicios de doble conversion o pre-multiplicacion por CI."
    )


def test_11_use_case_no_importa_streamlit():
    """Importar el use case NO debe arrastrar streamlit a sys.modules.

    Cubre frontera arquitectonica (test_fronteras_capas verifica AST; este
    verifica el comportamiento en runtime).
    """
    # Si streamlit ya estaba cargado por otro test, lo desactivamos para
    # detectar import accidental al cargar el modulo del use case.
    sys.modules.pop("streamlit", None)
    # Reimport limpio
    sys.modules.pop("src.aplicacion.editar_catalogo", None)
    import src.aplicacion.editar_catalogo  # noqa: F401

    assert "streamlit" not in sys.modules, (
        "src.aplicacion.editar_catalogo NO debe importar streamlit "
        "(frontera de capas test_fronteras_capas.py)."
    )
