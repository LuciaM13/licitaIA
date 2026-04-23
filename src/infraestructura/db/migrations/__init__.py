"""Lista ordenada de migraciones del schema.

El orden es **declarativo, no por número de versión**: preserva exactamente
el orden en que el runner histórico las aplicaba. En particular, M7 (dedup
demolición) corre ANTES que M6 (fix precios entibación) por un artefacto
del fichero original. Reordenar alteraría el comportamiento en BDs que
estén en una versión intermedia.

Cada módulo expone:
  - ``VERSION: int``
  - ``DESCRIPCION: str``
  - ``aplicar(conn: sqlite3.Connection) -> None``

El runner en ``src.infraestructura.db.runner`` toma la versión actual y
ejecuta solo las migraciones con versión estrictamente mayor.
"""

from __future__ import annotations

from src.infraestructura.db.migrations import (
    m01_factor_piezas,
    m02_entibacion_san,
    m03_entibacion_san_profunda,
    m04_demolicion_acerado_y_pozos_san,
    m05_eliminar_entibacion_paralelo,
    m07_dedup_demolicion,
    m06_fix_precios_entibacion,
    m08_patron_a_ci2,
    m09_residual_mec_hasta_25,
    m10_patron_b_imbornales,
    m11_residuales_patron_a_excavacion,
    m12_check_constraints,
    m13_integer_centimos,
    m14_audit_log,
    m15_demolicion_material,
    m16_san_bordillo_generico,
)


MIGRACIONES = [
    m01_factor_piezas,
    m02_entibacion_san,
    m03_entibacion_san_profunda,
    m04_demolicion_acerado_y_pozos_san,
    m05_eliminar_entibacion_paralelo,
    m07_dedup_demolicion,          # M7 antes de M6 (orden original del runner)
    m06_fix_precios_entibacion,
    m08_patron_a_ci2,
    m09_residual_mec_hasta_25,
    m10_patron_b_imbornales,
    m11_residuales_patron_a_excavacion,
    m12_check_constraints,
    m13_integer_centimos,
    m14_audit_log,
    m15_demolicion_material,
    m16_san_bordillo_generico,
]
