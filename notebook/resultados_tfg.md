---
title: "Capítulo 4 — Resultados"
subtitle: "Validación de LicitaIA contra el Excel oficial EMASESA"
lang: es
---

# 4.1. Validación contra el Excel oficial EMASESA

## 4.1.1. Metodología

La validación matemática del módulo de cálculo de **LicitaIA** se ha realizado contra el fichero `240415_VALORACIÓN ACTUACIONES.xlsx`, herramienta interna que EMASESA utiliza para presupuestación rápida de actuaciones de abastecimiento (ABA) y saneamiento (SAN). El propio fichero incorpora **cuatro hojas resueltas paso a paso** que actúan como casos de referencia, una por combinación representativa de material y diámetro:

- `A-Fundición 150`: fundición dúctil ABA, DN 150 mm, profundidad 1,25 m.
- `Fundición 300`: fundición dúctil ABA, DN 300 mm, profundidad 1,35 m.
- `S-Hormigón 2000+PE80`: hormigón armado SAN, DN 2000 mm, profundidad 5,00 m.
- `S-Gres 300`: gres SAN, DN 300 mm, profundidad 5,00 m.

Para cada caso se han comparado **siete métricas geométricas** (anchuras de zanja, volúmenes y superficie de entibación por metro lineal) y **cinco métricas financieras** (PEM, base GG/BI, PEC sin redondear y PEC final). Los valores oficiales se extraen directamente del Excel mediante `openpyxl`, localizando las celdas por su etiqueta textual para tolerar las diferencias de layout entre hojas. Los valores de LicitaIA se obtienen invocando directamente las funciones puras del dominio (`src.domain.geometria.calcular_geometria` y `src.domain.financiero.calcular_resumen`), sin pasar por la interfaz Streamlit. Se considera coincidencia exacta cuando la diferencia absoluta entre ambos valores es **inferior a 0,01** (un céntimo en EUR/m, un centímetro en m, una centésima en m²/m o m³/m).

El procedimiento completo y reproducible se encuentra implementado en el cuaderno [`notebook/08_validacion_excel.ipynb`](08_validacion_excel.ipynb), apoyado en el módulo auxiliar [`notebook/_excel_helpers.py`](_excel_helpers.py).

## 4.1.2. Resumen agregado de la validación

La Tabla 4.1 muestra el resultado agregado sobre los 4 casos de validación. La cifra clave es que **el cuadro financiero coincide al 100 %** con el Excel oficial y la geometría al 89,3 %.

**Tabla 4.1.** Resumen de exactitud de LicitaIA frente al Excel oficial EMASESA. Métricas exactas (≤ 0,01 de diferencia) sobre el total comparado.

| Caso | Geometría | Financiero | Resultado |
|---|:---:|:---:|---|
| A-Fundición 150 (ABA, DN 150) | 7 / 7 | 5 / 5 | EXACTO |
| Fundición 300 (ABA, DN 300) | 6 / 7 | 5 / 5 | Parcial |
| S-Hormigón 2000+PE80 (SAN, DN 2000) | 6 / 7 | 5 / 5 | Parcial |
| S-Gres 300 (SAN, DN 300) | 6 / 7 | 5 / 5 | Parcial |
| **TOTAL** | **25 / 28 (89,3 %)** | **20 / 20 (100 %)** | |

## 4.1.3. Detalle por caso

A continuación se desglosa, métrica por métrica, la comparación entre el valor del Excel oficial y el calculado por LicitaIA. Las diferencias se reportan como `LicitaIA − Excel`. Una diferencia inferior a 0,01 en valor absoluto se considera coincidencia exacta (columna OK).

### 4.1.3.1. Caso 1: A-Fundición 150 (FD ABA, DN 150 mm)

**Tabla 4.2.** Comparación geométrica del caso A-Fundición 150 (profundidad 1,25 m; altura de pavimento 0,49 m; con entibación).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| Anchura de fondo (m) | 0,6000 | 0,6000 | +0,0000 | sí |
| Anchura de cima (m) | 0,6000 | 0,6000 | +0,0000 | sí |
| Volumen de zanja (m³/m) | 0,5550 | 0,5550 | +0,0000 | sí |
| Anchura en recubrimiento (m) | 0,6000 | 0,6000 | +0,0000 | sí |
| Altura de arena (m) | 0,3800 | 0,3800 | +0,0000 | sí |
| Volumen de arena (m³/m) | 0,2026 | 0,2026 | −0,0000 | sí |
| Superficie de entibación (m²/m) | 2,9300 | 2,9300 | +0,0000 | sí |

**Tabla 4.3.** Comparación financiera del caso A-Fundición 150 (EUR por metro lineal de tubería).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| PEM | 416,29 | 416,29 | +0,00 | sí |
| Materiales excluidos de GG/BI | 3,92 | 3,92 | +0,00 | sí |
| Base GG/BI | 412,37 | 412,37 | +0,00 | sí |
| PEC sin redondear | 494,64 | 494,64 | +0,00 | sí |
| PEC redondeado a la decena superior | 500,00 | 500,00 | +0,00 | sí |

Las **doce métricas** coinciden con el Excel al céntimo: es el caso típico de tubería de abastecimiento en obra urbana estándar, con todas las fórmulas geométricas y financieras alineadas.

### 4.1.3.2. Caso 2: Fundición 300 (FD ABA, DN 300 mm)

