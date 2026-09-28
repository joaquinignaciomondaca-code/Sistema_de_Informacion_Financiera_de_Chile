"""Lector estricto de registros MB1 de longitud fija (no de B1 tabulado).

Diseño físico según manuales SBIF/CMF: código contable de 7/9 dígitos,
seguido por total y cuatro desgloses s9(14), cada uno con signo. MM CLP
antes de 2022; pesos desde 2022. No extrapolar el diseño de MB1 a TXT B1
publicados sin inspeccionar su especificación. No publica datos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BalanceLine:
    cuenta: str
    total: Decimal
    monedas: tuple[Decimal, Decimal, Decimal, Decimal]
    unidad: str


def parse_record(line: str, period: str) -> BalanceLine:
    if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", period):
        raise ValueError("Período MB1 inválido")
    old = period < "2022-01"
    width = 7 if old else 9
    if len(line) != width + 5 * 15 or not line[:width].isascii() or not line[:width].isdigit():
        raise ValueError("Longitud o código contable MB1 inválido")
    chunks = [line[width + i * 15:width + (i + 1) * 15] for i in range(5)]
    if any(re.fullmatch(r"[+-][0-9]{14}", c) is None for c in chunks):
        raise ValueError("Campo s9(14) MB1 inválido")
    amounts = [Decimal(c) for c in chunks]
    if amounts[0] != sum(amounts[1:]):
        raise ValueError("Total MB1 no cuadra con cuatro monedas")
    return BalanceLine(line[:width], amounts[0], tuple(amounts[1:]),
                       "millones_clp" if old else "pesos_clp")
