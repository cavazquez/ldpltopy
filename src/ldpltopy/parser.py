"""Parser recursivo para el subset LDPL soportado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from ldpltopy.ast import (
    AcceptStmt,
    CmpOp,
    DisplayPart,
    DisplayStmt,
    Expr,
    IfStmt,
    JoinStmt,
    MathBin,
    MathExpr,
    MathNeg,
    NumberLit,
    Program,
    SolveStmt,
    Statement,
    StoreStmt,
    StringLit,
    VarDecl,
    VarRef,
    WhileStmt,
)
from ldpltopy.lexer import Token, TokenKind, is_blank_or_comment, lex_line, line_starts_section


class ParseError(Exception):
    __slots__ = ("message", "line_no")

    def __init__(self, message: str, line_no: int) -> None:
        super().__init__(message)
        self.message = message
        self.line_no = line_no

    def __str__(self) -> str:  # pragma: no cover - mensaje legible
        return f"Línea {self.line_no}: {self.message}"


@dataclass(slots=True)
class _Parser:
    lines: list[str]
    i: int

    def _err(self, msg: str) -> ParseError:
        line_no = self.i + 1 if self.i < len(self.lines) else len(self.lines)
        return ParseError(msg, line_no)

    def _skip_blanks(self) -> None:
        while self.i < len(self.lines) and is_blank_or_comment(self.lines[self.i]):
            self.i += 1

    def _tokens_here(self) -> list[Token]:
        return lex_line(self.lines[self.i])

    def _expect_ident(self, tok: Token, ctx: str) -> str:
        if tok.kind != TokenKind.IDENT:
            raise self._err(f"se esperaba identificador ({ctx})")
        return tok.text

    def parse_program(self) -> Program:
        self._skip_blanks()
        decls: list[VarDecl] = []
        if self.i < len(self.lines) and line_starts_section(self.lines[self.i]) == "data":
            self.i += 1
            while True:
                self._skip_blanks()
                if self.i >= len(self.lines):
                    raise self._err("fin de archivo dentro de data: sin procedure:")
                if line_starts_section(self.lines[self.i]) == "procedure":
                    break
                decls.append(self._parse_decl())
        self._skip_blanks()
        if self.i >= len(self.lines) or line_starts_section(self.lines[self.i]) != "procedure":
            raise self._err("se requiere sección procedure:")
        self.i += 1
        stmts: list[Statement] = []
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                break
            stmt = self._parse_statement()
            if stmt is None:
                continue
            stmts.append(stmt)
        return Program(tuple(decls), tuple(stmts))

    def _parse_decl(self) -> VarDecl:
        toks = self._tokens_here()
        if len(toks) < 3:
            raise self._err("declaración inválida en data:")
        name = self._expect_ident(toks[0], "variable")
        if toks[1].text != "is":
            raise self._err("se esperaba 'is' en declaración")
        type_tok = toks[2].text
        if type_tok in {"number", "numbers"}:
            is_number = True
        elif type_tok in {"text", "texts"}:
            is_number = False
        else:
            raise self._err("solo se soportan tipos number y text en data:")
        if len(toks) != 3:
            raise self._err("demasiados tokens en declaración de variable")
        self.i += 1
        return VarDecl(name, is_number)

    def _parse_statement(self) -> Statement | None:
        self._skip_blanks()
        if self.i >= len(self.lines):
            return None
        toks = self._tokens_here()
        if not toks:
            self.i += 1
            return self._parse_statement()
        head = toks[0].text
        if head == "if":
            return self._parse_if()
        if head == "while":
            return self._parse_while()
        if head == "store":
            st_store = self._parse_store(toks)
            self.i += 1
            return st_store
        if head == "display":
            st_display = self._parse_display(toks)
            self.i += 1
            return st_display
        if head == "print":
            st_print = self._parse_print(toks)
            self.i += 1
            return st_print
        if head == "accept":
            st_accept = self._parse_accept(toks)
            self.i += 1
            return st_accept
        if head == "in" and len(toks) >= 3 and toks[2].text == "join":
            st_join = self._parse_join(toks)
            self.i += 1
            return st_join
        if head == "in" and len(toks) >= 3 and toks[2].text == "solve":
            st_solve = self._parse_solve(toks)
            self.i += 1
            return st_solve
        raise self._err(f"sentencia no soportada: {head}")

    def _parse_store(self, toks: list[Token]) -> StoreStmt:
        if len(toks) < 4 or toks[-2].text != "in":
            raise self._err("sintaxis: store <valor> in <variable>")
        target = self._expect_ident(toks[-1], "destino de store")
        val_toks = toks[1:-2]
        if len(val_toks) != 1:
            raise self._err("store admite un único valor en este subset")
        value = self._parse_atomic_expr(val_toks[0])
        return StoreStmt(value, target)

    def _parse_display(self, toks: list[Token]) -> DisplayStmt:
        parts = self._parse_display_parts(toks[1:])
        return DisplayStmt(parts)

    def _parse_print(self, toks: list[Token]) -> DisplayStmt:
        inner = self._parse_display_parts(toks[1:])
        return DisplayStmt(tuple([*inner, "crlf"]))

    def _parse_display_parts(self, toks: list[Token]) -> tuple[DisplayPart, ...]:
        out: list[DisplayPart] = []
        for t in toks:
            if t.kind == TokenKind.IDENT and t.text in {"lf", "crlf"}:
                br: Literal["lf", "crlf"] = cast(Literal["lf", "crlf"], t.text)
                out.append(br)
                continue
            out.append(self._parse_atomic_expr(t))
        return tuple(out)

    def _parse_join(self, toks: list[Token]) -> JoinStmt:
        if len(toks) < 4:
            raise self._err("sintaxis: in <var> join <partes...>")
        target = self._expect_ident(toks[1], "destino de join")
        if toks[2].text != "join":
            raise self._err("se esperaba join")
        parts = self._parse_display_parts(toks[3:])
        return JoinStmt(target, parts)

    def _parse_solve(self, toks: list[Token]) -> SolveStmt:
        if len(toks) < 4:
            raise self._err("sintaxis: in <var> solve <expr>")
        target = self._expect_ident(toks[1], "destino de solve")
        if toks[2].text != "solve":
            raise self._err("se esperaba solve")
        math_toks = toks[3:]
        if not math_toks:
            raise self._err("expresión matemática vacía")
        expr, pos = self._parse_math_expr(math_toks, 0)
        if pos != len(math_toks):
            raise self._err("tokens sobrantes en expresión matemática")
        return SolveStmt(target, expr)

    def _parse_accept(self, toks: list[Token]) -> AcceptStmt:
        if len(toks) != 2:
            raise self._err("sintaxis: accept <variable>")
        name = self._expect_ident(toks[1], "accept")
        return AcceptStmt(name)

    def _parse_atomic_expr(self, tok: Token) -> Expr:
        if tok.kind == TokenKind.NUMBER and tok.number_value is not None:
            return NumberLit(tok.number_value)
        if tok.kind == TokenKind.STRING:
            return StringLit(tok.text)
        if tok.kind == TokenKind.IDENT:
            return VarRef(tok.text)
        raise self._err("valor inválido en expresión")

    def _parse_if(self) -> IfStmt:
        toks = self._tokens_here()
        if not toks or toks[0].text != "if":
            raise self._err("if mal formado")
        if toks[-1].text != "then":
            raise self._err("se esperaba then al final de la línea if")
        cond_toks = toks[1:-1]
        left, op, right, pos = self._parse_condition(cond_toks, 0)
        if pos != len(cond_toks):
            raise self._err("condición if con tokens extra")
        self.i += 1
        then_body = self._parse_block_until_else_or_end_if()
        else_body: tuple[Statement, ...] | None
        self._skip_blanks()
        next_toks = self._tokens_here()
        if not next_toks:
            raise self._err("cuerpo if vacío o sin cierre")
        if next_toks[0].text == "else":
            self.i += 1
            else_stmts = self._parse_block_until_end_if()
            else_body = tuple(else_stmts)
        else:
            else_body = None
        self._consume_end_if()
        return IfStmt(left, op, right, tuple(then_body), else_body)

    def _parse_while(self) -> WhileStmt:
        toks = self._tokens_here()
        if not toks or toks[0].text != "while":
            raise self._err("while mal formado")
        if toks[-1].text != "do":
            raise self._err("se esperaba do al final de la línea while")
        cond_toks = toks[1:-1]
        left, op, right, pos = self._parse_condition(cond_toks, 0)
        if pos != len(cond_toks):
            raise self._err("condición while con tokens extra")
        self.i += 1
        body = self._parse_block_until_repeat()
        return WhileStmt(left, op, right, tuple(body))

    def _parse_block_until_else_or_end_if(self) -> list[Statement]:
        out: list[Statement] = []
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                raise self._err("fin de archivo dentro de if (falta end if)")
            toks = self._tokens_here()
            if not toks:
                self.i += 1
                continue
            if toks[0].text == "else" and len(toks) == 1:
                return out
            if toks[0].text == "end" and len(toks) == 2 and toks[1].text == "if":
                return out
            nxt = self._parse_statement()
            if nxt is None:
                raise self._err("sentencia esperada")
            out.append(nxt)

    def _parse_block_until_end_if(self) -> list[Statement]:
        out: list[Statement] = []
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                raise self._err("fin de archivo dentro de else (falta end if)")
            toks = self._tokens_here()
            if not toks:
                self.i += 1
                continue
            if toks[0].text == "end" and len(toks) == 2 and toks[1].text == "if":
                return out
            nxt = self._parse_statement()
            if nxt is None:
                raise self._err("sentencia esperada")
            out.append(nxt)

    def _consume_end_if(self) -> None:
        self._skip_blanks()
        if self.i >= len(self.lines):
            raise self._err("falta end if")
        toks = self._tokens_here()
        if len(toks) == 2 and toks[0].text == "end" and toks[1].text == "if":
            self.i += 1
            return
        raise self._err("se esperaba end if")

    def _parse_block_until_repeat(self) -> list[Statement]:
        out: list[Statement] = []
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                raise self._err("fin de archivo dentro de while (falta repeat)")
            toks = self._tokens_here()
            if not toks:
                self.i += 1
                continue
            if len(toks) == 1 and toks[0].text == "repeat":
                self.i += 1
                return out
            nxt = self._parse_statement()
            if nxt is None:
                raise self._err("sentencia esperada")
            out.append(nxt)

    def _parse_condition(self, toks: list[Token], pos: int) -> tuple[Expr, CmpOp, Expr, int]:
        if pos >= len(toks):
            raise self._err("condición vacía")
        left = self._parse_atomic_expr(toks[pos])
        pos += 1
        if pos >= len(toks) or toks[pos].text != "is":
            raise self._err("se esperaba is en condición")
        pos += 1
        op, pos = self._parse_relop(toks, pos)
        if pos >= len(toks):
            raise self._err("falta lado derecho en condición")
        right = self._parse_atomic_expr(toks[pos])
        pos += 1
        return left, op, right, pos

    def _parse_relop(self, toks: list[Token], pos: int) -> tuple[CmpOp, int]:
        if pos >= len(toks):
            raise self._err("relación incompleta")
        t0 = toks[pos].text
        if t0 == "equal" and pos + 1 < len(toks) and toks[pos + 1].text == "to":
            return CmpOp.EQ, pos + 2
        if (
            t0 == "not"
            and pos + 2 < len(toks)
            and toks[pos + 1].text == "equal"
            and toks[pos + 2].text == "to"
        ):
            return CmpOp.NE, pos + 3
        if t0 == "greater" and pos + 1 < len(toks) and toks[pos + 1].text == "than":
            if (
                pos + 4 < len(toks)
                and toks[pos + 2].text == "or"
                and toks[pos + 3].text == "equal"
                and toks[pos + 4].text == "to"
            ):
                return CmpOp.GE, pos + 5
            return CmpOp.GT, pos + 2
        if t0 == "less" and pos + 1 < len(toks) and toks[pos + 1].text == "than":
            if (
                pos + 4 < len(toks)
                and toks[pos + 2].text == "or"
                and toks[pos + 3].text == "equal"
                and toks[pos + 4].text == "to"
            ):
                return CmpOp.LE, pos + 5
            return CmpOp.LT, pos + 2
        raise self._err("operador relacional no soportado en este subset")

    def _parse_math_expr(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        return self._parse_add(toks, pos)

    def _parse_add(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        left, pos = self._parse_mul(toks, pos)
        while pos < len(toks) and toks[pos].kind in (TokenKind.PLUS, TokenKind.MINUS):
            op: Literal["+", "-", "*", "/"] = "+" if toks[pos].kind == TokenKind.PLUS else "-"
            pos += 1
            right, pos = self._parse_mul(toks, pos)
            left = MathBin(op, left, right)
        return left, pos

    def _parse_mul(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        left, pos = self._parse_unary(toks, pos)
        while pos < len(toks) and toks[pos].kind in (TokenKind.STAR, TokenKind.SLASH):
            op: Literal["+", "-", "*", "/"] = "*" if toks[pos].kind == TokenKind.STAR else "/"
            pos += 1
            right, pos = self._parse_unary(toks, pos)
            left = MathBin(op, left, right)
        return left, pos

    def _parse_unary(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        if pos < len(toks) and toks[pos].kind == TokenKind.MINUS:
            pos += 1
            inner, pos = self._parse_unary(toks, pos)
            return MathNeg(inner), pos
        return self._parse_primary_math(toks, pos)

    def _parse_primary_math(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        if pos >= len(toks):
            raise self._err("expresión matemática incompleta")
        t = toks[pos]
        if t.kind == TokenKind.LPAREN:
            pos += 1
            expr, pos = self._parse_add(toks, pos)
            if pos >= len(toks) or toks[pos].kind != TokenKind.RPAREN:
                raise self._err("falta ) en expresión")
            pos += 1
            return expr, pos
        if t.kind == TokenKind.NUMBER and t.number_value is not None:
            return NumberLit(t.number_value), pos + 1
        if t.kind == TokenKind.IDENT:
            return VarRef(t.text), pos + 1
        raise self._err("token inválido en expresión matemática")


def parse_source(source: str) -> Program:
    lines = source.splitlines()
    p = _Parser(lines, 0)
    return p.parse_program()