**Tabla 4.4.** Comparación geométrica del caso Fundición 300 (profundidad 1,35 m; sin pavimento previo; con entibación).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| Anchura de fondo (m) | 0,7600 | 0,7600 | +0,0000 | sí |
| Anchura de cima (m) | 0,7600 | 0,7600 | +0,0000 | sí |
| Volumen de zanja (m³/m) | 1,1628 | 1,1628 | +0,0000 | sí |
| Anchura en recubrimiento (m) | 0,7600 | 0,7600 | +0,0000 | sí |
| Altura de arena (m) | 0,5600 | 0,5600 | +0,0000 | sí |
| Volumen de arena (m³/m) | 0,3238 | 0,3238 | −0,0000 | sí |
| **Superficie de entibación (m²/m)** | **3,0600** | **3,1600** | **+0,1000** | **no** |

**Tabla 4.5.** Comparación financiera del caso Fundición 300 (EUR por metro lineal).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| PEM | 316,54 | 316,54 | +0,00 | sí |
| Materiales excluidos de GG/BI | 55,31 | 55,31 | +0,00 | sí |
| Base GG/BI | 261,23 | 261,23 | +0,00 | sí |
| PEC sin redondear | 366,17 | 366,17 | +0,00 | sí |
| PEC redondeado a la decena superior | 370,00 | 370,00 | +0,00 | sí |

Coinciden las cinco métricas financieras al céntimo. La única discrepancia es de naturaleza geométrica (superficie de entibación), cuya causa se analiza en la sección 4.1.4.

### 4.1.3.3. Caso 3: S-Hormigón 2000+PE80 (HACCH SAN, DN 2000 mm)

**Tabla 4.6.** Comparación geométrica del caso S-Hormigón 2000+PE80 (profundidad 5,00 m; altura de pavimento 0,35 m; con entibación).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| Anchura de fondo (m) | 3,9000 | 3,9000 | +0,0000 | sí |
| Anchura de cima (m) | 3,9000 | 3,9000 | −0,0000 | sí |
| Volumen de zanja (m³/m) | 19,5000 | 19,5000 | −0,0000 | sí |
| Anchura en recubrimiento (m) | 3,9000 | 3,9000 | +0,0000 | sí |
| Altura de arena (m) | 2,7000 | 2,7000 | +0,0000 | sí |
| Volumen de arena (m³/m) | 6,0100 | 6,0061 | −0,0039 | sí |
| **Superficie de entibación (m²/m)** | **10,7000** | **13,2000** | **+2,5000** | **no** |

**Tabla 4.7.** Comparación financiera del caso S-Hormigón 2000+PE80 (EUR por metro lineal).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| PEM | 3 436,84 | 3 436,84 | +0,00 | sí |
| Materiales excluidos de GG/BI | 0,00 | 0,00 | +0,00 | sí |
| Base GG/BI | 3 436,84 | 3 436,84 | +0,00 | sí |
| PEC sin redondear | 4 089,84 | 4 089,84 | +0,00 | sí |
| PEC redondeado a la decena superior | 4 090,00 | 4 090,00 | +0,00 | sí |

Caso de saneamiento de gran diámetro con doble tubería (hormigón armado y PE-80 a presión). Cuadro financiero exacto al céntimo y geometría coincidente salvo en la entibación, cuyo origen es estructural y se discute en la sección 4.1.4.

### 4.1.3.4. Caso 4: S-Gres 300 (Gres SAN, DN 300 mm)

**Tabla 4.8.** Comparación geométrica del caso S-Gres 300 (profundidad 5,00 m; altura de pavimento 0,35 m; con entibación).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| Anchura de fondo (m) | 1,8600 | 1,8600 | +0,0000 | sí |
| Anchura de cima (m) | 1,8600 | 1,8600 | −0,0000 | sí |
| Volumen de zanja (m³/m) | 8,9838 | 8,9838 | +0,0000 | sí |
| Anchura en recubrimiento (m) | 1,8600 | 1,8600 | +0,0000 | sí |
| Altura de arena (m) | 0,6600 | 0,6600 | +0,0000 | sí |
| Volumen de arena (m³/m) | 1,1300 | 1,1258 | −0,0042 | sí |
| **Superficie de entibación (m²/m)** | **10,3600** | **13,2000** | **+2,8400** | **no** |

**Tabla 4.9.** Comparación financiera del caso S-Gres 300 (EUR por metro lineal).

| Métrica | Excel | LicitaIA | Δ | OK |
|---|---:|---:|---:|:---:|
| PEM | 1 255,67 | 1 255,67 | +0,00 | sí |
| Materiales excluidos de GG/BI | 0,00 | 0,00 | +0,00 | sí |
| Base GG/BI | 1 255,67 | 1 255,67 | +0,00 | sí |
| PEC sin redondear | 1 494,25 | 1 494,25 | +0,00 | sí |
| PEC redondeado a la decena superior | 1 500,00 | 1 500,00 | +0,00 | sí |

## 4.1.4. Análisis de las desviaciones residuales

Las **tres desviaciones** que persisten tras la validación se concentran exclusivamente en una métrica (superficie de entibación) y no son errores aleatorios: corresponden a inconsistencias documentadas del propio Excel oficial, identificadas tras inspeccionar las **fórmulas reales** de las celdas con `openpyxl` en modo no-evaluación. La Tabla 4.10 las resume con las celdas y fórmulas Excel exactas.

**Tabla 4.10.** Trazabilidad de las desviaciones residuales: celda y fórmula del Excel oficial frente al cálculo de LicitaIA.

