"""Lexer para el subset LDPL (línea a línea, sensible a comillas)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    text: str
    number_value: float | None = None


KEYWORDS: frozenset[str] = frozenset(
    {
        "data",
        "procedure",
        "is",
        "number",
        "numbers",
        "text",
        "texts",
        "store",
        "in",
        "display",
        "print",
        "accept",
        "join",
        "solve",
        "if",
        "then",
        "else",
        "end",
        "while",
        "do",
        "repeat",
        "lf",
        "crlf",
        "equal",
        "not",
        "greater",
        "less",
        "than",
        "or",
        "to",
        "and",
        "for",
        "each",
        "from",
        "step",
        "break",
        "continue",
        "push",
        "list",
        "map",
        "add",
        "subtract",
        "multiply",
        "divide",
        "modulo",
        "floor",
        "ceil",
        "increment",
        "decrement",
        "get",
        "random",
        "length",
        "trim",
        "replace",
        "call",
        "with",
        "return",
        "sub",
        "parameters",
        "local",
        "load",
        "file",
        "write",
        "append",
        "include",
        "of",
    }
)


def _decode_string_escapes(raw: str) -> str:
    """Convierte secuencias de escape LDPL comunes dentro de un literal ya extraído."""
    out: list[str] = []
    i = 0
    escapes = {
        "a": "\a",
        "b": "\b",
        "t": "\t",
        "n": "\n",
        "v": "\v",
        "f": "\f",
        "r": "\r",
        "e": "\x1b",
        "0": "\0",
        "\\": "\\",
        '"': '"',
    }
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            rep = escapes.get(nxt)
            if rep is not None:
                out.append(rep)
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def lex_line(line: str) -> list[Token]:
    """Tokeniza una línea LDPL (sin incluir el salto de línea). Los comentarios # se ignoran."""
    if "#" in line:
        line = line[: line.index("#")]
    s = line.strip()
    if not s:
        return []
    tokens: list[Token] = []
    i = 0
    n = len(s)

    def skip_spaces() -> None:
        nonlocal i
        while i < n and s[i].isspace():
            i += 1

    while i < n:
        skip_spaces()
        if i >= n:
            break
        ch = s[i]
        if ch == "+":
            tokens.append(Token(TokenKind.PLUS, "+"))
            i += 1
            continue
        if ch == "-":
            j = i + 1
            if j < n and s[j].isdigit():
                start = i
                i += 1
                while i < n and (s[i].isdigit() or s[i] == "."):
                    i += 1
                num_s = s[start:i]
                tokens.append(Token(TokenKind.NUMBER, num_s, float(num_s)))
                continue
            tokens.append(Token(TokenKind.MINUS, "-"))
            i += 1
            continue
        if ch == "*":
            tokens.append(Token(TokenKind.STAR, "*"))
            i += 1
            continue
        if ch == "/":
            tokens.append(Token(TokenKind.SLASH, "/"))
            i += 1
            continue
        if ch == "(":
            tokens.append(Token(TokenKind.LPAREN, "("))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token(TokenKind.RPAREN, ")"))
            i += 1
            continue
        if ch == ":":
            tokens.append(Token(TokenKind.COLON, ":"))
            i += 1
            continue
        if ch == '"':
            i += 1
            start = i
            while i < n:
                if s[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if s[i] == '"':
                    raw = s[start:i]
                    decoded = _decode_string_escapes(raw)
                    tokens.append(Token(TokenKind.STRING, decoded))
                    i += 1
                    break
                i += 1
            else:
                msg = "cadena sin cerrar"
                raise ValueError(msg)
            continue
        if ch.isdigit() or (ch == "." and i + 1 < n and s[i + 1].isdigit()):
            start = i
            if ch == ".":
                i += 1
                while i < n and s[i].isdigit():
                    i += 1
            else:
                while i < n and (s[i].isdigit() or s[i] == "."):
                    i += 1
            num_s = s[start:i]
            tokens.append(Token(TokenKind.NUMBER, num_s, float(num_s)))
            continue
        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (s[i].isalnum() or s[i] == "_"):
                i += 1
            word = s[start:i]
            low = word.lower()
            tokens.append(Token(TokenKind.IDENT, low))
            continue
        msg = f"carácter inesperado: {ch!r}"
        raise ValueError(msg)
    return tokens


def line_starts_section(line: str) -> str | None:
    """Devuelve 'data' o 'procedure' si la línea abre sección; considera `data:` y sinónimos."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "#" in stripped:
        stripped = stripped[: stripped.index("#")].strip()
    low = stripped.lower().rstrip(":")
    low = low.removesuffix(":").strip()
    if low in {"data", "-- data --"}:
        return "data"
    if low in {"procedure", "-- procedure --"}:
        return "procedure"
    return None


def is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#")
