"""Preprocesador mínimo: resuelve `include \"ruta\"` línea a línea."""

from __future__ import annotations

from pathlib import Path

from ldpltopy.lexer import TokenKind, lex_line


def expand_includes(source: str, base_path: Path, seen: set[Path] | None = None) -> str:
    """Inserta el contenido de cada `include \"archivo\"` relativo a `base_path`."""
    if seen is None:
        seen = set()
    out_lines: list[str] = []
    for line in source.splitlines():
        toks = lex_line(line)
        if (
            len(toks) >= 2
            and toks[0].kind == TokenKind.IDENT
            and toks[0].text == "include"
            and toks[1].kind == TokenKind.STRING
        ):
            rel = toks[1].text
            path = (base_path.parent / rel).resolve()
            if path in seen:
                msg = f"include cíclico o duplicado: {path}"
                raise ValueError(msg)
            if not path.is_file():
                msg = f"include: no existe el archivo {path}"
                raise ValueError(msg)
            seen.add(path)
            nested = path.read_text(encoding="utf-8")
            expanded = expand_includes(nested, path, seen)
            seen.discard(path)
            out_lines.extend(expanded.splitlines())
        else:
            out_lines.append(line)
    return "\n".join(out_lines)
