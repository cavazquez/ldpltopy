from __future__ import annotations

from ldpltopy.lexer import TokenKind, lex_line


def test_lex_number_and_ident() -> None:
    toks = lex_line("store 42 in x")
    assert [t.kind for t in toks] == [
        TokenKind.IDENT,
        TokenKind.NUMBER,
        TokenKind.IDENT,
        TokenKind.IDENT,
    ]
    assert toks[1].number_value == 42.0


def test_lex_string_and_ops() -> None:
    toks = lex_line("in r solve ( a + 3 ) * 4")
    kinds = [t.kind for t in toks]
    assert kinds[0] == TokenKind.IDENT
    assert kinds.count(TokenKind.LPAREN) == 1


def test_lex_comment_stripped() -> None:
    toks = lex_line('display "hi" # end')
    assert len(toks) == 2
    assert toks[1].kind == TokenKind.STRING
