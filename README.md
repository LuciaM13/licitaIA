# LicitAIA · Calculadora de presupuesto

Aplicación en **Streamlit** para calcular presupuestos usando únicamente los datos proporcionados en el CSV y el resumen de capítulos.

## Archivos importantes

- `app_licitaia.py`: aplicación principal.
- `datos.csv`: catálogo de partidas y precios.
- `requirements.txt`: dependencias.

## Ejecutarlo en local

```bash
pip install -r requirements.txt
streamlit run app_licitaia.py
```

## Ejecutarlo desde GitHub en Streamlit Cloud

1. Sube al repositorio estos archivos:
   - `app_licitaia.py`
   - `datos.csv`
   - `requirements.txt`

2. En Streamlit Cloud, crea una app nueva desde tu repo.

3. En **Main file path** selecciona:
   `app_licitaia.py`

4. Despliega la app.

## Qué hace

### 1. Resumen por capítulos
Replica el formato del presupuesto final con los 8 capítulos, PEM, GG, BI, IVA y total.

### 2. Detalle desde catálogo CSV
Permite:
- filtrar por sección
- buscar por código o nombre
- seleccionar partidas
- marcar partidas tipo **S/N** con checkbox
- introducir cantidades
- descargar el desglose en CSV

## Nota

La app intenta leer el CSV con cualquiera de estos nombres:
- `datos.csv`
- `catalogo_precios_limpio.csv`
- `240415_VALORACIÓN ACTUACIONES(S-BASE PRECIOS ABRIL-'24)).csv`

Así es más fácil usarla en GitHub aunque cambie el nombre del archivo.
