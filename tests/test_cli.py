from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ldpltopy.cli import app

FIXTURES = Path(__file__).resolve().parent / "fixtures"
runner = CliRunner()


def test_cli_stdout(tmp_path: Path) -> None:
    src = FIXTURES / "01_hello.ldpl"
    result = runner.invoke(app, [str(src)])
    assert result.exit_code == 0
    expected = (FIXTURES / "01_hello_expected.py").read_text(encoding="utf-8")
    assert result.stdout == expected


def test_cli_output_file(tmp_path: Path) -> None:
    src = FIXTURES / "01_hello.ldpl"
    out = tmp_path / "out.py"
    result = runner.invoke(app, ["-o", str(out), str(src)])
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8") == (FIXTURES / "01_hello_expected.py").read_text(
        encoding="utf-8"
    )
