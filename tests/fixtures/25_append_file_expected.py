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
    buf: str = ""
    try:
        _p = Path('_ldpltopy_append.txt')
        _p.parent.mkdir(parents=True, exist_ok=True)
        _p.write_text(str('A'), encoding='utf-8')
    except OSError:
        pass
    try:
        _p = Path('_ldpltopy_append.txt')
        _p.parent.mkdir(parents=True, exist_ok=True)
        with _p.open('a', encoding='utf-8') as _f:
            _f.write(str('B'))
    except OSError:
        pass
    try:
        buf = Path('_ldpltopy_append.txt').read_text(encoding='utf-8')
    except OSError:
        buf = ""
    print(''.join([str(buf), '\n']), end="")


if __name__ == "__main__":
    main()
