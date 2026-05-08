"""Comparación opcional con el compilador LDPL de referencia (stdout).

Requiere `ldpl` en PATH o la variable de entorno `LDPL_BIN` (p. ej. `/snap/bin/ldpl`).
Si no hay binario, los tests se saltan; CI no necesita LDPL instalado.

Solo se incluyen fixtures que no dependen de rutas de include ni de E/S a ficheros
con nombres fijos en el árbol del repo (salvo lo que resuelva `tmp_path`).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from ldpltopy.parser import parse_source
from ldpltopy.transpiler import transpile

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _ldpl_executable() -> str | None:
    env = (os.environ.get("LDPL_BIN") or "").strip()
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return str(p.resolve())
        return shutil.which(env)
    return shutil.which("ldpl")


def _norm_out(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _run_transpiled(
    ldpl_name: str,
    stdin: str | None,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    path = FIXTURES / ldpl_name
    src = path.read_text(encoding="utf-8")
    py = transpile(parse_source(src, file_path=path.resolve()))
    return subprocess.run(
        [sys.executable, "-c", py],
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,
    )


def _compile_ldpl(exe: str, source: Path, out_bin: Path, workdir: Path) -> None:
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, str(source.resolve()), f"-o={out_bin.resolve()}"]
    proc = subprocess.run(
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        msg = f"ldpl no pudo compilar {source.name} (exit {proc.returncode})\n"
        msg += f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        pytest.fail(msg)


@pytest.fixture(scope="session")
def ldpl_exe_ready() -> str:
    """Salta toda la sesión de comparación si no hay ldpl o no enlaza (p. ej. snap roto)."""
    exe = _ldpl_executable()
    if not exe:
        pytest.skip("Sin ldpl en PATH; define LDPL_BIN=/ruta/al/ldpl si hace falta")
    tmp = Path(tempfile.mkdtemp(prefix="ldpltopy_ldpl_smoke_"))
    src = FIXTURES / "01_hello.ldpl"
    out_bin = tmp / "smoke_bin"
    proc = subprocess.run(
        [exe, str(src.resolve()), f"-o={out_bin.resolve()}"],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        tail = (proc.stderr + proc.stdout)[-800:]
        pytest.skip(
            "ldpl no compila un programa mínimo (¿falta ldpl_lib.cpp / instalación incompleta?). "
            f"Última salida:\n{tail}"
        )
    return exe


# Programas puramente “consola”; sin load/write/include ni subs complejas de rutas.
_LDPL_COMPARE = [
    ("01_hello.ldpl", None),
    ("02_string_var.ldpl", None),
    ("03_number_var.ldpl", None),
    ("04_assign.ldpl", None),
    ("05_display.ldpl", None),
    ("06_concat.ldpl", None),
    ("07_arithmetic.ldpl", None),
    ("08_if_else.ldpl", None),
    ("09_while.ldpl", None),
    ("10_accept.ldpl", "Ada\n"),
    ("11_bool_and_or.ldpl", None),
    ("12_else_if.ldpl", None),
    ("13_for_loop.ldpl", None),
    ("14_for_each.ldpl", None),
    ("15_break_continue.ldpl", None),
]


@pytest.mark.parametrize(("ldpl_name", "stdin"), _LDPL_COMPARE, ids=[x[0] for x in _LDPL_COMPARE])
def test_reference_stdout_matches_transpiled(
    ldpl_exe_ready: str,
    ldpl_name: str,
    stdin: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exe = ldpl_exe_ready

    monkeypatch.chdir(tmp_path)
    src = FIXTURES / ldpl_name
    if not src.is_file():
        pytest.fail(f"fixture ausente: {src}")

    out_bin = tmp_path / "ldpl_reference_bin"
    _compile_ldpl(exe, src, out_bin, tmp_path)

    proc_ldpl = subprocess.run(
        [str(out_bin.resolve())],
        cwd=tmp_path,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if proc_ldpl.returncode != 0:
        pytest.fail(
            f"binario ldpl falló (exit {proc_ldpl.returncode})\n"
            f"stdout:\n{proc_ldpl.stdout!r}\nstderr:\n{proc_ldpl.stderr!r}"
        )

    proc_py = _run_transpiled(ldpl_name, stdin, tmp_path)

    assert _norm_out(proc_ldpl.stdout) == _norm_out(proc_py.stdout), (
        f"stdout distinto para {ldpl_name}\n"
        f"--- ldpl ---\n{proc_ldpl.stdout!r}\n--- ldpltopy ---\n{proc_py.stdout!r}"
    )
