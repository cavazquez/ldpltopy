"""Interfaz de línea de comandos para ldpltopy."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ldpltopy.parser import ParseError, parse_source
from ldpltopy.transpiler import transpile

app = typer.Typer(
    help="Transpilador de un subset de LDPL a Python 3.13",
    no_args_is_help=True,
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def _root(
    ctx: typer.Context,
    entrada: Annotated[
        Path | None,
        typer.Argument(help="Archivo fuente .ldpl"),
    ] = None,
    salida: Annotated[
        Path | None,
        typer.Option("-o", "--output", help="Archivo Python de salida"),
    ] = None,
) -> None:
    """Lee un programa LDPL y emite Python por stdout o a un archivo."""
    if ctx.invoked_subcommand is not None:
        return
    if entrada is None:
        typer.echo("Indicá un archivo .ldpl (p. ej. ldpltopy hola.ldpl).", err=True)
        raise typer.Exit(code=2)
    if not entrada.is_file():
        typer.secho(f"No existe el archivo: {entrada}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    texto = entrada.read_text(encoding="utf-8")
    try:
        programa = parse_source(texto)
    except ParseError as err:
        typer.secho(str(err), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from err
    except ValueError as err:
        typer.secho(f"Error léxico: {err}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from err
    python = transpile(programa)
    if salida is None:
        typer.echo(python, nl=False)
        if not python.endswith("\n"):
            typer.echo()
    else:
        salida.write_text(python, encoding="utf-8")


def main() -> None:
    """Punto de entrada para el script de consola y `python -m ldpltopy`."""
    app()


if __name__ == "__main__":
    main()
