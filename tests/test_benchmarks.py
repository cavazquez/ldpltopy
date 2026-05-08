from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from ldpltopy.lexer import lex_line
from ldpltopy.parser import parse_source
from ldpltopy.transpiler import transpile

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE = (FIXTURES / "09_while.ldpl").read_text(encoding="utf-8")


def test_bench_lex_all_lines(benchmark: Any) -> None:
    def _run() -> None:
        for line in SAMPLE.splitlines():
            lex_line(line)

    benchmark(_run)


def test_bench_parse(benchmark: Any) -> None:
    benchmark(parse_source, SAMPLE)


def test_bench_transpile(benchmark: Any) -> None:
    prog = parse_source(SAMPLE)

    def _run() -> None:
        transpile(prog)

    benchmark(_run)


def test_bench_run_generated_python(benchmark: Any, tmp_path: Path) -> None:
    py = transpile(parse_source(SAMPLE))
    out = tmp_path / "gen.py"
    out.write_text(py, encoding="utf-8")

    def _run() -> None:
        subprocess.run(
            [sys.executable, str(out)],
            check=True,
            capture_output=True,
            text=True,
        )

    benchmark(_run)
