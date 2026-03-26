# Proyecto de presupuesto en Python

Este proyecto convierte los datos proporcionados a una aplicación en **Streamlit**.

## Qué incluye

- `app.py`: interfaz principal.
- `catalogo_precios_limpio.csv`: catálogo de precios extraído del CSV proporcionado.
- `requirements.txt`: dependencias.

## Cómo ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Modos disponibles

### 1. Resumen por capítulos
Replica el formato del presupuesto final, con los 8 capítulos, gastos generales, beneficio industrial e IVA.

### 2. Detalle desde catálogo CSV
Permite seleccionar partidas del catálogo, marcar partidas tipo **S/N** con checkbox y meter cantidades para calcular el presupuesto.

## Notas

- El proyecto usa únicamente la información del CSV proporcionado y el resumen de capítulos del pliego.
- Como el CSV no expone todas las partidas de abastecimiento de forma completa, el modo detalle permite añadir ajustes manuales por capítulo para completar el cálculo.
