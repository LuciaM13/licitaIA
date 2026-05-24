"""Dataclasses inmutables del modulo de validacion cruzada."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class PartidaReal:
    codigo: str
    capitulo: str
    descripcion: str
    medicion: float
    precio_unitario: float
    importe: float


@dataclass(frozen=True)
class ProyectoReal:
    expediente: str
    nombre: str
    fuente_xlsx: Path
    pem_total: float
    capitulos_real: dict[str, float]
    partidas: list[PartidaReal]


@dataclass(frozen=True)
class MetaProyecto:
    expediente: str
    nombre: str
    capitulos_fuera_alcance: tuple[str, ...]
    notas: tuple[str, ...]
    tipo_obra: str = "instalacion_nueva"
    partidas_fuera_alcance: tuple[str, ...] = ()


@dataclass(frozen=True)
class Huerfana:
    partida: PartidaReal
    motivo: Literal["sin_match_descripcion", "match_pero_precio_fuera_tolerancia"]
    candidato_mas_cercano: dict | None
    similitud: float
    delta_pct: float | None


@dataclass(frozen=True)
class GapCapitulo:
    capitulo: str
    nombre_canonico: str
    pem_real: float
    pem_licitaia: float
    gap_abs: float
    gap_pct: float


@dataclass(frozen=True)
class GapReport:
    expediente: str
    pem_real_bruto: float
    pem_real_ajustado: float
    pem_licitaia: float
    gap_abs: float
    gap_pct: float
    por_capitulo: tuple[GapCapitulo, ...]
    huerfanas: tuple[Huerfana, ...]
    capitulos_excluidos: tuple[str, ...]
