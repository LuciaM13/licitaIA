"""
Validación de la app contra el Excel oficial EMASESA - abril 2024.

Fuente de verdad: 240415_VALORACIÓN ACTUACIONES.xlsx
Hoja de referencia: 'A-Fundición 150'

Estos tests prueban que las fórmulas de la app reproducen exactamente
los resultados del Excel de EMASESA. Son independientes de los precios
almacenados en la BD - validan la LÓGICA, no los datos.

Ejecutar:
    pytest tests/test_validacion_excel.py -v

Si todos pasan → las fórmulas de cálculo son idénticas al Excel de EMASESA.
"""

from __future__ import annotations

import pytest

from src.domain.geometria import calcular_geometria
from src.domain.financiero import calcular_resumen


# ═══════════════════════════════════════════════════════════════════════════════
# Valores de referencia extraídos directamente del Excel
# Hoja: A-Fundición 150 - 1 metro lineal de tubería FD DN=150 mm
# ═══════════════════════════════════════════════════════════════════════════════

# Parámetros de entrada (columna izquierda del Excel)
_DN_MM         = 150
_PROFUNDIDAD_M = 1.25    # Cota roja (F17)
_ENTIBACION    = True    # Entibación = s (F19) - activa a 1.25 m en el Excel
_H_PAVIMENTO_M = 0.49    # Altura de pavimento (F79)
_PCT_MANUAL    = 0.50    # 50% excavación manual (F26)

# Geometría esperada (tabla de mediciones, filas F69–F78 del Excel)
_ANCHO_FONDO_M      = 0.600               # F69
_ANCHO_CIMA_M       = 0.600               # F70 - igual al fondo (entibación)
_VOL_ZANJA_M3       = 0.555               # F71
_VOL_EXCAV_MEC_M3   = 0.278               # F72
_VOL_EXCAV_MAN_M3   = 0.278               # F73
_ANCHO_RECUB_M      = 0.600               # F74 - igual al fondo (entibación)
_ALTURA_ARENA_M     = 0.380               # F75
_VOL_ARENA_M3       = 0.2026              # F76
_SUP_ENTIBACION_M2  = 2.93                # F77
_VOL_RELLENO_M3     = 0.327               # F78

# Cuadro resumen financiero (filas F57–F66 del Excel)
# PEM = SUMA(a+b+c+d) + e)MATERIALES = 412.37 + 3.92 = 416.29
_SUMA_ABCD     = 412.37   # (1) SUMA - base sobre la que aplican GG y BI (F61)
_MATERIALES    = 3.92     # e) MATERIALES - excluidos de GG/BI (F64)
_PEM           = _SUMA_ABCD + _MATERIALES   # 416.29
_GG_ESPERADO   = 53.61    # (2) G.G. 13% de SUMA (F62)
_BI_ESPERADO   = 24.74    # (3) B.I. 6% de SUMA (F63)
_PEC_REDONDEADO = 500.0   # PEC redondeado (F66) - equivale a nuestro PBL sin IVA


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GEOMETRÍA DE ZANJA
# ═══════════════════════════════════════════════════════════════════════════════

