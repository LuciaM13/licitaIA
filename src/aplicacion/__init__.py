"""Capa de aplicación: use cases que orquestan dominio + infraestructura.

Cada módulo aquí representa una operación de negocio concreta (calcular un
presupuesto, editar el catálogo, consultar/guardar historial). Los use
cases son el punto de entrada desde la UI Streamlit y coordinan lógica
del dominio con los adaptadores de persistencia.

Restricciones:
  - Ningún módulo de aplicación importa ``streamlit`` ni ``pages/``.
  - Los contratos (DTOs) de casos de uso viven en ``contratos.py``.
"""
