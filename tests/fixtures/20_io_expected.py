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
    t: str = ""
    try:
        _p = Path('_ldpltopy_test_io.txt')
        _p.parent.mkdir(parents=True, exist_ok=True)
        _p.write_text(str('hello'), encoding='utf-8')
    except OSError:
        pass
    try:
        t = Path('_ldpltopy_test_io.txt').read_text(encoding='utf-8')
    except OSError:
        t = ""
    print(''.join([str(t), '\n']), end="")


if __name__ == "__main__":
    main()
