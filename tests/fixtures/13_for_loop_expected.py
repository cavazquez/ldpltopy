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
    i: float = 0.0
    i = float(0)
    _ldpl_for_0_end = float(2)
    _ldpl_for_0_step = float(1)
    if _ldpl_for_0_step >= 0:
        while i < _ldpl_for_0_end:
            print(''.join([_ldpl_number_text(i), '\n']), end="")
            i += _ldpl_for_0_step
    else:
        while i > _ldpl_for_0_end:
            print(''.join([_ldpl_number_text(i), '\n']), end="")
            i += _ldpl_for_0_step
    print(''.join(['x', '\n']), end="")


if __name__ == "__main__":
    main()
