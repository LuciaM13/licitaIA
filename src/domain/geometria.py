"""
Geometría de zanja - fórmulas puras verificadas contra el Excel EMASESA.

Este módulo no importa nada externo al dominio. Todas las funciones son
puras: dado el mismo input producen el mismo output sin efectos laterales.

Fórmulas de referencia:
  ABA - hoja 'A-Fundición 150' del Excel de valoración EMASESA (abril 2024)
  SAN - hoja 'S-Gres 300' del mismo Excel
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resultado de geometría (valor object inmutable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GeometriaZanja:
    """Resultado completo de los cálculos geométricos de una zanja."""
    ancho_fondo_m: float
    ancho_cima_m: float
    ancho_recub_m: float
    altura_arena_m: float
    P_exc_m: float           # Profundidad efectiva de excavación (descontado pavimento)
    vol_zanja_m3: float      # Por metro lineal
    vol_tubo_pm: float       # Sección transversal del tubo (m³/m)
    vol_arena_pm: float      # Volumen de arriñonado por metro lineal
    vol_relleno_pm: float    # Volumen de relleno por metro lineal
    sup_entibacion_pm: float # Superficie de entibación por metro lineal (m²/m)


# ---------------------------------------------------------------------------
# Funciones auxiliares internas
# ---------------------------------------------------------------------------

def _ancho_fondo(dn_mm: int, es_san: bool) -> float:
    """
    Ancho de fondo de zanja.

    ABA (Excel H69): =IF(DN<250, 0.6, 1.2*DN/1000+0.4)
    SAN (Excel H62): =1.2*DN/1000+1.5
    """
    if es_san:
        return 1.2 * dn_mm / 1000.0 + 1.5
    return 0.6 if dn_mm < 250 else (1.2 * dn_mm / 1000.0 + 0.4)


def _ancho_cima(P_exc: float, hay_entibacion: bool, ancho_fondo: float) -> float:
    """
    Ancho de zanja en la cima (nivel de pavimento).

    Con entibación → paredes verticales → igual al fondo.
    Sin entibación → talud 0.4:1 aplicado sobre P_exc.

    ABA (Excel H70): =IF(entib, H69, P_exc*0.4+H69)
    """
    if hay_entibacion:
        return ancho_fondo
    return P_exc * 0.4 + ancho_fondo


def _ancho_recubrimiento(dn_mm: int, es_san: bool, hay_entibacion: bool,
                         ancho_fondo: float) -> float:
    """
    Ancho de zanja a la altura del arriñonado de arena.

    ABA (Excel H74): =IF(entib, H69, (1.2*DN/1000+0.2)*0.4+H69)
    SAN (Excel H67): =IF(entib, H62, (1.2*DN/1000+0.3)*0.4+H62)
    """
    if hay_entibacion:
        return ancho_fondo
    offset = 0.3 if es_san else 0.2
    return (1.2 * dn_mm / 1000.0 + offset) * 0.4 + ancho_fondo


def _altura_arena(dn_mm: int, es_san: bool) -> float:
    """
    Altura del lecho de arriñonado.

    ABA (Excel H75): =1.2*DN/1000+0.2
    SAN (Excel H68): =1.2*DN/1000+0.3
    """
    return 1.2 * dn_mm / 1000.0 + (0.3 if es_san else 0.2)


def _superficie_entibacion_pm(P: float, dn_mm: int, es_san: bool) -> float:
    """
    Superficie de entibación por metro lineal de zanja (m²/m).

    ABA (Excel H77): =(P + 0.1*DN/1000 + 0.20) * 2
    SAN (Excel H17, obra civil): =(P + 1) * 2 * 1.1
      Nota: la hoja SAN tiene dos fórmulas de entibación. H70 (tabla geometría)
      usa (P+0.1*DN/100+0.15)*2, pero la partida de obra civil (H17) usa la
      fórmula simplificada (P+1)*2*1.1, que es la que aplica al coste real.
      El "+1 m" refleja la holgura adicional de trabajo en zanjas de saneamiento
      y el factor 1.1 incorpora un 10% de solapamiento/desperdicio.
    """
    if es_san:
        return (P + 1.0) * 2.0 * 1.1
    return (P + 0.1 * dn_mm / 1000.0 + 0.20) * 2.0


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_geometria(
    dn_mm: int,
    profundidad_m: float,
    es_san: bool,
    hay_entibacion: bool,
    espesor_pavimento_m: float = 0.0,
) -> GeometriaZanja:
    """
    Calcula todos los parámetros geométricos de la zanja por metro lineal.

    Args:
        dn_mm: Diámetro nominal de la tubería en milímetros.
        profundidad_m: Profundidad de zanja (cota roja) en metros.
        es_san: True si la red es saneamiento, False si es abastecimiento.
        hay_entibacion: True si el motor experto ha decidido que hay entibación.
        espesor_pavimento_m: Espesor de pavimento a descontar (para cánones RCD).

    Returns:
        GeometriaZanja con todos los volúmenes y dimensiones por metro lineal.
    """
    red_label = "SAN" if es_san else "ABA"

    if dn_mm <= 0:
        logger.warning("[GEO-%s] DN inválido (%d mm) - los resultados no tendrán sentido", red_label, dn_mm)
    if profundidad_m <= 0:
        logger.warning("[GEO-%s] Profundidad inválida (%.2f m) - los resultados no tendrán sentido", red_label, profundidad_m)

    P = max(profundidad_m, 0.0)
    h_pav = max(espesor_pavimento_m, 0.0)
    logger.debug("[GEO-%s] Entrada: DN=%d P=%.2f h_pav=%.3f entib=%s",
                 red_label, dn_mm, profundidad_m, espesor_pavimento_m, hay_entibacion)

    # Profundidad efectiva de excavación (descontado el pavimento ya demolido)
    clearance = 0.15 + 0.1 * dn_mm / 1000.0
    P_exc = max(P + clearance - h_pav, 0.0)
    logger.debug("[GEO-%s] P_exc: P(%.2f) + clearance(%.4f) - h_pav(%.3f) = %.4f",
                 red_label, P, clearance, h_pav, P_exc)

    # Dimensiones horizontales
    W_fondo = _ancho_fondo(dn_mm, es_san)
    W_cima = _ancho_cima(P_exc, hay_entibacion, W_fondo)
    W_media = (W_fondo + W_cima) / 2.0
    W_recub = _ancho_recubrimiento(dn_mm, es_san, hay_entibacion, W_fondo)
    logger.debug("[GEO-%s] Anchos: fondo=%.4f cima=%.4f media=%.4f recub=%.4f",
                 red_label, W_fondo, W_cima, W_media, W_recub)

    # Sección transversal del tubo (diámetro exterior = 1.2 × DN)
    d_ext = 1.2 * dn_mm / 1000.0
    vol_tubo_pm = math.pi / 4.0 * d_ext ** 2
    logger.debug("[GEO-%s] Tubo: d_ext=%.4f → vol_tubo=%.6f m³/m",
                 red_label, d_ext, vol_tubo_pm)

    # Volumen de zanja (sección trapezoidal × longitud unitaria)
    vol_zanja_pm = W_media * P_exc
    logger.debug("[GEO-%s] Zanja: W_media(%.4f) × P_exc(%.4f) = %.6f m³/m",
                 red_label, W_media, P_exc, vol_zanja_pm)

    # Arriñonado de arena
    h_arena = _altura_arena(dn_mm, es_san)
    W_arena_media = (W_fondo + W_recub) / 2.0
    vol_arena_pm = max(W_arena_media * h_arena - vol_tubo_pm, 0.0)
    logger.debug("[GEO-%s] Arena: h=%.4f W_media_arena=%.4f → bruto=%.6f - tubo=%.6f = %.6f m³/m",
                 red_label, h_arena, W_arena_media,
                 W_arena_media * h_arena, vol_tubo_pm, vol_arena_pm)

    # Relleno de albero
    vol_relleno_pm = max(vol_zanja_pm - vol_arena_pm - vol_tubo_pm, 0.0)
    logger.debug("[GEO-%s] Relleno: zanja(%.6f) - arena(%.6f) - tubo(%.6f) = %.6f m³/m",
                 red_label, vol_zanja_pm, vol_arena_pm, vol_tubo_pm, vol_relleno_pm)

    # Entibación
    sup_entibacion_pm = (
        _superficie_entibacion_pm(P, dn_mm, es_san) if hay_entibacion else 0.0
    )
    if hay_entibacion:
        logger.debug("[GEO-%s] Entibación: P=%.2f → sup=%.4f m²/m (fórmula %s)",
                     red_label, P, sup_entibacion_pm,
                     "(P+1)*2*1.1" if es_san else "(P+0.1*DN/1000+0.20)*2")
    else:
        logger.debug("[GEO-%s] Sin entibación", red_label)

    geo = GeometriaZanja(
        ancho_fondo_m=round(W_fondo, 4),
        ancho_cima_m=round(W_cima, 4),
        ancho_recub_m=round(W_recub, 4),
        altura_arena_m=round(h_arena, 4),
        P_exc_m=round(P_exc, 4),
        vol_zanja_m3=round(vol_zanja_pm, 6),
        vol_tubo_pm=round(vol_tubo_pm, 6),
        vol_arena_pm=round(vol_arena_pm, 6),
        vol_relleno_pm=round(vol_relleno_pm, 6),
        sup_entibacion_pm=round(sup_entibacion_pm, 4),
    )
    logger.debug("[GEO-%s] RESULTADO: P_exc=%.4f W_fondo=%.4f W_cima=%.4f "
                 "vol_zanja=%.6f vol_arena=%.6f vol_rell=%.6f sup_entib=%.4f",
                 red_label, geo.P_exc_m, geo.ancho_fondo_m, geo.ancho_cima_m,
                 geo.vol_zanja_m3, geo.vol_arena_pm, geo.vol_relleno_pm, geo.sup_entibacion_pm)
    return geo