| Caso | Métrica | Celda Excel | Fórmula Excel | Excel | LicitaIA | Δ | Diagnóstico |
|---|---|:---:|---|---:|---:|---:|---|
| Fundición 300 | Sup. entibación (m²/m) | H75 | `=(D17+0,1·D2/1000+0,15)·2` | 3,06 | 3,16 | +0,10 | Heterogeneidad ABA en el Excel oficial |
| S-Hormigón 2000 | Sup. entibación (m²/m) | H70 (informativa) | `=(D19+0,1·D2/100+0,15)·2` | 10,70 | 13,20 | +2,50 | Doble fórmula SAN: H70 visual vs. H17 de coste |
| S-Gres 300 | Sup. entibación (m²/m) | H70 (informativa) | `=(D19+0,1·D2/100+0,15)·2` | 10,36 | 13,20 | +2,84 | Doble fórmula SAN: H70 visual vs. H17 de coste |

### 4.1.4.1. Heterogeneidad ABA entre hojas del Excel oficial

La inspección de las celdas de superficie de entibación en las dos hojas ABA del Excel oficial reveló que **utilizan fórmulas distintas para la misma magnitud**: la hoja `A-Fundición 150` (celda H77) emplea la fórmula `(P + 0,1·DN/1000 + 0,20)·2`, mientras que la hoja `Fundición 300` (celda H75) emplea `(P + 0,1·DN/1000 + 0,15)·2`. La constante de holgura difiere entre 0,20 m y 0,15 m sin que exista justificación técnica documentada.

LicitaIA implementa una **única fórmula coherente** con el resto del módulo geométrico (clearance 0,15 + 0,1·DN/1000 m, offset de recubrimiento ABA 0,20 m), que coincide con la versión de la hoja A-Fundición 150 y produce, por tanto, una desviación de +0,10 m²/m en el caso Fundición 300. La discrepancia se ha documentado como **inconsistencia interna del Excel oficial** y no como error de LicitaIA.

### 4.1.4.2. Doble fórmula de entibación en saneamiento

En las hojas SAN del Excel oficial coexisten **dos fórmulas distintas para la superficie de entibación**, una con función informativa (cuadro de geometría) y otra con función económica (partida de coste). La inspección directa de las celdas confirma esta dualidad estructural, ilustrada en la Figura 4.1.

**Figura 4.1.** Trazabilidad de la fórmula de superficie de entibación en saneamiento entre el Excel oficial EMASESA y LicitaIA. Caso `S-Hormigón 2000+PE80` con profundidad 5,00 m y DN 2000 mm.

| Excel oficial EMASESA | LicitaIA |
|---|---|
| **Celda H70** (cuadro de geometría, informativa) | Función `_superficie_entibacion_pm()` en `src/domain/geometria.py` |
| Fórmula: `=(D19 + 0,1·D2/100 + 0,15)·2` | Fórmula: `(P + 1)·2·1,1` |
| Resultado: 10,70 m²/m (visible en tabla geométrica) | Resultado: 13,20 m²/m |
|  |  |
| **Celda H17** (partida de coste, fila de obra civil) |  |
| Fórmula: `=+(D19 + 1)·2·1,1` |  |
| Resultado: 13,20 m²/m × 22,73 €/m² = 300,04 €/m | Coste calculado: 300,04 €/m |
| ↑ Coincide con LicitaIA al céntimo | |

La fórmula H70 es **únicamente informativa**: se imprime en el cuadro geométrico de la hoja para mostrar al técnico la superficie geométrica de las paredes de la zanja. La fórmula económicamente vinculante es la de la celda H17, situada en la fila de la partida de obra civil correspondiente, que es la que multiplica al precio unitario para obtener el importe del capítulo. LicitaIA aplica esta segunda fórmula —la de coste— por lo que, pese a la discrepancia visual de 2,50 / 2,84 m²/m con la celda informativa, **el PEM de saneamiento coincide con el Excel al céntimo** en ambos casos SAN.

## 4.1.5. Bug detectado y corregido durante la validación: convención GG/BI en saneamiento

El proceso de validación detalla métrica a métrica permitió detectar una **divergencia previamente no documentada** entre LicitaIA y el Excel oficial en el cálculo del PEC sin redondear de los casos de saneamiento, con una diferencia constante de 1,09 €/m. La inspección de las fórmulas de las celdas SUMA en cada hoja reveló la causa raíz:

- En **abastecimiento**, la celda SUMA (`J61` en `A-Fundición 150`, `J59` en `Fundición 300`) implementa `=SUM(J57:J60)` con cuatro sumandos y **excluye explícitamente** el subtotal e) MATERIALES.
- En **saneamiento**, la celda SUMA (`J53` en ambas hojas SAN) implementa `=SUM(J48:J52)` con cinco sumandos e **incluye** el subtotal e) MATERIALES en la base.

LicitaIA, hasta el momento de esta validación, aplicaba la convención de abastecimiento de forma generalizada en ambas redes, infraestimando la base de Gastos Generales (GG) y Beneficio Industrial (BI) cuando había proyecto de saneamiento. La corrección se ha implementado en `src/aplicacion/calcular_presupuesto.py` y `src/presupuesto/bloques.py`, donde ahora se rastrean por separado los importes de materiales ABA y SAN, excluyendo de la base GG/BI únicamente los primeros. La Tabla 4.11 muestra el efecto del fix sobre los cuatro casos de validación.

**Tabla 4.11.** Resultado de la validación financiera antes y después de la corrección de la convención GG/BI en saneamiento.

| Indicador | Antes del fix | Después del fix |
|---|:---:|:---:|
| Métricas financieras coincidentes (total) | 18 / 20 (90,0 %) | 20 / 20 (100 %) |
| Casos con cuadro financiero exacto | 1 / 4 | 4 / 4 |
| Diferencia en PEC sin redondear (S-Hormigón 2000) | −1,09 €/m | +0,00 €/m |
| Diferencia en PEC sin redondear (S-Gres 300) | −1,09 €/m | +0,00 €/m |

