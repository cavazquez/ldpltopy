"""Generado por ldpltopy — subset LDPL."""

from __future__ import annotations

import math
import random
from pathlib import Path

def _ldpl_text_to_number(t: str) -> float:
    s = t.strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

def _ldpl_number_text(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return str(v)

def _ldpl_map_key_num(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return str(v)


def main() -> None:
    m: dict[str, float] = {}
    k: str = ""
    lst: list[float] = []
    k = 'x'
    m[str(k)] = float(7)
    lst.append(float(1))
    lst.append(float(2))
    lst[int(float(0))] = float(9)
    print(''.join([_ldpl_number_text(m[str(k)]), '\n']), end="")
    print(''.join([_ldpl_number_text(lst[int(float(1))]), '\n']), end="")


if __name__ == "__main__":
    main()
