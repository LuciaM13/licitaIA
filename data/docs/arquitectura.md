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

| Modulo | Responsabilidad |
|--------|----------------|
| `db.py` | Persistencia SQLite (schema, CRUD, migraciones) |
| `precios.py` | Carga con cache, validacion, escalado de costes indirectos |
| `config.py` | Modelo de datos (dataclass `ParametrosProyecto`) |
| `motor_experto.py` | Decisiones de negocio via CLIPS (elegibilidad) |
| `normalizacion.py` | Constantes de dominio, normalizacion de inputs |
| `desempates.py` | Ranking y tiebreaking de candidatos (funciones puras) |
| `calcular.py` | Geometria de zanja y calculo de partidas por capitulo |
| `presupuesto.py` | Ensamblaje de capitulos y resumen financiero |
| `utils.py` | Formateo, busqueda en catalogos, exportacion a Word |
| `diff_precios.py` | Calculo de diff para confirmacion de guardado (admin) |

## Paginas Streamlit

| Archivo | Responsabilidad |
|---------|----------------|
| `app.py` | Entrypoint multipage, `init_db()`, navegacion |
| `pages/calculadora.py` | Formulario de inputs, construccion de `ParametrosProyecto`, display |
| `pages/admin_precios.py` | Editores de catalogos, confirmacion con diff, guardado |

## Fundamentacion: sistema experto como paradigma de IA

### Que es un sistema experto

Un sistema experto es una rama de la inteligencia artificial que replica el razonamiento de un especialista humano en un dominio concreto. A diferencia de un programa convencional que ejecuta instrucciones secuenciales, un sistema experto **razona** sobre un conjunto de hechos aplicando reglas de conocimiento para llegar a conclusiones. Esta capacidad de razonamiento automatico es lo que lo distingue de la programacion clasica y lo situa dentro de la IA.

Los sistemas expertos nacen en los anos 60-70 como una de las primeras aplicaciones exitosas de la IA (MYCIN para diagnostico medico, DENDRAL para quimica analitica, R1/XCON para configuracion de hardware). Representan el enfoque **simbolico** de la IA: en lugar de aprender de datos (como hace el machine learning), codifican el conocimiento de expertos humanos en forma de reglas explicitas y lo aplican mediante inferencia logica.

### Arquitectura canonica de un sistema experto

Todo sistema experto se compone de tres elementos:

```
+---------------------+     +---------------------+     +---------------------+
|   BASE DE HECHOS    |     | BASE DE CONOCIMIENTO|     | MOTOR DE INFERENCIA |
|                     |     |                      |     |                     |
| Datos del caso      |     | Reglas del dominio   |     | Algoritmo que       |
| concreto que se     |     | expresadas como      |     | evalua las reglas   |
| esta evaluando.     |     | IF...THEN            |     | contra los hechos   |
|                     |     | declarativas.        |     | y genera nuevos     |
| Aqui: parametros    |     |                      |     | hechos (candidatos  |
| del proyecto +      |     | Aqui: reglas de      |     | elegibles).         |
| catalogos EMASESA.  |     | elegibilidad de      |     |                     |
|                     |     | materiales.          |     | Aqui: CLIPS (RETE). |
+---------------------+     +---------------------+     +---------------------+
```

- **Base de hechos**: los datos del problema particular. En LicitaIA: tipo de tuberia, diametro, red (ABA/SAN), profundidad de zanja, tipo de instalacion, y los catalogos completos de materiales de EMASESA.
- **Base de conocimiento**: las reglas del dominio expresadas de forma declarativa. En LicitaIA: "un item de entibacion es elegible si su red coincide con la del proyecto Y la profundidad supera su umbral". Estas reglas codifican el criterio que aplicaria un ingeniero de EMASESA.
- **Motor de inferencia**: el componente que ejecuta el ciclo de razonamiento. Toma los hechos, evalua las reglas, y genera conclusiones (nuevos hechos). LicitaIA usa CLIPS, que implementa el algoritmo Rete — un algoritmo de pattern-matching optimizado para evaluar eficientemente muchas reglas contra muchos hechos simultaneamente.

### Por que es inteligencia artificial

Un sistema experto es IA porque realiza una tarea que, sin el, requeriria inteligencia humana: **tomar decisiones en un dominio especializado aplicando razonamiento**. No se limita a calcular — razona. La diferencia es fundamental:

- **Calcular**: dada una formula y unos datos, producir un resultado numerico. No hay decision, solo aritmetica. Ejemplo: "volumen de excavacion = ancho × profundidad × longitud".
- **Razonar**: dado un conjunto de condiciones y restricciones, determinar que opciones son validas y cual es la mejor. Hay juicio, hay eliminacion de candidatos, hay resolucion de conflictos. Ejemplo: "de los 15 tipos de pozo del catalogo, solo 3 aplican para esta red, este diametro y esta profundidad; de esos 3, el mas especifico es este".

El sistema experto automatiza el segundo tipo de tarea. Sin el, un ingeniero tendria que revisar mentalmente cada item del catalogo, comprobar si cumple las condiciones del proyecto, y elegir el mas adecuado. El motor de inferencia replica ese proceso de razonamiento.

### Contraste con el enfoque de calculo directo

Antes de la implementacion del sistema experto, la logica de seleccion de materiales estaba resuelta con codigo Python procedural: filtrados con pandas/NumPy, condicionales encadenados (`if`/`elif`), y busquedas secuenciales en listas. Funcionalmente producia el mismo resultado, pero con diferencias criticas:

| Aspecto | Calculo directo (pandas/NumPy) | Sistema experto (CLIPS) |
|---------|-------------------------------|------------------------|
| **Representacion del conocimiento** | Implicita en el codigo (dispersa entre `if`, `for`, `filter`) | Explicita en reglas declarativas (`defrule`) |
| **Separacion de concerns** | La logica de decision y el calculo numerico comparten modulo | La decision (CLIPS) y el calculo (`calcular.py`) son independientes |
| **Mantenimiento de reglas** | Modificar una regla obliga a editar funciones Python con riesgo de efectos colaterales | Anadir o modificar una regla es declarativo y aislado |
| **Auditabilidad** | Dificil trazar por que se eligio un material concreto | Cada candidato elegible queda registrado como hecho CLIPS; el razonamiento es trazable |
| **Naturaleza** | Programa que calcula | Programa que razona y luego calcula |

El calculo directo es adecuado para geometria de zanja, volumenes, e importes — problemas con formula cerrada y sin ambiguedad. La seleccion de materiales, en cambio, es un problema de **decision bajo restricciones**: multiples candidatos, multiples criterios, reglas que interactuan entre si. Este tipo de problema es el dominio natural de los sistemas expertos.

### Implementacion en LicitaIA: CLIPS + Python hibrido

LicitaIA adopta una arquitectura hibrida que separa razonamiento y calculo en capas distintas:

```
Razonamiento (IA)          Ranking (algoritmico)       Calculo (numerico)
motor_experto.py           desempates.py               calcular.py
     |                          |                           |
     | CLIPS evalua reglas      | Python ordena por         | Formulas Excel
     | de elegibilidad y        | especificidad y           | EMASESA: vol.,
     | marca candidatos         | resuelve empates          | importes, canon
     | validos                  | entre elegibles           |
     |                          |                           |
     v                          v                           v
  "Que items son            "De los elegibles,          "Cuanto cuesta?"
   elegibles?"               cual es el mejor?"
```

CLIPS (C Language Integrated Production System) es un shell de sistemas expertos desarrollado por la NASA en 1985. Se selecciona por ser el estandar academico e industrial de referencia para sistemas basados en reglas, con bindings nativos a Python (`clipspy`).

El ciclo de razonamiento en cada consulta:

1. Se crea un entorno CLIPS limpio (sin estado residual de consultas anteriores).
2. Se cargan los **templates** (esquema de los hechos: datos-tuberia, item-entibacion, etc.).
3. Se cargan las **reglas** de elegibilidad (defrule).
4. Se insertan los **hechos** del caso concreto (parametros del proyecto + catalogos EMASESA).
5. Se ejecuta `env.run()` — el motor de inferencia evalua todas las reglas contra todos los hechos y genera hechos derivados (candidatos elegibles).
6. Python recoge los candidatos elegibles y aplica criterios de desempate (funciones puras en `desempates.py`).
7. Se destruye el entorno CLIPS.

Este ciclo se ejecuta una vez por cada red activa (ABA y/o SAN), produciendo un diccionario de decisiones que `presupuesto.py` consume sin necesidad de conocer como se tomaron.

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
  test_presupuesto.py     6 regresiones contra tests/verify_baseline.json
  verify_baseline.json    Baselines de regresion (golden file)
```

Ejecutar: `python -m pytest tests/ -v`