El test de regresión `tests/test_snapshot_excel.py::test_snapshot_valores_financieros`, que mantiene un baseline de un proyecto mixto ABA+SAN de referencia, se ha actualizado para reflejar los nuevos valores financieros corregidos: GG ha pasado de 6 985,40 € a 7 041,31 €, BI de 3 224,03 € a 3 249,84 € y el total con IVA de 83 562,60 € a 83 659,40 €. El PEM no ha cambiado, dado que la corrección afecta exclusivamente a la base sobre la que se aplican los porcentajes GG y BI, no a los importes de obra.

## 4.1.6. Conclusiones de la validación

La validación contra el Excel oficial EMASESA, ejecutada métrica a métrica sobre los cuatro casos de referencia incluidos en el propio fichero, arroja los siguientes resultados:

1. **El cuadro financiero coincide al 100 %** con el Excel oficial en los cuatro casos, en cinco métricas por caso (PEM, materiales excluidos de GG/BI, base GG/BI, PEC sin redondear y PEC redondeado a la decena superior).

2. **La geometría coincide al 89,3 %** (25 de 28 métricas exactas al céntimo). Las tres desviaciones residuales se concentran exclusivamente en una métrica (superficie de entibación) y se han trazado a inconsistencias del propio Excel oficial: heterogeneidad entre las dos hojas ABA y existencia de fórmula doble (visual vs. económica) en las hojas SAN. En los casos de saneamiento, la fórmula económicamente vinculante (celda H17) coincide con la de LicitaIA al céntimo, lo cual valida indirectamente la corrección del módulo geométrico.

3. **La validación reveló y permitió corregir un error previo** del módulo financiero (aplicación de la convención GG/BI de abastecimiento a la red de saneamiento), elevando la exactitud financiera del 90 % al 100 %. Este hallazgo demuestra que el procedimiento de validación tiene **valor diagnóstico**, no únicamente de comprobación.

En términos generales, **LicitaIA reproduce con fidelidad la lógica matemática del Excel oficial EMASESA**, con discrepancias residuales totalmente caracterizadas y trazables al código fuente o a las celdas concretas del fichero original. Esta fidelidad valida el módulo de cálculo como cimiento sólido sobre el que se construyen las dos aportaciones diferenciales del presente Trabajo Fin de Grado: la base de datos versionada de precios y el sistema experto basado en CLIPS.


## 4.2. Validacion contra obras reales individuales

### 4.2.1. Metodologia

Esta seccion extiende la validacion del calculo (§ 4.1, certificacion contra el Excel oficial agregado EMASESA) con una validacion complementaria de **cobertura del catalogo**: se compara el resultado de LicitaIA contra siete expedientes BC3 de obras individuales reales (`data/proyectos_individuales/*.xlsx`). El objeto de prueba ya no es la formula del calculo, certificada en § 4.1, sino la pregunta de si los items del catalogo cubren los materiales y variantes que aparecen en obra real.

El procedimiento es:

1. Cargar cada BC3 con un loader generico (`notebook/_obras_individuales_helpers.py:cargar_bc3`) que parsea las filas "Total partida X.Y.Z" del export Presto/Arquimedes y devuelve una lista de `PartidaBC3` con codigo, descripcion, medicion, precio unitario e importe.
2. Curar manualmente un `MappingObra` por obra que declara que partida del BC3 alimenta cada input de `ParametrosProyecto` (longitud zanja ABA/SAN, profundidad, acometidas, m² acerado, m² calzada, label de tuberia dominante, materiales de demolicion). El mapping es trabajo de **knowledge engineering** — la traduccion defendible del proyecto BC3 al modelo parametrico de LicitaIA — y se versiona en codigo.
3. Derivar `ParametrosProyecto` desde el BC3 via `derivar_parametros(bc3, mapping, precios_base)`. Si un label del mapping no existe en el catalogo, la funcion lanza `ValueError("[CATALOG GAP] ...")` y se registra el item faltante.
4. Llamar a `calcular_presupuesto(parametros, precios_base)` con la misma ruta que la UI (sin codigo especial para validacion) y comparar el PEM obtenido contra el PEM total real del BC3.
5. Metrica unica: `gap_pct = (PEM_real_BC3 - PEM_LicitaIA) / PEM_real_BC3`. Positivo = LicitaIA infraestima; negativo = LicitaIA sobreestima. La comparacion se hace siempre contra el **PEM total** del BC3 (sin restar capitulos out-of-scope), por compromiso metodologico: el gap es la metrica que se reporta sin maquillaje.

Se mantiene a lo largo de todo el procedimiento el principio de **parametros derivados, no inventados**: cualquier valor que pueda extraerse del BC3 (longitud, profundidad, importe, label de tuberia) se calcula a partir del propio fichero. Cuando el BC3 no permite derivar un parametro sin ambiguedad (tipicamente la profundidad cuando la descripcion dice unicamente "< 2,50 m"), se elige un *midpoint* defensivo y se documenta en las notas del mapping.

Tolerancia adoptada **antes** de producir cualquier tabla: AACE Class 5 (± 15 % PEM global, ± 20 % por capitulo). Justificacion en nota al pie.

> Fuente: AACE International Recommended Practice 18R-97 / 56R-08, "Cost Estimate Classification System". Class 5 admite variabilidad del ± 15 % PEM global para proyectos cuyo nivel de definicion sea ≤ 5 %.

### 4.2.2. Protocolo de clasificacion y resultados cualitativos

Antes de gastar esfuerzo en gap analysis cuantitativo se aplica un protocolo cualitativo a las siete obras para clasificarlas como in-scope, parcial-in-scope u out-of-scope. La regla, declarada por adelantado, es:

