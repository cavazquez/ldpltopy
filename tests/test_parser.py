from __future__ import annotations

from ldpltopy.ast import DisplayStmt, NumberLit, StoreStmt, StringLit
from ldpltopy.parser import parse_source


def test_parse_minimal_procedure() -> None:
    src = """
procedure:
display "x" crlf
"""
    prog = parse_source(src)
    assert len(prog.declarations) == 0
    assert len(prog.statements) == 1
    st = prog.statements[0]
    assert isinstance(st, DisplayStmt)


def test_parse_data_and_store() -> None:
    src = """
data:
n is number
procedure:
store 5 in n
"""
    prog = parse_source(src)
    assert len(prog.declarations) == 1
    st = prog.statements[0]
    assert isinstance(st, StoreStmt)
    assert isinstance(st.value, NumberLit)
    assert st.value.value == 5.0


def test_parse_string_var() -> None:
    src = """
data:
s is text
procedure:
store "a" in s
"""
    prog = parse_source(src)
    st = prog.statements[0]
    assert isinstance(st, StoreStmt)
    assert isinstance(st.value, StringLit)
