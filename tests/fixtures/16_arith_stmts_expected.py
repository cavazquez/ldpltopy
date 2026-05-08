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
    a: float = 0.0
    b: float = 0.0
    c: float = 0.0
    a = float(5)
    b = (float(2) + float(3))
    c = (float(10) - float(1))
    a = (float(b) * float(2))
    b = (float(8) / float(2))
    c = (float(7) % float(3))
    a = float(math.floor(float(2.9)))
    b = float(b) + 1.0
    c = float(c) - 1.0


if __name__ == "__main__":
    main()