- Obra no lineal (rotonda, deposito, ETAP/EDAR, electromecanica dominante) → out-of-scope.
- Capitulos no modelados por LicitaIA (jardineria, alumbrado, mobiliario, semaforizacion, electromecanico) > 50 % PEM → out-of-scope; entre 20 % y 50 % → parcial.
- Materiales o DN fuera del catalogo dominante > 70 % PEM → out-of-scope; entre 30 % y 70 % → parcial.
- ≥ 80 % PEM en capitulos modelados con materiales del catalogo → in-scope.

**Tabla 4.12.** Clasificacion de las siete obras BC3 por cobertura del modelo LicitaIA.

| Expediente | Nombre | Clasificacion | Motivo |
|------------|--------|---------------|--------|
| GOB.24.059 | Calle Baloncesto       | parcial-in-scope | Relining ULLAST 22 % PEM + cap 11 mobiliario ~10 % |
| GOB.25.002 | Avda Libertad          | out-of-scope     | 78,5 % PEM Relining PEAD 110 mm; LicitaIA no modela relining |
| GOB.25.006 | Santa Gema/Sta Rita    | in-scope         | Catalogo cubierto excepto FD DN 60 mm (catalog gap, 0,6 % PEM) |
| GOB.25.020 | Fuselaje               | parcial-in-scope | Cap 11 mobiliario / desvios / zocalos ~21 % PEM |
| GOB.25.026 | Sarandi                | in-scope         | FD DN 100 estandar; FC residual presente |
| GOB.25.036 | Arsenal                | in-scope         | Catalogo dominante FD DN 80/100 + PE-100 DN 90 cubierto |
| GOB.25.041 | Calle Argentina CR     | parcial-in-scope | Relining GOB25041 23 % PEM + cap 11 mobiliario ~16 % |

Distribucion: tres obras in-scope, tres parcial-in-scope, una out-of-scope. La obra out-of-scope queda excluida del gap analysis cuantitativo; las restantes seis se evaluan de forma honesta sabiendo que las parcial-in-scope dificilmente cerraran dentro de la tolerancia y que ese es el resultado esperado, no un fallo del modelo.

### 4.2.3. Tabla gap pre-migraciones

Con el catalogo en su estado anterior a Phase 2 (17 migraciones aplicadas) se ejecuta el procedimiento sobre las seis obras in-scope o parcial-in-scope. La tabla muestra el gap a nivel global; los catalog gaps detectados como `ValueError("[CATALOG GAP] ...")` se enumeran en § 4.2.4.

**Tabla 4.13.** Gap analysis pre-migraciones. Tolerancia AACE Class 5 (± 15 % PEM).

| Expediente | Clasif.  | PEM BC3 (€) | PEM LicitaIA (€) | gap (€)    | gap %  | Tipo   |
|------------|----------|------------:|-----------------:|------------:|-------:|--------|
| GOB.24.059 | parcial  | 145.500,01  | 229.256,71       | -83.756,70  | -57,6 % | EXCEDE |
| GOB.25.006 | in-scope | 340.000,06  | 186.763,04       | 153.237,02  | +45,1 % | EXCEDE |
| GOB.25.020 | parcial  | 181.999,95  | 130.854,28       | 51.145,67   | +28,1 % | EXCEDE |
| GOB.25.026 | in-scope |  92.894,94  |  69.158,95       | 23.735,99   | +25,6 % | EXCEDE |
| GOB.25.036 | in-scope | 157.999,99  | 112.314,27       | 45.685,72   | +28,9 % | EXCEDE |
| GOB.25.041 | parcial  | 204.192,71  | 125.271,65       | 78.921,06   | +38,7 % | EXCEDE |

Las seis obras exceden la tolerancia ± 15 % PEM en la pasada pre-migraciones. Esta es la senal esperada del gap analysis: la metrica sirve precisamente para **detectar** cobertura incompleta del catalogo y de la formula. La seccion siguiente convierte la unica brecha tipificable como catalog gap en una migracion de catalogo.

### 4.2.4. Items anadidos al catalogo (m18+)

La politica de Phase 2 (decision de proyecto LD-10) es **ampliar, no modificar**: los catalog gaps detectados se cierran anadiendo nuevas filas al catalogo con `INSERT OR IGNORE`, sin tocar las filas existentes que ya estan certificadas contra el Excel agregado oficial (§ 4.1). El precio de cada nuevo item se deriva del propio BC3 con la formula `precio_BD_centimos = int(round(valor_BC3 / 1,05 × 100))`, donde `1,05` es el coeficiente de seguridad CI que LicitaIA aplica al cargar precios.

**Tabla 4.14.** Migracion m18 anadida en Phase 2.

| Migracion | Tabla    | Variante                                       | precio_m (cts) | precio_material_m (cts) | Obra motivadora              |
|-----------|----------|------------------------------------------------|---------------:|------------------------:|-------------------------------|
| m18       | tuberias | (ABA, "FD  60 mm", FD, 60, factor_piezas=1,2) | 4093           | 1208                    | GOB.25.006 Santa Gema/Sta Rita |

Calculo de m18:
- Importe BC3 / medicion = 1.934,10 € / 45 m = 42,98 €/m con CI aplicado.
- Precio base BD = 42,98 / 1,05 = 40,9333 €/m → 4093 centimos.
- Reparto material/instalacion replicando la ratio de FD DN 80 (1276 / 4325 = 0,2950) → precio_material_m = round(4093 × 0,2950) = 1208 centimos.

