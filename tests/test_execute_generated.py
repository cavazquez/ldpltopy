from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ldpltopy.parser import parse_source
from ldpltopy.transpiler import transpile

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run_generated(ldpl_name: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    path = FIXTURES / ldpl_name
    src = path.read_text(encoding="utf-8")
    py = transpile(parse_source(src, file_path=path.resolve()))
    return subprocess.run(
        [sys.executable, "-c", py],
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
    )


def test_execute_hello() -> None:
    r = _run_generated("01_hello.ldpl")
    assert r.stdout == "Hello World!\n"


def test_execute_while_output() -> None:
    r = _run_generated("09_while.ldpl")
    assert r.stdout == "3\n2\n1\ndone\n"


def test_execute_accept_greets() -> None:
    r = _run_generated("10_accept.ldpl", stdin="Ada\n")
    assert r.stdout == "Name? \nHi Ada\n"


def test_execute_if_else_branch() -> None:
    r = _run_generated("08_if_else.ldpl")
    assert r.stdout == "big\n"


def test_execute_bool_and_or() -> None:
    r = _run_generated("11_bool_and_or.ldpl")
    assert r.stdout == "ok\nn\n"


def test_execute_else_if_branch() -> None:
    r = _run_generated("12_else_if.ldpl")
    assert r.stdout == "M\n"


def test_execute_for_loop() -> None:
    r = _run_generated("13_for_loop.ldpl")
    assert r.stdout == "0\n1\nx\n"


def test_execute_for_each_letters() -> None:
    r = _run_generated("14_for_each.ldpl")
    assert r.stdout == "A\nB\n"


def test_execute_break_continue() -> None:
    r = _run_generated("15_break_continue.ldpl")
    assert r.stdout == "1\n3\ndone\n"


def test_execute_text_trim_replace() -> None:
    r = _run_generated("17_text_stmts.ldpl")
    assert r.stdout == "yo\n"


def test_execute_map_and_list_index() -> None:
    r = _run_generated("18_map_list_index.ldpl")
    assert r.stdout == "7\n2\n"


def test_execute_sub_call() -> None:
    r = _run_generated("19_sub_call.ldpl")
    assert r.stdout == "9\n"


def test_execute_io_write_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    r = _run_generated("20_io.ldpl")
    assert r.stdout == "hello\n"


def test_execute_io_errorcode_sync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    r = _run_generated("21_io_errorcode.ldpl")
    assert r.stdout == "1\nThe file could not be opened.\n"


def test_execute_case_insensitive() -> None:
    r = _run_generated("23_case_insensitive.ldpl")
    assert r.stdout == "7\n"


def test_execute_solve_list_index() -> None:
    r = _run_generated("24_solve_list.ldpl")
    assert r.stdout == "99\n"


def test_execute_append_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    r = _run_generated("25_append_file.ldpl")
    assert r.stdout == "AB\n"


def test_execute_include_fragment() -> None:
    r = _run_generated("22_include_main.ldpl")
    assert r.stdout == "inc\n"
