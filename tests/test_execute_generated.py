from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ldpltopy.parser import parse_source
from ldpltopy.transpiler import transpile

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run_generated(ldpl_name: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    src = (FIXTURES / ldpl_name).read_text(encoding="utf-8")
    py = transpile(parse_source(src))
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