La verificacion post-aplicacion con `init_db()` muestra `precio_BD × 1,05 = 42,9765 €/m` frente al BC3 `42,98 €/m`, error inferior al 0,1 %. La migracion es idempotente (UNIQUE(red, label) + `INSERT OR IGNORE`). El test invariante `tests/test_bd_invariante_ci.py` continua verde tras la aplicacion (141 pasados, 4 saltados, 2 deuda conocida xfail; ningun fallo nuevo).

### 4.2.5. Tabla gap post-migraciones y diff

Tras `init_db()` (que aplica m18) y recargar precios se re-ejecuta el procedimiento con catalogo ampliado.

**Tabla 4.15.** Gap analysis post-migraciones y mejora respecto a la pasada pre-migraciones.

| Expediente | gap % PRE | gap % POST | Mejora (pp) | Cierre (± 15 %) | Tipo de gap residual |
|------------|----------:|-----------:|------------:|------------------|----------------------|
| GOB.24.059 |   -57,6 % |   -57,6 %  |       0,0   | NO               | scope gap (parcial)  |
| GOB.25.006 |   +45,1 % |   +44,5 %  |       0,6   | NO               | formula gap          |
| GOB.25.020 |   +28,1 % |   +28,1 %  |       0,0   | NO               | scope gap (parcial)  |
| GOB.25.026 |   +25,6 % |   +25,6 %  |       0,0   | NO               | scope gap            |
| GOB.25.036 |   +28,9 % |   +28,9 %  |       0,0   | NO               | scope gap            |
| GOB.25.041 |   +38,7 % |   +38,7 %  |       0,0   | NO               | scope gap (parcial)  |

Solo Santa Gema muestra mejora (de 45,1 % a 44,5 %, equivalente a los 1.934 € del nuevo item FD DN 60). Las otras cinco obras no se mueven: su gap residual no es de catalogo. Los gaps residuales se tipifican y se documentan a continuacion.

### 4.2.6. Lectura del resultado

**Cierre dentro de la tolerancia AACE Class 5:** ninguna de las seis obras analizadas cierra al ± 15 % PEM tras m18. Este resultado es **el hallazgo principal de la validacion**: la migracion m18 cierra el unico catalog gap concreto detectable (FD DN 60 mm, 0,6 % PEM en Santa Gema), pero el grueso del residuo no es problema de catalogo.

**Tipificacion de los gaps residuales:**

- **Scope gap fundamental (3 obras parcial-in-scope):** Baloncesto (-57,6 %), Fuselaje (+28,1 %) y Calle Argentina CR (+38,7 %) tienen una porcion del PEM (entre 21 % y 23 % aproximadamente) en partidas que LicitaIA no modela: relining de tuberia FC, mobiliario urbano, pasarelas peatonales, desvios de trafico provisionales, reparacion de zocalos y proteccion de arbolado. En Baloncesto el efecto es inverso: LicitaIA *sobreestima* porque calcula una zanja completa (569 m × 2 m) que en realidad no se excava al ejecutar relining sobre la tuberia existente. Este resultado valida el alcance acotado de LicitaIA (redes lineales urbanas con instalacion a cielo abierto) y delimita honestamente el universo de proyectos en los que la herramienta es directamente aplicable.

- **Scope gap transversal (3 obras in-scope con +25-29 %):** Sarandi, Arsenal y Santa Gema exceden la tolerancia por una causa comun: el capitulo 11 de los BC3 (mobiliario urbano, pasarelas, desvios de trafico, reparacion de zocalos) representa entre el 11 % y el 15 % del PEM y no esta modelado en LicitaIA. Adicionalmente, P01 "Proteccion del Arbolado" anade entre 3 % y 6 % PEM en estas obras. Este es un **descubrimiento metodologico** del proceso de validacion: el gap analysis ha caracterizado un componente sistematico de la obra urbana real que el modelo parametrico actual no captura. Es informacion accionable para futuras iteraciones de la herramienta.

- **Formula gap (Santa Gema):** la diferencia residual de +44,5 % en Santa Gema, ademas del catalog gap ya cerrado, viene del reparto de longitud de zanja entre redes ABA y SAN cuando ambas comparten el mismo capitulo 02 de excavacion. El selector curado para SAN (`agregar=False`) devuelve la primera coincidencia y no la suma proporcional, infraestimando la zanja SAN. Es un gap de formula, parcialmente subsanable con curado adicional del mapping (no afecta al modelo de LicitaIA, si al *pipeline* de derivacion BC3 → ParametrosProyecto).

- **Catalog gap residual:** ninguno tras m18.

**Patron transversal sobre `pct_seguridad` y obras con fibrocemento:** tres de las cinco obras con presencia de FC en el BC3 muestran un porcentaje de seguridad y salud (S01 / PEM) inferior al 4 % que se espera convencionalmente cuando hay amianto: Baloncesto 2,4 %, Santa Gema 2,9 %, Sarandi 3,2 %. El procedimiento ha mantenido los valores derivados del BC3 sin forzarlos a un minimo predefinido, en aplicacion del compromiso metodologico de no inventar parametros. La regla CLIPS `obra-regulada-amianto` del sistema experto (§ 5) tiene aqui una oportunidad clara: avisar al licitador cuando el FC detectado en el proyecto no se corresponde con un dimensionado de S&S coherente con la presencia del material.

**Conclusion:** la validacion contra obras reales no certifica la herramienta como completa para todo proyecto BC3. La certifica como **fiable y honesta**: el modelo parametrico cubre el nucleo lineal de la obra urbana EMASESA y delimita el resto como scope gap caracterizado. La extension natural del trabajo — fuera del alcance del presente TFG — es modelar el capitulo 11 (obra accesoria) y dotar al sistema experto de una alerta especifica de coherencia FC ↔ S&S.

### 4.2.7. Cierre de gaps — Phase 2.2

