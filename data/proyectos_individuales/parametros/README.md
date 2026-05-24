# Parametros YAML por proyecto individual

Esta carpeta contiene un fichero YAML por expediente, mapeado 1:1 a
`ParametrosProyecto` (`src/modelo/parametros.py:14`). El cargador
`src/validacion_proyectos/cargador_yaml.py` los hidrata en runtime
resolviendo los `*_label` contra el catalogo de precios.

## Ficheros

| Fichero | Contenido |
|---------|-----------|
| `GOB.XX.YYY.yaml` | Parametros derivados del Excel BC3 del expediente |

Los ficheros de proyecto **se generaron automaticamente** con el script
`scripts/_extract_yamls.py` a partir de los `.xlsx` en
`data/proyectos_individuales/`. Siempre revisar a ojo antes de usar:
hay marcas `# TODO:` en los campos de baja confianza.

## Como rellenar un YAML nuevo

1. Crear `<expediente>.yaml` usando como referencia cualquier `GOB.*.yaml` existente (o regenerar todos con `scripts/_extract_yamls.py` y editar a mano lo necesario).
2. Rellenar `expediente`, `nombre`, `fuente_xlsx`.
3. Para cada bloque, mirar en el Excel BC3 (hoja unica `Hoja1`):

| Campo YAML | Donde mirar en el Excel |
|------------|-------------------------|
| `aba.tipo` | Descripcion de la partida tuberia ABA principal: `FD`, `PE100`, `PE80`, `PEAD`. Si dice "Relining" suele ser `PE100`. |
| `aba.dn` | Mismo titulo: "DN 150 mm" o "PEAD 110 mm". |
| `aba.longitud_m` | Col I (medicion) de la partida `Total partida X.Y.Z` correspondiente. |
| `aba.profundidad_m` | Memoria del proyecto / seccion tipo. Si solo aparece `< 2,50m` en titulos de excavacion, es el MAXIMO permitido, NO la profundidad real. Default 1.20 m si no hay dato. |
| `san.*` | Igual que `aba` pero buscando "Tuberia gres", "PVC sane.", "HM DN..." etc. |
| `pavimentacion_aba.acerado_m2` | Suma de m2 de partidas "Solado/baldosa/cigarrillo/adoquin" en cap. PAVIMENTACION ABA o cap. OBRA CIVIL ABA si no hay capitulo dedicado. Si no hay solado, fallback a m2 de "Demolicion acerado". |
| `pavimentacion_aba.calzada_m2` | Idem con "Reposicion pavimento", "AC 16", "Hormigon bituminoso", "Mezcla asf.". Fallback: m2 demolicion calzada. |
| `pavimentacion_aba.bordillo_m` | Suma medicion partidas "Bordillo prefabricado". |
| `subbase_aba.label` | Descripcion de "Base albero", "Base zahorra ZA-25" etc. |
| `subbase_aba.espesor_m` | Memoria / seccion tipo. Default 0.20 m. |
| `acometidas.aba_n` | Suma medicion de partidas "Acom Abto..." (puede ser ml; dividir por longitud unitaria si toca, o contar uds segun proyecto). |
| `acometidas.san_n` | "Acom.sto..." idem. |
| `obra.pct_manual` | `exc_manual_m3 / (exc_manual_m3 + exc_mecanica_m3)`. Buscar partidas `2.2.x.001` (manual) y `2.2.x.005`/`2.2.x.010` (mecanica). |
| `obra.desmontaje_tipo` | `fibrocemento` si la partida dice "Levantado tuberia FC"; `normal` para otras tuberias; `none` si no hay desmontaje. |
| `obra.desmontaje_longitud_m` | Medicion de la partida desmontaje. |
| `obra.pozos_existentes_aba` | `demolicion` si "Demolicion pozo de registro existente"; `anulacion` si "Anulacion pozo"; `none` en otro caso. |
| `obra.pozos_existentes_aba_n` | Medicion de la partida correspondiente. |
| `imbornales.tipo` | `nuevo` si hay partida "Imbornal 60x30 ..." nueva; `adaptacion` si "Adaptacion imbornal"; `none` en otro caso. |
| `imbornales.nuevo_label` | Descripcion exacta de la partida si tipo=`nuevo`. |
| `porcentajes.pct_seguridad` | `S&S_EUR / base` donde `base = PEM - cap_11 - SS - gestion`. |
| `porcentajes.pct_gestion` | `gestion_EUR / base`. |
| `porcentajes.pct_servicios_afectados` | Por defecto 0.0 (cap 11 fuera de alcance). |

## Convenciones

- **Comentarios**: usar `#`. Marcar campos dudosos como `# TODO: ...`.
- **Bloques opcionales**: si el proyecto no tiene SAN, omite el bloque
  `san:` completo (las properties `aba_activa` / `san_activa` son
  derivadas y no requieren flag explicito).
- **Labels**: deben coincidir letra a letra con la fila del catalogo en
  BD (ej. `acerado_aba`, `calzada_aba`, `bordillo_reposicion`,
  `calzadas_reposicion`). El cargador lanza `ValidationConfigError` si
  un label no resuelve. Ver `src/catalogo/carga.py:31` para el inventario
  de catalogos disponibles.
- **No incluir descripciones literales del Excel** en ficheros que se
  vayan a publicar (TFG): los YAMLs locales si las llevan en bloques
  `_descripcion_excel:` y `_alternativas:` para auditoria, pero el
  reporte agregado debe omitirlas (ver politica de privacidad en el
  README de `data/proyectos_individuales/`).
- **Bloques `_meta_extraccion`, `_alternativas`, `_TODO_*`**: son
  informativos. El cargador los ignora. Borrarlos tras revision
  manual deja el YAML limpio.

## Regenerar todos los YAMLs

```powershell
py scripts/_extract_yamls.py
```

Sobrescribe los YAMLs existentes con la salida actual del script.
**Hacer copia de seguridad si has rellenado a mano.**

## Verificacion rapida

Tras editar un YAML, comprobar carga con:

```python
from pathlib import Path
import yaml
data = yaml.safe_load(Path("data/proyectos_individuales/parametros/GOB.25.002.yaml").read_text(encoding="utf-8"))
print(data["parametros"].keys())
```

El cargador completo se implementara en
`src/validacion_proyectos/cargador_yaml.py` (no esta dentro del alcance
de la extraccion automatica).
