"""Políticas de dominio: filtros de elegibilidad y reglas de desempate.

Estas funciones son conocimiento estable del dominio EMASESA: qué
material de un catálogo aplica a una combinación (red, profundidad, DN,
instalación) y qué criterio desempata cuando varios aplican. Python puro,
sin CLIPS, sin I/O.

El módulo ``src.reglas.decisor`` las consume para orquestar la selección
de material; el motor CLIPS (en ``src.reglas.alertas_clips``) no
interviene en esta decisión.
"""
