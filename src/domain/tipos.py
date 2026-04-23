"""TypedDict para los contratos internos de dominio.

Estos tipos documentan el shape de los diccionarios que circulan por el
cálculo de presupuestos. Son transparentes en runtime (``TypedDict`` son
``dict``) y solo aportan verificación estática vía pyright/mypy.

Alcance acotado (Paso 5 del refactor de Fase 2): el objetivo es detectar
errores de *claves inexistentes* en los tipos aquí introducidos, no
endurecer todo el tipado del proyecto. Warnings sobre ``Any``, opcionales
sin anotar o campos no declarados del resto del código quedan fuera de
alcance y se consideran trabajo futuro.
"""

from __future__ import annotations

from typing import Any, TypedDict


# ---------------------------------------------------------------------------
# Item de catálogo (shape amplio con todos los campos opcionales)
# ---------------------------------------------------------------------------

class ItemCatalogo(TypedDict, total=False):
    """Shape unificado de una fila de catálogo (tuberías, pozos, valvulería, etc.).

    Todos los campos son opcionales (``total=False``) porque el mismo alias
    ``ItemCatalogo`` se usa para varios tipos de item con shapes distintos:

    - **Tubería** (``catalogo_aba``/``catalogo_san``): label, precio_m, tipo,
      diametro_mm, factor_piezas, precio_material_m, red.
    - **Pozo** (``catalogo_pozos``): label, precio, intervalo, red,
      profundidad_max, dn_max, precio_tapa, precio_tapa_material,
      precio_pate_material.
    - **Valvulería** (``catalogo_valvuleria``): label, tipo, dn_min, dn_max,
      precio, intervalo_m, instalacion, factor_piezas, precio_material.
    - **Entibación** (``catalogo_entibacion``): label, precio_m2, umbral_m, red.
    - **Acerado / Bordillo / Calzada**: label, unidad, precio, factor_ci, red.
    - **Demolición**: red, label, unidad, material, precio, factor_ci.
    - **Desmontaje**: label, dn_max, precio_m, es_fibrocemento.
    - **Imbornal**: label, precio, tipo.
    - **Subbase**: label, precio_m3.
    - **Pozos existentes**: red, accion, precio, intervalo_m.

    Campos frecuentemente usados como identificador:
    """
    # Identificación
    label: str
    tipo: str
    red: str | None
    unidad: str
    material: str
    # Diámetros y rangos
    diametro_mm: int
    dn_min: int
    dn_max: int
    dn_max_field: int  # alias técnico no usado; el campo real es dn_max
    profundidad_max: float | None
    umbral_m: float
    intervalo: float
    intervalo_m: float
    # Precios (€ en runtime; cents en BD)
    precio: float
    precio_m: float
    precio_m2: float
    precio_m3: float
    precio_material: float
    precio_material_m: float
    precio_tapa: float
    precio_tapa_material: float
    precio_pate_material: float
    # Factores
    factor_piezas: float
    factor_ci: float
    # Banderas
    es_fibrocemento: int
    instalacion: str | None
    # Campos específicos (pozos existentes, etc.)
    accion: str


# ---------------------------------------------------------------------------
# Dict raíz de precios devuelto por ``cargar_precios()``
# ---------------------------------------------------------------------------

class Precios(TypedDict, total=False):
    """Shape del dict raíz que ``cargar_precios()`` devuelve.

    Contiene catálogos (listas de ``ItemCatalogo``) y escalares de configuración.
    Marcado ``total=False`` porque no todos los catálogos están siempre poblados
    (p.ej. ``catalogo_subbases`` puede estar vacío en proyectos sin pavimentación).
    """
    # Configuración financiera y CI
    pct_gg: float
    pct_bi: float
    pct_iva: float
    pct_ci: float
    pct_manual_defecto: float
    factor_esponjamiento: float
    # Catálogos de obra civil
    catalogo_aba: list[ItemCatalogo]
    catalogo_san: list[ItemCatalogo]
    catalogo_entibacion: list[ItemCatalogo]
    catalogo_pozos: list[ItemCatalogo]
    catalogo_valvuleria: list[ItemCatalogo]
    catalogo_desmontaje: list[ItemCatalogo]
    catalogo_imbornales: list[ItemCatalogo]
    catalogo_subbases: list[ItemCatalogo]
    catalogo_pozos_existentes: list[ItemCatalogo]
    # Catálogos de superficie
    acerados_aba: list[ItemCatalogo]
    acerados_san: list[ItemCatalogo]
    bordillos_reposicion: list[ItemCatalogo]
    calzadas_reposicion: list[ItemCatalogo]
    demolicion_aba: list[ItemCatalogo]
    demolicion_san: list[ItemCatalogo]
    acometidas_aba_tipos: dict[str, float]
    acometidas_san_tipos: dict[str, float]
    acometida_aba_defecto: str
    acometida_san_defecto: str
    espesores_calzada: dict[str, float]
    excavacion: dict[str, float]
    # Escalares sueltos
    conduccion_provisional_precio_m: float
    # Defaults UI
    defaults_ui: dict[str, float]
    # Config cruda (diccionario por clave)
    config: dict[str, float]


# ---------------------------------------------------------------------------
# Resultado de ``calcular_presupuesto()``
# ---------------------------------------------------------------------------

class CapituloResultado(TypedDict):
    """Un capítulo dentro del resultado del presupuesto."""
    subtotal: float
    partidas: dict[str, float]


class PctsFinancieros(TypedDict):
    """Porcentajes financieros aplicados en el cálculo."""
    gg: float
    bi: float
    iva: float


class ResultadoPresupuesto(TypedDict, total=False):
    """Shape del dict devuelto por ``calcular_presupuesto()``.

    Consumido por ``pages/calculadora.py`` y ``pages/historial.py``; sus
    claves son parte del contrato del snapshot persistido en la tabla
    ``presupuestos`` de la BD.
    """
    capitulos: dict[str, CapituloResultado]
    pem: float
    gg: float
    bi: float
    pbl_sin_iva: float
    iva: float
    total: float
    pcts: PctsFinancieros
    pct_seguridad_info: float
    pct_gestion_info: float
    auxiliares: dict[str, Any]
    # Explicaciones narrativas por red (la clave conserva su nombre histórico
    # ``trazabilidad`` para no romper el historial persistido, aunque el
    # contenido se genera en ``src.reglas.explicaciones``).
    trazabilidad: dict[str, list[str]]
