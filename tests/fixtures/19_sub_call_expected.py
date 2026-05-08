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
    r: float = 0.0
    def ldpl_sub_addtwo(a_box, b_box, c_box) -> None:
        c_box[0] = (float(a_box[0]) + float(b_box[0]))
    _ldpl_cb_0 = [float(4)]
    _ldpl_cb_1 = [float(5)]
    _ldpl_cb_2 = [r]
    ldpl_sub_addtwo(_ldpl_cb_0, _ldpl_cb_1, _ldpl_cb_2)
    r = _ldpl_cb_2[0]
    print(''.join([_ldpl_number_text(r), '\n']), end="")


if __name__ == "__main__":
    main()
