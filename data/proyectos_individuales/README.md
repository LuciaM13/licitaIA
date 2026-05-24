# Proyectos individuales --- datos BC3

Esta carpeta contiene los ficheros Excel BC3 (export Presto/Arquimedes) de
obras individuales de EMASESA utilizados en la validacion del catalogo de
LicitaIA (Phase 2, seccion 4.2 del TFG).

Los ficheros `.xlsx` estan gitignored deliberadamente: son exportaciones de
trabajo de los expedientes de EMASESA y no son datos publicos.

## Ficheros esperados

Para ejecutar el notebook `notebook/09_validacion_obras_individuales.ipynb`
deben estar presentes localmente los siguientes ficheros (nombre exacto tal y
como se entrega por EMASESA):

- `GOB.24.059 Calle Baloncesto.xlsx`         (ABA + SAN, fibrocemento)
- `GOB.25.002 Avda Libertad.xlsx`            (ABA puro, FD DN150)
- `GOB.25.006 Calle Santa Gema Santa Rita.xlsx` (ABA + SAN, mas grande de las 7)
- `GOB.25.020 Fuselaje.xlsx`                 (ABA + SAN, FD DN80)
- `GOB.25.026 Sarandi.xlsx`                  (ABA puro, FD DN100)
- `GOB.25.036 Arsenal.xlsx`                  (ABA + SAN, Plaza Huerta San Luis)
- `GOB.25.041 Calle Argentina CR.xlsx`       (ABA, fibrocemento <350 mm)

## Como obtenerlos

Solicitar los exportados BC3 (formato `.xlsx`, una hoja unica `Hoja1`) al
sistema de expedientes de EMASESA para cada numero de expediente listado.

## Formato esperado

Cada fichero tiene una unica hoja `Hoja1` con columnas:

| Col | Contenido |
|-----|-----------|
| A   | Codigo de capitulo o partida (`01`, `2.2.2.001`, ...) |
| C   | Descripcion (titulo de partida, sumandos, o "Total partida X.Y.Z") |
| D   | Uds (sumandos en filas de desglose) |
| E   | Longitud |
| F   | Latitud |
| G   | Altura |
| H   | Subtotal de cada sumando |
| I   | Medicion total (solo en filas "Total partida ...") |
| J   | Precio unitario (string con coma decimal, ej. "10,07") |
| K   | Importe total (float) |

Fila 1 = cabecera. Fila 2 = nodo raiz (`A = "."`). Las filas con codigo
en col A son cabeceras de capitulo o partida. Las filas con `C = "Total
partida X.Y.Z"` son las leaf partidas que el loader extrae.

## Privacidad

Los `.xlsx` no se versionan. La estructura y los ratios de gap se documentan
en `notebook/resultados_tfg.md` § 4.2 sin reproducir las descripciones
literales que pudieran identificar zonas concretas.
