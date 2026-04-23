"""Tests que verifican que la capa de infraestructura no depende de Streamlit.

Cubre:
  - ``src/infraestructura/precios.py`` no importa ``streamlit`` (Paso 2 B3).
  - ``cargar_precios()`` funciona en un subproceso donde ``streamlit`` no está
    importado, confirmando que se puede ejecutar desde un script CLI sin
    levantar Streamlit.
  - ``PRAGMA journal_mode = WAL`` está activo tras ``conectar()`` (Paso 2 R2).
  - Una conexión lectora no se bloquea mientras otra conexión escribe
    (smoke de concurrencia WAL, acotado a lector-mientras-escribe; WAL sigue
    serializando escrituras).

Excepción a la regla "solo AppTest": valida invariantes de infraestructura
pura sin superficie Streamlit. Ver AGENTS.md.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from src.infraestructura.db import DB_PATH, conectar


_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# B3 — Infraestructura no importa Streamlit
# ---------------------------------------------------------------------------

def test_precios_infraestructura_no_importa_streamlit():
    """El AST de ``precios.py`` no debe contener ningún ``import streamlit``."""
    fichero = _REPO_ROOT / "src" / "infraestructura" / "precios.py"
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    imports_streamlit = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name.split(".")[0] == "streamlit":
                    imports_streamlit.append(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            if (nodo.module or "").split(".")[0] == "streamlit":
                imports_streamlit.append(nodo.module)
    assert not imports_streamlit, (
        f"src/infraestructura/precios.py importa streamlit: {imports_streamlit}. "
        "La capa de infraestructura debe ser pura; el cache UI vive en src/ui/."
    )


def test_cargar_precios_funciona_sin_streamlit_en_subproceso():
    """Lanza un subproceso que importa y ejecuta ``cargar_precios()`` asegurándose
    de que ``streamlit`` NO esté en ``sys.modules`` en el momento de llamar.

    Simula el escenario "script CLI de simulación masiva" sin levantar la app.
    """
    script = (
        "import sys\n"
        "assert 'streamlit' not in sys.modules, 'streamlit ya está cargado antes del import'\n"
        "from src.infraestructura.precios import cargar_precios\n"
        "assert 'streamlit' not in sys.modules, 'precios.py cargó streamlit transitivamente'\n"
        "precios = cargar_precios()\n"
        "assert 'pct_ci' in precios\n"
        "assert precios['catalogo_aba'], 'catalogo_aba vacío'\n"
        "print('OK')\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert resultado.returncode == 0, (
        f"Subproceso falló:\nstdout={resultado.stdout}\nstderr={resultado.stderr}"
    )
    assert "OK" in resultado.stdout


# ---------------------------------------------------------------------------
# R2 — WAL activo y concurrencia lector-mientras-escribe
# ---------------------------------------------------------------------------

def test_conectar_activa_wal():
    """Tras ``conectar()`` SQLite debe reportar ``journal_mode=wal``."""
    with conectar() as conn:
        modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert modo.lower() == "wal", f"journal_mode esperado 'wal', obtuvo '{modo}'"


def test_lector_no_se_bloquea_mientras_otra_conexion_escribe():
    """Smoke test de concurrencia WAL.

    Abre dos conexiones sobre la misma BD. Una escribe dentro de una
    transacción larga; la otra lee. En modo WAL la lectura no debe bloquearse
    con ``database is locked``. El test NO pretende probar dos escritores
    concurrentes (WAL sigue serializando escrituras).
    """
    error_lector: dict = {}
    escritura_completada = threading.Event()

    def escribir():
        # Abre una conexión separada al mismo fichero y mantiene una transacción
        # abierta durante 500 ms.
        conn = None
        try:
            with conectar() as conn:
                conn.execute("BEGIN IMMEDIATE")
                # Escritura sintética sobre una tabla inocua (schema_version existe).
                # La mantenemos sin commit para simular una transacción lenta.
                conn.execute(
                    "CREATE TEMP TABLE IF NOT EXISTS _wal_smoke_tmp (x INTEGER)"
                )
                conn.execute("INSERT INTO _wal_smoke_tmp (x) VALUES (1)")
                time.sleep(0.3)
                conn.execute("ROLLBACK")
        except Exception as exc:  # no se espera, pero si pasa, el test lo verá
            error_lector["escritor"] = repr(exc)
        finally:
            escritura_completada.set()

    def leer():
        try:
            # Pequeña espera para que el escritor tome la transacción primero.
            time.sleep(0.05)
            with conectar() as conn:
                filas = conn.execute(
                    "SELECT COUNT(*) FROM schema_version"
                ).fetchone()
                assert filas[0] >= 0
        except Exception as exc:
            error_lector["lector"] = repr(exc)

    t_escritor = threading.Thread(target=escribir)
    t_lector = threading.Thread(target=leer)
    t_escritor.start()
    t_lector.start()
    t_escritor.join(timeout=5)
    t_lector.join(timeout=5)
    escritura_completada.wait(timeout=5)

    assert not error_lector, (
        "La lectura no debe bloquearse mientras otra conexión escribe (WAL). "
        f"Errores: {error_lector}"
    )