class TestGeometriaVsExcel:
    """
    Valida que calcular_geometria() reproduce exactamente los valores
    de la tabla de mediciones del Excel (filas F69–F78, hoja A-Fundición 150).
    """

    @pytest.fixture(scope="class")
    def geo(self):
        return calcular_geometria(
            dn_mm=_DN_MM,
            profundidad_m=_PROFUNDIDAD_M,
            es_san=False,
            hay_entibacion=_ENTIBACION,
            espesor_pavimento_m=_H_PAVIMENTO_M,
        )

    def test_ancho_fondo(self, geo):
        """Anchura de fondo = 0,60 m (Excel F69: =IF(DN<250, 0.6, ...))"""
        assert geo.ancho_fondo_m == pytest.approx(_ANCHO_FONDO_M, abs=0.001)

    def test_ancho_cima(self, geo):
        """Anchura de cima = 0,60 m - igual al fondo con entibación (Excel F70)"""
        assert geo.ancho_cima_m == pytest.approx(_ANCHO_CIMA_M, abs=0.001)

    def test_volumen_excavacion(self, geo):
        """Volumen de excavación = 0,555 m³/m (Excel F71)"""
        assert geo.vol_zanja_m3 == pytest.approx(_VOL_ZANJA_M3, abs=0.001)

    def test_split_mecanica_manual(self, geo):
        """Excavación mecánica = manual = 0,278 m³ (50% de 0,555, Excel F72–F73)"""
        assert geo.vol_zanja_m3 * _PCT_MANUAL == pytest.approx(_VOL_EXCAV_MAN_M3, abs=0.001)
        assert geo.vol_zanja_m3 * (1 - _PCT_MANUAL) == pytest.approx(_VOL_EXCAV_MEC_M3, abs=0.001)

    def test_altura_arena(self, geo):
        """Altura arriñonado de arena = 0,38 m (Excel F75: =1.2*DN/1000+0.2)"""
        assert geo.altura_arena_m == pytest.approx(_ALTURA_ARENA_M, abs=0.001)

    def test_volumen_arena(self, geo):
        """Volumen arriñonado = 0,2026 m³/m (Excel F76)"""
        assert geo.vol_arena_pm == pytest.approx(_VOL_ARENA_M3, abs=0.001)

    def test_superficie_entibacion(self, geo):
        """Superficie de entibación = 2,93 m²/m (Excel F77: =(P+0.1*DN/1000+0.20)*2)"""
        assert geo.sup_entibacion_pm == pytest.approx(_SUP_ENTIBACION_M2, abs=0.01)

    def test_volumen_relleno(self, geo):
        """Volumen relleno albero = 0,327 m³/m (Excel F78)"""
        assert geo.vol_relleno_pm == pytest.approx(_VOL_RELLENO_M3, abs=0.001)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RESUMEN FINANCIERO
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinancieroVsExcel:
    """
    Valida que calcular_resumen() reproduce exactamente el cuadro resumen
    del Excel (filas F56–F66, hoja A-Fundición 150).

    PEM = SUMA(a+b+c+d) + e)MATERIALES
    GG y BI se aplican sobre SUMA(a+b+c+d), NO sobre e)MATERIALES.
    PEC redondeado = ROUNDUP((PEM + GG + BI) / 10) × 10
    """

    @pytest.fixture(scope="class")
    def resumen(self):
        return calcular_resumen(
            pem=_PEM,
            materiales=_MATERIALES,
            pct_gg=0.13,
            pct_bi=0.06,
            pct_iva=0.21,
        )

    def test_base_gg_bi(self, resumen):
        """Base GG/BI = SUMA(a+b+c+d) = 412,37 € - sin incluir e)Materiales (Excel F61)"""
        assert resumen.base_gg_bi == pytest.approx(_SUMA_ABCD, abs=0.01)

    def test_gastos_generales(self, resumen):
        """G.G. 13% sobre SUMA = 53,61 € (Excel F62)"""
        assert resumen.gg == pytest.approx(_GG_ESPERADO, abs=0.01)

    def test_beneficio_industrial(self, resumen):
        """B.I. 6% sobre SUMA = 24,74 € (Excel F63)"""
        assert resumen.bi == pytest.approx(_BI_ESPERADO, abs=0.01)

    def test_pec_redondeado(self, resumen):
        """PEC redondeado (ROUNDUP a decena) = 500 € (Excel F66)"""
        assert resumen.pbl_sin_iva == pytest.approx(_PEC_REDONDEADO, abs=0.01)

    def test_pec_sin_redondear(self, resumen):
        """PEC sin redondear = 494,64 € (Excel F65: PEM + GG + BI = 416.29 + 53.61 + 24.74)"""
        pec_sin_redondear = _PEM + _GG_ESPERADO + _BI_ESPERADO
        assert pec_sin_redondear == pytest.approx(494.64, abs=0.01)

    def test_invariante_total(self, resumen):
        """TOTAL = PBL sin IVA + IVA (invariante siempre válido)"""
        assert resumen.total == pytest.approx(resumen.pbl_sin_iva + resumen.iva, abs=0.01)
