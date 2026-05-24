"""Exportación del resultado del presupuesto a texto listo para pegar en Word.

Genera un texto plano con los subtotales por capítulo y el resumen
financiero. La UI lo presenta en un ``st.code`` para que el licitador lo
copie y lo pegue en su informe Word. No genera ``.docx`` directamente.
"""

from __future__ import annotations

from typing import Any

from src.soporte.formato import euro


def generar_texto_word(r: dict[str, Any]) -> str:
    """Genera texto listo para copiar a Word a partir del resultado del cálculo."""
    pcts = r["pcts"]
    lineas = [f"{k}: {euro(v['subtotal'])}" for k, v in r["capitulos"].items()]
    lineas.append(f"Presupuesto de Ejecución Material: {euro(r['pem'])}")
    lineas.append(f"{pcts['gg']*100:.0f} % Gastos Generales: {euro(r['gg'])}")
    lineas.append(f"{pcts['bi']*100:.0f} % Beneficio Industrial: {euro(r['bi'])}")
    lineas.append(f"Presupuesto Base de Licitación excluido IVA: {euro(r['pbl_sin_iva'])}")
    lineas.append(f"{pcts['iva']*100:.0f} % IVA: {euro(r['iva'])}")
    lineas.append(f"Presupuesto Base de Licitación incluido IVA: {euro(r['total'])}")
    return "\n".join(lineas)
