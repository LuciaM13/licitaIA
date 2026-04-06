# Arquitectura del proyecto LicitaIA

Calculadora de presupuestos para obras de EMASESA (Empresa Municipal de Abastecimiento y Saneamiento de Aguas de Sevilla). Aplicacion Streamlit multipage con motor de reglas CLIPS para decisiones de negocio y persistencia en SQLite.

## Diagrama de flujo

```
+---------------------------------------------------------------------+
|                        UI (Streamlit)                                |
|                                                                      |
|  app.py                   Entrypoint: define paginas, init_db()      |
|  pages/calculadora.py     Formulario -> ParametrosProyecto -> calcula|
|  pages/admin_precios.py   Editores de catalogos -> guardar en SQLite |
+----------+------------------------------+---------------------------+
           |                              |
           v                              v
+-----------------------------+   +---------------------------------------+
|   src/precios.py            |   |       src/config.py                   |
|                             |   |                                       |
|  cargar_precios()           |   |  @dataclass ParametrosProyecto        |
|  -> cargar_todo() + CI      |   |  (todo lo que el usuario introduce)   |
|  guardar_precios()          |   |                                       |
|  -> validar + guardar_todo  |   +-------------------+-------------------+
+-----------+-----------------+                       |
            |                                         |
            v                                         v
+-----------------------------+   +---------------------------------------+
|    src/db.py                |   |    src/presupuesto.py                  |
|                             |   |                                       |
|  SQLite schema + CRUD       |   |  calcular_presupuesto(params, precios)|
|  cargar_todo() / guardar    |   |  Orquesta los 9 capitulos:            |
|  Migraciones de schema      |   |   01-02 Obra Civil (ABA/SAN)          |
+-----------------------------+   |   03-04 Pavimentacion                  |
                                  |   05-06 Acometidas                     |
                                  |   07 Seguridad y Salud                 |
                                  |   08 Gestion Ambiental                 |
                                  |   09 Materiales                        |
                                  |  + Resumen financiero (PEM->TOTAL)     |
                                  +---+------------------+-----------------+
                                      |                  |
                       +--------------+                  +--------------+
                       v                                                v
+--------------------------------+         +-----------------------------+
|  src/motor_experto.py          |         |  src/calcular.py            |
|                                |         |                             |
|  resolver_decisiones()         |         |  Geometria de zanja         |
|  -> Crea entorno CLIPS         |         |  (formulas Excel EMASESA)   |
|  -> Carga catalogos como       |         |                             |
|     hechos CLIPS               |         |  capitulo_obra_civil_red    |
|  -> Ejecuta reglas de          |         |  capitulo_pozos_registro    |
|     elegibilidad               |         |  capitulo_valvuleria        |
|  -> Devuelve decisiones dict   |         |  capitulo_demolicion        |
|                                |         |  capitulo_pavimentacion     |
|  Decide:                       |         |  capitulo_acometidas        |
|   - factor_piezas              |         |  capitulo_desmontaje        |
|   - entibacion (si/no + item)  |         |  capitulo_imbornales        |
|   - pozo de registro           |         |  capitulo_canones           |
|   - valvuleria (lista)         |         +-----------------------------+
|   - desmontaje                 |
+---+---------------+------------+
    |               |
    v               v
+-------------+  +--------------------+
|normalizacion|  | desempates.py      |
|   .py       |  |                    |
|             |  | desempatar_entib.  |
|FACTORES_PIEZAS| desempatar_pozo   |
|NULL_SENTINEL|  | ordenar_valvuleria |
|normalizar_  |  | desempatar_desm.   |
| tipo/red/   |  |                    |
| instalacion |  +--------------------+
+-------------+
```

## Flujo de una peticion de calculo

1. **Usuario** rellena formulario en `pages/calculadora.py` y construye un `ParametrosProyecto`.
2. **`presupuesto.py`** recibe `(params, precios)` y orquesta todo:
   - Llama a `motor_experto.resolver_decisiones()` una vez por red activa (ABA y/o SAN).
   - El motor CLIPS filtra candidatos elegibles; `desempates.py` resuelve cual gana.
   - Con las decisiones, llama a las funciones de `calcular.py` para cada capitulo.
   - Ensambla los 9 capitulos y calcula PEM -> GG -> BI -> PBL -> IVA -> TOTAL.
3. **`calculadora.py`** muestra resultados.

## Modulos de `src/`

