"""
Geometría de zanja — fórmulas puras verificadas contra el Excel EMASESA.

Este módulo no importa nada externo al dominio. Todas las funciones son
puras: dado el mismo input producen el mismo output sin efectos laterales.

Fórmulas de referencia:
  ABA — hoja 'A-Fundición 150' del Excel de valoración EMASESA (abril 2024)
  SAN — hoja 'S-Gres 300' del mismo Excel
"""

from __future__ import annotations

import math
from dataclasses import dataclass


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
    SAN (Excel H70): =(P + 0.1*DN/1000 + 0.15) * 2
    """
    extra = 0.15 if es_san else 0.20
    return (P + 0.1 * dn_mm / 1000.0 + extra) * 2.0


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
    P = max(profundidad_m, 0.0)
    h_pav = max(espesor_pavimento_m, 0.0)

    # Profundidad efectiva de excavación (descontado el pavimento ya demolido)
    clearance = 0.15 + 0.1 * dn_mm / 1000.0
    P_exc = max(P + clearance - h_pav, 0.0)

    # Dimensiones horizontales
    W_fondo = _ancho_fondo(dn_mm, es_san)
    W_cima = _ancho_cima(P_exc, hay_entibacion, W_fondo)
    W_media = (W_fondo + W_cima) / 2.0
    W_recub = _ancho_recubrimiento(dn_mm, es_san, hay_entibacion, W_fondo)

    # Sección transversal del tubo (diámetro exterior = 1.2 × DN)
    d_ext = 1.2 * dn_mm / 1000.0
    vol_tubo_pm = math.pi / 4.0 * d_ext ** 2

    # Volumen de zanja (sección trapezoidal × longitud unitaria)
    vol_zanja_pm = W_media * P_exc

    # Arriñonado de arena
    h_arena = _altura_arena(dn_mm, es_san)
    W_arena_media = (W_fondo + W_recub) / 2.0
    vol_arena_pm = max(W_arena_media * h_arena - vol_tubo_pm, 0.0)

    # Relleno de albero
    vol_relleno_pm = max(vol_zanja_pm - vol_arena_pm - vol_tubo_pm, 0.0)

    # Entibación
    sup_entibacion_pm = (
        _superficie_entibacion_pm(P, dn_mm, es_san) if hay_entibacion else 0.0
    )

    return GeometriaZanja(
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
