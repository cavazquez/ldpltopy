from __future__ import annotations

from pathlib import Path

import pytest

from ldpltopy.parser import parse_source
from ldpltopy.transpiler import transpile

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "base",
    [
        "01_hello",
        "02_string_var",
        "03_number_var",
        "04_assign",
        "05_display",
        "06_concat",
        "07_arithmetic",
        "08_if_else",
        "09_while",
        "10_accept",
    ],
)
def test_fixture_matches_expected(base: str) -> None:
    ldpl = (FIXTURES / f"{base}.ldpl").read_text(encoding="utf-8")
    expected = (FIXTURES / f"{base}_expected.py").read_text(encoding="utf-8")
    assert transpile(parse_source(ldpl)) == expected
