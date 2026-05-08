"""Generado por ldpltopy — subset LDPL."""

from __future__ import annotations

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


def main() -> None:
    result: float = 0.0
    a: float = 0.0
    a = float(2)
    result = ((float(a) + 3) * 4)
    print(''.join([_ldpl_number_text(result), '\n']), end="")


if __name__ == "__main__":
    main()