| Modulo | Responsabilidad | Lineas |
|--------|----------------|--------|
| `db.py` | Persistencia SQLite (schema, CRUD, migraciones) | 626 |
| `precios.py` | Carga con cache, validacion, escalado de costes indirectos | 237 |
| `config.py` | Modelo de datos (dataclass `ParametrosProyecto`) | 74 |
| `motor_experto.py` | Decisiones de negocio via CLIPS (elegibilidad) | 384 |
| `normalizacion.py` | Constantes de dominio, normalizacion de inputs | 48 |
| `desempates.py` | Ranking y tiebreaking de candidatos (funciones puras) | 97 |
| `calcular.py` | Geometria de zanja y calculo de partidas por capitulo | 464 |
| `presupuesto.py` | Ensamblaje de capitulos y resumen financiero | 453 |
| `utils.py` | Formateo, busqueda en catalogos, exportacion a Word | 73 |
| `diff_precios.py` | Calculo de diff para confirmacion de guardado (admin) | 256 |

## Paginas Streamlit

| Archivo | Responsabilidad | Lineas |
|---------|----------------|--------|
| `app.py` | Entrypoint multipage, `init_db()`, navegacion | 33 |
| `pages/calculadora.py` | Formulario de inputs, construccion de `ParametrosProyecto`, display | 448 |
| `pages/admin_precios.py` | Editores de catalogos, confirmacion con diff, guardado | 549 |

## Regla de diseno clave

**CLIPS decide que es elegible, Python decide quien gana entre los elegibles, y `presupuesto.py` solo consume decisiones — nunca re-filtra catalogos.**

Esto evita la duplicacion de logica de elegibilidad entre el motor de reglas y el ensamblaje del presupuesto.

## Separacion CLIPS vs Python

- **CLIPS (reglas en `motor_experto.py`)**: Filtra candidatos que cumplen condiciones de negocio (red, diametro, profundidad, instalacion). Responde a la pregunta *"que items son elegibles?"*.
- **Python (`desempates.py`)**: Resuelve el ranking entre candidatos elegibles con criterios de especificidad. Responde a la pregunta *"de los elegibles, cual es el mejor?"*.
- **Python (`calcular.py`)**: Calcula importes usando los items ya decididos. Responde a la pregunta *"cuanto cuesta?"*.

## Decisiones del motor experto

`resolver_decisiones()` devuelve un dict con 5 decisiones:

```python
{
    "factor_piezas": float,          # Por tipo de tuberia (FD=1.2, Gres=1.35, etc.)
    "entibacion": {
        "necesaria": bool,           # Profundidad > umbral?
        "item": dict | None,         # Item de entibacion seleccionado
    },
    "pozo_registro": {
        "item": dict | None,         # Pozo mas especifico (red > prof_max > dn_max)
    },
    "valvuleria": {
        "items": list[dict],         # Todos los elegibles, en orden de catalogo
    },
    "desmontaje": {
        "item": dict | None,         # Menor dn_max que cumpla
    },
}
```

## Estructura de capitulos del presupuesto

```
01  OBRA CIVIL ABASTECIMIENTO   Excavacion, tuberia, arrinonado, relleno,
                                carga, transporte, entibacion, pozos,
                                valvuleria, desmontaje, canones
02  OBRA CIVIL SANEAMIENTO      Idem + imbornales, pozos existentes SAN
03  PAVIMENTACION ABASTECIMIENTO Demolicion + reposicion acerado/bordillo + sub-base
04  PAVIMENTACION SANEAMIENTO   Demolicion + reposicion calzada/acera + sub-base
05  ACOMETIDAS ABASTECIMIENTO
06  ACOMETIDAS SANEAMIENTO
07  SEGURIDAD Y SALUD            % sobre capitulos 01-06 (sin canones/desmontaje)
08  GESTION AMBIENTAL            % sobre capitulos 01-06 (sin canones/desmontaje)
09  MATERIALES                   Suministro puro ABA (excluido de GG/BI)
```

## Resumen financiero (alineado con Excel EMASESA)

```
PEM         = suma capitulos 01-09
base GG/BI  = PEM - MATERIALES
GG          = base_GG/BI x pct_gg
BI          = base_GG/BI x pct_bi
PBL sin IVA = ROUNDUP((PEM + GG + BI) / 10) x 10
IVA         = PBL x pct_iva
TOTAL       = PBL + IVA
```

## Persistencia

- **SQLite** (`data/precios.db`): Schema relacional con FK constraints. Gestionado por `src/db.py`.
- **Cache Streamlit** (`@st.cache_data`): `cargar_precios()` cachea 60s; se invalida con `.clear()` tras guardar.
- **Costes indirectos (CI)**: Se almacenan precios base en SQLite. Al cargar, `_aplicar_ci()` multiplica todos los precios por el factor CI (`pct_ci`). El admin siempre edita precios base.

## Tests

```
tests/
  conftest.py             Fixture session-scoped `precios` (cargar_todo sin CI)
  test_motor_experto.py   14 tests del motor CLIPS (casos A-J)
  test_presupuesto.py     6 regresiones contra verify_baseline.json
```

Ejecutar: `python -m pytest tests/ -v`
