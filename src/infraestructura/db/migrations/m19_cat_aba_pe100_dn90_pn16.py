"""m19: anadir tuberia PE-100 DN 90 mm PN 16 al catalogo ABA.

Motivado por GOB.25.036 Arsenal (Phase 2.2 gap analysis, 2026-05-05): el BC3
oficial incluye 310 m de "Tuberia PE-100, DN 90 mm, PN 16 (Abto.) ENTUBADA"
(partida 3.1.2.3.080) con importe 5.986,10 EUR (CI aplicado). El catalogo
ABA solo contiene la variante PE-100 DN 90 mm sin clase de presion explicita
(precio 10,49 EUR/m base, asimilable a PN 10); sin esta variante PN 16,
derivar_parametros mapea a la PN 10 mas barata e infravalora el tramo de
alta presion de Arsenal.

Calculo del precio (precios.db almacena base; CI 1.05 se aplica al cargar):
  - Importe BC3 / medicion = 5.986,10 / 310 = 19,31 EUR/m (precio con CI)
  - Precio base = 19,31 / 1.05 = 18,3905 EUR/m
  - precio_m centimos = int(round(19,31 / 1.05 * 100)) = 1839

Reparto material/instalacion: se replica la ratio de PE-100 DN 90 PN 10
existente en catalogo (precio_m 1049, precio_material_m 232 -> ratio
0,2212) para mantener coherencia con la convencion "materiales ABA
excluidos de GG/BI" (Excel EMASESA J57:J60):
  - precio_material_m = int(round(1839 * 232/1049)) = 407

factor_piezas: 1,2 (mismo valor que el resto de PE-100 ABA, herencia del
patron de instalacion estandar de polietileno de alta densidad).

Sin UPDATE: la migracion solo INSERT OR IGNORE (UNIQUE(red, label)). Las
filas existentes del catalogo, certificadas contra el Excel agregado oficial,
no se tocan (LD-10 "Ampliar, no modificar").
"""
from __future__ import annotations

import sqlite3

VERSION = 19
DESCRIPCION = "Catalogo: tuberia PE-100 DN 90 mm PN 16 ABA (motivado por GOB.25.036 Arsenal)"


def aplicar(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO tuberias "
        "(red, label, tipo, diametro_mm, precio_m, factor_piezas, precio_material_m) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("ABA", "PE-100  90 mm PN16", "PE-100", 90, 1839, 1.2, 407),
    )