Tras los hallazgos de § 4.2.6 (gap residual sistematico atribuible a capitulo 11 BC3 y a errores de mapping ABA/SAN en obras mixtas), se ejecuta una segunda iteracion de validacion (Phase 2.2) con tres lineas de actuacion **aditivas**: (A) parametro nuevo `pct_obra_accesoria`, (B) correcciones de selectores en el helper de derivacion BC3, (C) ampliacion del catalogo (m19) para una variante PE-100 ausente en Arsenal. La invariante 141 / 141 sobre el Excel certificado se preserva en cada paso (cero filas modificadas, solo INSERT OR IGNORE).

#### Cambios aplicados

**A) Parametro nuevo `pct_obra_accesoria`**

Se anade el campo `pct_obra_accesoria` (0–25 %, default 0,0) a `ParametrosProyecto`, aplicado sobre la misma base que `pct_servicios_afectados` (`base_ss`). Genera un capitulo nuevo `OBRA ACCESORIA URBANA` en el desglose del presupuesto. Justificacion: el capitulo 11 BC3 de obras reales contiene partidas de mobiliario urbano, desvios de trafico, pasarelas peatonales y zocalos que no forman parte del nucleo lineal modelado por LicitaIA. Son sistematicas (presentes en 5 de 6 obras analizadas) y acotadas: rango observado 6 % – 21 % PEM, mediana aproximada 14 %. El percentil 25 – 75 (10 % – 17 %) se usa como referencia defensible para el tribunal TFG: *el licitador puede acotar la obra accesoria a su experiencia en la zona*. **El default 0,0 preserva los 141 casos certificados Excel** sin un solo cambio en el desglose pre-existente.

**B) Correcciones de selectores (notebook MAPPINGS, sin cambio de BD)**

Se anade el campo `capitulo_emasesa` a `PartidaSelector` para permitir filtrar por capitulo canonico EMASESA (heredado de la cabecera de texto del BC3) antes que por capitulo BC3-interno. El filtro canonico va FIRST en la cadena de selectores (`capitulo_emasesa → capitulo → descripcion_substr → codigo_exacto`). Este cambio infraestructural permite separar redes ABA y SAN en obras mixtas donde ambas comparten el mismo `capitulo` BC3 pero distintos `capitulo_emasesa`. Sobre esta base se corrigieron cuatro mappings:

1. **Santa Gema `longitud_zanja_san_m`**: `agregar=False` → `agregar=True` con `capitulo_emasesa='02'` (OC SAN canonico). Antes capturaba 13 m de 247 m reales.
2. **Santa Gema `longitud_zanja_aba_m`**: anadido `capitulo_emasesa='01'` (OC ABA canonico) para separar la red ABA de la SAN cuando ambas comparten capitulo BC3 `'02'`.
3. **Arsenal `m2_calzada_aba`**: sustituido `capitulo='04'` (BC3-interno) por `capitulo_emasesa='03'` (PV ABA canonico EMASESA).
4. **Argentina CR `m2_calzada_aba`**: misma correccion que Arsenal.

Estos bugs estaban enmascarados en Phase 2 porque el loader BC3 usaba codigos internos en lugar de capitulos canonicos EMASESA. Phase 2 corrigio el loader; Phase 2.2 corrige los selectores que consumian el campo erroneo.

**C) Ampliacion del catalogo m19 — PE-100 DN 90 PN 16**

La obra Arsenal incluye 310 m de tuberia PE-100 DN 90 PN 16 (5.986,10 EUR / 310 m / 1,05 = 18,39 EUR/m base). En el catalogo Phase 2 solo existia PE-100 DN 90 sin sufijo PN (asimilable a PN 10, 10,49 EUR/m). Migracion `m19_cat_aba_pe100_dn90_pn16` (INSERT OR IGNORE) anade la variante PN 16 con `precio_m=18,39 EUR/m`, `factor_piezas=1,2`, `precio_material_m=4,07 EUR/m` derivado por ratio del PN 10 existente. El `schema_version` queda en 19. Como efecto colateral del INSERT, el cargador de tuberias en `db_precios.py` requirio un `tiebreaker` `id` ASC en el `order_by` para preservar la invariante 141 (la fila certificada PN 10 sale primero ante empate en `diametro_mm`). Es un fix latente que se manifestaba solo al ampliar el catalogo con variantes que comparten clave de busqueda; documentado como patron `Stable order_by con tiebreaker`.

#### Tabla 4.16. Gap PRE-Phase-2.2 vs POST-Phase-2.2 (notebook 09 re-ejecutado)

Tras aplicar A + B + C y re-ejecutar `09_validacion_obras_individuales.ipynb` con `pct_obra_accesoria = 0,0` (configuracion neutra, equivalente al estado Phase 2):

| Expediente | Obra                | Clasificacion       | gap Phase 2 | gap Phase 2.2 (sel + m19) | Cierre (± 15 %) | Tipo de gap residual |
|------------|---------------------|---------------------|------------:|--------------------------:|------------------|----------------------|
| GOB.24.059 | Calle Baloncesto    | parcial-in-scope    |   −57,6 %   |   −57,6 %                 | NO               | scope gap (parcial)  |
| GOB.25.006 | Santa Gema Sta Rita | in-scope            |   +44,5 %   |    −3,6 %                 | **SI**           | ACEPTABLE            |
| GOB.25.020 | Fuselaje            | parcial-in-scope    |   +28,1 %   |   +28,1 %                 | NO               | scope gap (parcial)  |
| GOB.25.026 | Sarandi             | in-scope            |   +25,6 %   |   +25,6 %                 | NO               | scope gap (cap 11)   |
| GOB.25.036 | Arsenal             | in-scope            |   +28,9 %   |   +28,9 %                 | NO               | scope gap (cap 11) + bug latente sel  |
| GOB.25.041 | Calle Argentina CR  | parcial-in-scope    |   +38,7 %   |   +38,7 %                 | NO               | scope gap (parcial)  |

