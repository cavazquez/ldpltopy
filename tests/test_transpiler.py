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
        "11_bool_and_or",
        "12_else_if",
        "13_for_loop",
        "14_for_each",
        "15_break_continue",
        "16_arith_stmts",
        "17_text_stmts",
        "18_map_list_index",
        "19_sub_call",
        "20_io",
        "21_io_errorcode",
        "22_include_main",
        "23_case_insensitive",
        "24_solve_list",
        "25_append_file",
    ],
)
def test_fixture_matches_expected(base: str) -> None:
    path = FIXTURES / f"{base}.ldpl"
    ldpl = path.read_text(encoding="utf-8")
    expected = (FIXTURES / f"{base}_expected.py").read_text(encoding="utf-8")
    assert transpile(parse_source(ldpl, file_path=path.resolve())) == expected
