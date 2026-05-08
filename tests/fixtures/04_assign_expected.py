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
    value: float = 0.0
    value = float(100)
    value = float(200)
    print(''.join([_ldpl_number_text(value), '\n']), end="")


if __name__ == "__main__":
    main()