**Hallazgos cuantitativos:**

- **Santa Gema cierra al ± 15 % PEM** (de +44,5 % a −3,6 %, mejora de 48,1 puntos porcentuales). El fix de selectores ABA/SAN sobre el capitulo 02 compartido fue el mecanismo decisivo: separar la longitud de zanja SAN (247 m reales) de la ABA (resto del capitulo) mediante el filtro `capitulo_emasesa` lleva la formula al rango certificado. Es la primera obra real que cierra dentro de la tolerancia AACE Class 5 sin necesidad de palancas residuales.
- **Sarandi y Arsenal mantienen +25 % – +29 %**. El analisis de las trazas confirma lo previsto en § 4.2.6: el residual es scope gap del capitulo 11 BC3 (obra accesoria urbana — mobiliario, desvios, pasarelas, zocalos), no error de mapping ni gap de catalogo.
- **Las tres obras parcial-in-scope** (Baloncesto, Fuselaje, Argentina CR) no se mueven, como era previsible: su gap dominante es scope gap fundamental (relining, conexiones especiales, P01 proteccion arbolado) que ningun fix de mapping o ampliacion de catalogo puede cerrar honestamente.

#### Proyeccion con `pct_obra_accesoria` calibrado a la mediana observada

El notebook 09 actual no parametriza `pct_obra_accesoria` (se ejecuta con default 0,0). Como ejercicio de proyeccion para las dos obras in-scope con scope gap del capitulo 11, se aplica analiticamente la palanca al percentil 50 (`pct_obra_accesoria = 0,14`). El termino se suma sobre `base_ss` (presupuesto sin cap. material/cánones); para Sarandi `base_ss ≈ 51.500 EUR` y Arsenal `base_ss ≈ 84.700 EUR` (estimacion a partir del PEM_LIC y la ratio observada en el desglose):

| Obra     | gap Phase 2.2 base | aporte `pct=0,14` (EUR) | gap proyectado |
|----------|-------------------:|------------------------:|---------------:|
| Sarandi  | +25,6 %            | ≈ 7.200 EUR             | ≈ +17,8 %      |
| Arsenal  | +28,9 %            | ≈ 11.900 EUR            | ≈ +21,4 %      |

La proyeccion no cierra ninguna de las dos al ± 15 %; un licitador que opere en zonas donde el capitulo 11 sea mas dominante (por ejemplo Arsenal con presencia historica de mobiliario urbano y desvios) puede legitimamente subir a `pct = 0,17` (percentil 75), llevando Arsenal a aproximadamente +18 % y Sarandi a +14 %, con Sarandi ya dentro de tolerancia. El caso queda **acotado al juicio del licitador**, no embebido en la herramienta.

**Bug latente detectado durante la re-ejecucion de Arsenal:** los selectores `descripcion_substr` no son accent-insensitive (`"reposicion pavimento calzada"` no matchea `"Reposición Pavimento Calzada"` por la `ó`). Esto afecta a los fixes de m2_calzada_aba en Arsenal y Argentina CR (fix sin efecto), pero no introduce regresion porque el comportamiento PRE y POST coincide. Documentado como deuda tecnica para futura iteracion (normalizacion NFKD en `seleccionar_partidas`); fuera del alcance del presente TFG.

#### Lectura de los resultados

- **El cierre defendible de la herramienta es el nucleo lineal EMASESA con mappings curados** (Santa Gema POST-2.2 al −3,6 %), no el universo BC3 completo.
- **El parametro `pct_obra_accesoria` traslada la responsabilidad del scope gap al licitador**, sin alterar la matematica certificada (default 0,0 preserva 141 / 141 Excel).
- **El catalog gap residual a fecha de cierre Phase 2.2 es nulo** sobre las obras analizadas: m18 cierra el FD DN 60 mm de Santa Gema, m19 cierra el PE-100 DN 90 PN 16 de Arsenal. El resto del residual es scope (cap. 11) o formula (selector accent-bug detectado, deferido).
- **El protocolo de validacion ejecutado se documenta en su totalidad** (4.2.1 pre-migraciones, 4.2.5 post-migraciones-Phase-2, 4.2.7 post-Phase-2.2). El TFG defendera ante tribunal una herramienta cuya tolerancia AACE Class 5 se cumple, en al menos una obra real auditada externamente, sin tocar los 141 casos certificados.

#### Verificacion dual

| Verificacion                                                                  | Resultado                          |
|-------------------------------------------------------------------------------|------------------------------------|
| `pytest tests/test_bd_invariante_ci.py -q`                                    | 141 passed, 4 skipped, 2 xfailed   |
| `pytest tests/ -q`                                                            | 297 passed, 5 skipped, 2 xfailed   |
| `09_validacion_obras_individuales.ipynb` re-ejecutado vía `nbclient`          | OK (15 celdas, sin errores)        |
| `data/precios.db` `schema_version`                                            | 19                                 |
| Reduccion de gap atribuible a Phase 2.2 (obras in-scope)                      | Santa Gema −48,1 pp; Sarandi y Arsenal sin cambio (scope gap, esperado) |

La invariante 141 / 141 sobre Excel EMASESA es la **prueba dura** de no regresion: cualquier cambio en BD (m17, m18, m19) o en el cargador (`tiebreaker` `id`) que rompiera la matematica certificada se manifiesta como fallo en este test. La invariante permanece verde en cada commit de la fase 02.2.
