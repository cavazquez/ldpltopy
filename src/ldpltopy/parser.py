"""Parser recursivo para el subset LDPL soportado."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from ldpltopy.ast import (
    AcceptStmt,
    AddStmt,
    AppendFileStmt,
    BoolAnd,
    BoolExpr,
    BoolNot,
    BoolOr,
    BreakStmt,
    CallStmt,
    CeilStmt,
    CmpOp,
    CmpPredicate,
    ContinueStmt,
    DecrementStmt,
    DisplayPart,
    DisplayStmt,
    DivideStmt,
    Expr,
    FloorStmt,
    ForEachStmt,
    ForStmt,
    GetLengthStmt,
    GetRandomStmt,
    IfStmt,
    IncrementStmt,
    IndexRef,
    JoinStmt,
    LoadFileStmt,
    MathBin,
    MathExpr,
    MathNeg,
    ModuloStmt,
    MultiplyStmt,
    NumberLit,
    Program,
    PushStmt,
    ReplaceStmt,
    ReturnStmt,
    SolveStmt,
    Statement,
    StoreStmt,
    StringLit,
    SubDef,
    SubtractStmt,
    TrimStmt,
    VarDecl,
    VarKind,
    VarRef,
    WhileStmt,
    WriteFileStmt,
)
from ldpltopy.lexer import Token, TokenKind, is_blank_or_comment, lex_line, line_starts_section
from ldpltopy.preprocess import expand_includes


class ParseError(Exception):
    __slots__ = ("message", "line_no")

    def __init__(self, message: str, line_no: int) -> None:
        super().__init__(message)
        self.message = message
        self.line_no = line_no

    def __str__(self) -> str:  # pragma: no cover - mensaje legible
        return f"Línea {self.line_no}: {self.message}"


def _strip_ldpl_comment(raw: str) -> str:
    s = raw.strip()
    if "#" in s:
        s = s[: s.index("#")].strip()
    return s


@dataclass(slots=True)
class _Parser:
    lines: list[str]
    i: int
    loop_depth: int = 0
    sub_depth: int = 0

    def _err(self, msg: str) -> ParseError:
        line_no = self.i + 1 if self.i < len(self.lines) else len(self.lines)
        return ParseError(msg, line_no)

    def _skip_blanks(self) -> None:
        while self.i < len(self.lines) and is_blank_or_comment(self.lines[self.i]):
            self.i += 1

    def _tokens_here(self) -> list[Token]:
        return lex_line(self.lines[self.i])

    def _line_is_solve(self, toks: list[Token]) -> bool:
        if len(toks) < 4 or toks[0].text != "in":
            return False
        if toks[2].text == "solve":
            return True
        return len(toks) >= 6 and toks[2].kind == TokenKind.COLON and toks[4].text == "solve"

    def _expect_ident(self, tok: Token, ctx: str) -> str:
        if tok.kind != TokenKind.IDENT:
            raise self._err(f"se esperaba identificador ({ctx})")
        return tok.text

    def _header_is_parameters(self, raw: str) -> bool:
        s = _strip_ldpl_comment(raw).lower().rstrip(":")
        return s in {"parameters", "-- parameters --"}

    def _header_is_local_data(self, raw: str) -> bool:
        s = _strip_ldpl_comment(raw).lower().rstrip(":")
        return s in {"local data", "-- local data --"}

    def _header_is_procedure_sub(self, raw: str) -> bool:
        s = _strip_ldpl_comment(raw).lower().rstrip(":")
        return s in {"procedure", "-- procedure --"}

    def _is_decl_line(self, toks: list[Token]) -> bool:
        return len(toks) >= 3 and toks[1].text == "is"

    def _is_end_sub_line(self, toks: list[Token]) -> bool:
        return len(toks) == 2 and toks[0].text == "end" and toks[1].text == "sub"

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
        stmts, subs = self._parse_procedure_content()
        return Program(tuple(decls), tuple(stmts), tuple(subs))

    def _parse_procedure_content(self) -> tuple[list[Statement], list[SubDef]]:
        stmts: list[Statement] = []
        subs: list[SubDef] = []
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                break
            toks = self._tokens_here()
            if not toks:
                self.i += 1
                continue
            if toks[0].text == "sub":
                subs.append(self._parse_sub())
                continue
            stmt = self._parse_statement()
            if stmt is None:
                continue
            stmts.append(stmt)
        return stmts, subs

    def _parse_decl(self) -> VarDecl:
        toks = self._tokens_here()
        if len(toks) < 3:
            raise self._err("declaración inválida en data:")
        name = self._expect_ident(toks[0], "variable")
        if toks[1].text != "is":
            raise self._err("se esperaba 'is' en declaración")
        words = [t.text for t in toks[2:]]
        kind: VarKind
        if len(words) >= 2 and words[-1] == "list":
            base = words[:-1]
            if base in (["number"], ["numbers"]):
                kind = VarKind.NUMBER_LIST
            elif base in (["text"], ["texts"]):
                kind = VarKind.TEXT_LIST
            else:
                raise self._err("solo se soportan 'number list' y 'text list' en data:")
            if len(words) != 2:
                raise self._err("demasiados tokens en declaración de lista")
        elif len(words) >= 2 and words[-1] == "map":
            base = words[:-1]
            if base in (["number"], ["numbers"]):
                kind = VarKind.NUMBER_MAP
            elif base in (["text"], ["texts"]):
                kind = VarKind.TEXT_MAP
            else:
                raise self._err("solo se soportan 'number map' y 'text map' en data:")
            if len(words) != 2:
                raise self._err("demasiados tokens en declaración de mapa")
        elif words in (["number"], ["numbers"]):
            kind = VarKind.NUMBER
        elif words in (["text"], ["texts"]):
            kind = VarKind.TEXT
        else:
            raise self._err("tipo no soportado en data:")
        if len(toks) != 2 + len(words):
            raise self._err("demasiados tokens en declaración de variable")
        self.i += 1
        return VarDecl(name, kind)

    def _parse_sub(self) -> SubDef:
        toks = self._tokens_here()
        if not toks or toks[0].text != "sub" or len(toks) < 2:
            raise self._err("sub mal formada")
        name = self._expect_ident(toks[1], "nombre de sub")
        if len(toks) != 2:
            raise self._err("tokens extra en línea sub")
        self.i += 1
        self.sub_depth += 1
        try:
            params, locals_, body = self._parse_sub_body()
        finally:
            self.sub_depth -= 1
        return SubDef(name, tuple(params), tuple(locals_), tuple(body))

    def _parse_sub_body(
        self,
    ) -> tuple[list[VarDecl], list[VarDecl], list[Statement]]:
        params: list[VarDecl] = []
        locals_: list[VarDecl] = []
        body: list[Statement] = []
        mode = "outer"
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                raise self._err("fin de archivo dentro de sub (falta end sub)")
            raw = self.lines[self.i]
            toks = self._tokens_here()
            if not toks:
                self.i += 1
                continue
            if self._is_end_sub_line(toks):
                self.i += 1
                return params, locals_, body
            if mode == "outer":
                if self._header_is_parameters(raw):
                    mode = "params"
                    self.i += 1
                    continue
                if self._header_is_local_data(raw):
                    mode = "locals"
                    self.i += 1
                    continue
                if self._header_is_procedure_sub(raw):
                    mode = "body"
                    self.i += 1
                    continue
                mode = "body"
            if mode == "params":
                if self._header_is_local_data(raw):
                    mode = "locals"
                    self.i += 1
                    continue
                if self._header_is_procedure_sub(raw):
                    mode = "body"
                    self.i += 1
                    continue
                if self._is_decl_line(toks):
                    params.append(self._parse_decl())
                    continue
                mode = "body"
            if mode == "locals":
                if self._header_is_procedure_sub(raw):
                    mode = "body"
                    self.i += 1
                    continue
                if self._is_decl_line(toks):
                    locals_.append(self._parse_decl())
                    continue
                mode = "body"
            st = self._parse_statement()
            if st is None:
                raise self._err("sentencia esperada en sub")
            body.append(st)

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
        if head == "for":
            if len(toks) >= 2 and toks[1].text == "each":
                return self._parse_for_each()
            return self._parse_for()
        if head == "break":
            if len(toks) != 1:
                raise self._err("sintaxis: break")
            if self.loop_depth == 0:
                raise self._err("break fuera de un bucle")
            self.i += 1
            return BreakStmt()
        if head == "continue":
            if len(toks) != 1:
                raise self._err("sintaxis: continue")
            if self.loop_depth == 0:
                raise self._err("continue fuera de un bucle")
            self.i += 1
            return ContinueStmt()
        if head == "return":
            if len(toks) != 1:
                raise self._err("sintaxis: return")
            if self.sub_depth == 0:
                raise self._err("return fuera de una sub")
            self.i += 1
            return ReturnStmt()
        if head == "call":
            self.i += 1
            return self._parse_call(toks)
        if head == "store":
            self.i += 1
            return self._parse_store(toks)
        if head == "push":
            self.i += 1
            return self._parse_push(toks)
        if head == "display":
            self.i += 1
            return self._parse_display(toks)
        if head == "print":
            self.i += 1
            return self._parse_print(toks)
        if head == "accept":
            self.i += 1
            return self._parse_accept(toks)
        if head == "in" and len(toks) >= 3 and toks[2].text == "join":
            self.i += 1
            return self._parse_join(toks)
        if head == "in" and self._line_is_solve(toks):
            self.i += 1
            return self._parse_solve(toks)
        if head == "add":
            self.i += 1
            return self._parse_add_stmt(toks)
        if head == "subtract":
            self.i += 1
            return self._parse_subtract(toks)
        if head == "multiply":
            self.i += 1
            return self._parse_multiply(toks)
        if head == "divide":
            self.i += 1
            return self._parse_divide(toks)
        if head == "modulo":
            self.i += 1
            return self._parse_modulo(toks)
        if head == "floor":
            self.i += 1
            return self._parse_floor(toks)
        if head == "ceil":
            self.i += 1
            return self._parse_ceil(toks)
        if head == "increment":
            self.i += 1
            return self._parse_increment(toks)
        if head == "decrement":
            self.i += 1
            return self._parse_decrement(toks)
        if head == "get":
            if len(toks) >= 2 and toks[1].text == "length":
                self.i += 1
                return self._parse_get_length(toks)
            if len(toks) >= 2 and toks[1].text == "random":
                self.i += 1
                return self._parse_get_random(toks)
        if head == "trim":
            self.i += 1
            return self._parse_trim(toks)
        if head == "replace":
            self.i += 1
            return self._parse_replace(toks)
        if head == "load":
            self.i += 1
            return self._parse_load_file(toks)
        if head == "write":
            self.i += 1
            return self._parse_write_file(toks)
        if head == "append":
            self.i += 1
            return self._parse_append_file(toks)
        raise self._err(f"sentencia no soportada: {head}")

    def _parse_call(self, toks: list[Token]) -> CallStmt:
        if len(toks) < 2:
            raise self._err("sintaxis: call <nombre> [with <args...>]")
        name = self._expect_ident(toks[1], "sub a llamar")
        if len(toks) == 2:
            return CallStmt(name, ())
        if toks[2].text != "with":
            raise self._err("se esperaba with después del nombre en call")
        args = tuple(self._parse_atomic_expr(t) for t in toks[3:])
        return CallStmt(name, args)

    def _parse_add_stmt(self, toks: list[Token]) -> AddStmt:
        if len(toks) != 6 or toks[2].text != "and" or toks[4].text != "in":
            raise self._err("sintaxis: add <a> and <b> in <destino>")
        return AddStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino add"),
        )

    def _parse_subtract(self, toks: list[Token]) -> SubtractStmt:
        if len(toks) != 6 or toks[2].text != "from" or toks[4].text != "in":
            raise self._err("sintaxis: subtract <a> from <b> in <destino>")
        return SubtractStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino subtract"),
        )

    def _parse_multiply(self, toks: list[Token]) -> MultiplyStmt:
        if len(toks) != 6 or toks[2].text != "by" or toks[4].text != "in":
            raise self._err("sintaxis: multiply <a> by <b> in <destino>")
        return MultiplyStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino multiply"),
        )

    def _parse_divide(self, toks: list[Token]) -> DivideStmt:
        if len(toks) != 6 or toks[2].text != "by" or toks[4].text != "in":
            raise self._err("sintaxis: divide <a> by <b> in <destino>")
        return DivideStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino divide"),
        )

    def _parse_modulo(self, toks: list[Token]) -> ModuloStmt:
        if len(toks) != 6 or toks[2].text != "by" or toks[4].text != "in":
            raise self._err("sintaxis: modulo <a> by <b> in <destino>")
        return ModuloStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino modulo"),
        )

    def _parse_floor(self, toks: list[Token]) -> FloorStmt:
        if len(toks) != 4 or toks[2].text != "in":
            raise self._err("sintaxis: floor <x> in <destino>")
        return FloorStmt(
            self._parse_atomic_expr(toks[1]),
            self._expect_ident(toks[3], "destino floor"),
        )

    def _parse_ceil(self, toks: list[Token]) -> CeilStmt:
        if len(toks) != 4 or toks[2].text != "in":
            raise self._err("sintaxis: ceil <x> in <destino>")
        return CeilStmt(
            self._parse_atomic_expr(toks[1]),
            self._expect_ident(toks[3], "destino ceil"),
        )

    def _parse_increment(self, toks: list[Token]) -> IncrementStmt:
        if len(toks) != 2:
            raise self._err("sintaxis: increment <variable>")
        return IncrementStmt(self._expect_ident(toks[1], "increment"))

    def _parse_decrement(self, toks: list[Token]) -> DecrementStmt:
        if len(toks) != 2:
            raise self._err("sintaxis: decrement <variable>")
        return DecrementStmt(self._expect_ident(toks[1], "decrement"))

    def _parse_get_length(self, toks: list[Token]) -> GetLengthStmt:
        if len(toks) != 6 or toks[2].text != "of" or toks[4].text != "in":
            raise self._err("sintaxis: get length of <texto> in <destino>")
        return GetLengthStmt(
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino length"),
        )

    def _parse_get_random(self, toks: list[Token]) -> GetRandomStmt:
        if len(toks) != 4 or toks[2].text != "in":
            raise self._err("sintaxis: get random in <destino>")
        return GetRandomStmt(self._expect_ident(toks[3], "destino random"))

    def _parse_trim(self, toks: list[Token]) -> TrimStmt:
        if len(toks) != 4 or toks[2].text != "in":
            raise self._err("sintaxis: trim <texto> in <destino>")
        return TrimStmt(
            self._parse_atomic_expr(toks[1]),
            self._expect_ident(toks[3], "destino trim"),
        )

    def _parse_replace(self, toks: list[Token]) -> ReplaceStmt:
        if len(toks) != 6 or toks[2].text != "with" or toks[4].text != "in":
            raise self._err("sintaxis: replace <old> with <new> in <var>")
        return ReplaceStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[3]),
            self._expect_ident(toks[5], "destino replace"),
        )

    def _parse_load_file(self, toks: list[Token]) -> LoadFileStmt:
        if len(toks) != 5 or toks[1].text != "file" or toks[3].text != "in":
            raise self._err("sintaxis: load file <ruta> in <var>")
        return LoadFileStmt(
            self._parse_atomic_expr(toks[2]),
            self._expect_ident(toks[4], "destino load file"),
        )

    def _parse_write_file(self, toks: list[Token]) -> WriteFileStmt:
        if len(toks) != 5 or toks[2].text != "to" or toks[3].text != "file":
            raise self._err("sintaxis: write <valor> to file <ruta>")
        return WriteFileStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[4]),
        )

    def _parse_append_file(self, toks: list[Token]) -> AppendFileStmt:
        if len(toks) != 5 or toks[2].text != "to" or toks[3].text != "file":
            raise self._err("sintaxis: append <valor> to file <ruta>")
        return AppendFileStmt(
            self._parse_atomic_expr(toks[1]),
            self._parse_atomic_expr(toks[4]),
        )

    def _parse_store(self, toks: list[Token]) -> StoreStmt:
        if len(toks) < 4 or "in" not in {t.text for t in toks}:
            raise self._err("sintaxis: store <valor> in <variable>[: clave]")
        in_positions = [i for i, t in enumerate(toks) if t.text == "in"]
        in_i = in_positions[-1]
        if in_i < 1:
            raise self._err("store mal formado")
        val_toks = toks[1:in_i]
        if len(val_toks) != 1:
            raise self._err("store admite un único valor en este subset")
        value = self._parse_atomic_expr(val_toks[0])
        rest = toks[in_i + 1 :]
        if len(rest) >= 3 and rest[1].kind == TokenKind.COLON:
            target = self._expect_ident(rest[0], "destino de store")
            key = self._parse_atomic_expr(rest[2])
            if len(rest) != 3:
                raise self._err("tokens extra tras clave en store")
            return StoreStmt(value, target, key)
        if len(rest) != 1:
            raise self._err("destino de store inválido")
        target = self._expect_ident(rest[0], "destino de store")
        return StoreStmt(value, target, None)

    def _parse_push(self, toks: list[Token]) -> PushStmt:
        if len(toks) < 4 or toks[-2].text != "to":
            raise self._err("sintaxis: push <valor> to <lista>")
        target = self._expect_ident(toks[-1], "destino de push")
        val_toks = toks[1:-2]
        if len(val_toks) != 1:
            raise self._err("push admite un único valor en este subset")
        value = self._parse_atomic_expr(val_toks[0])
        return PushStmt(value, target)

    def _parse_display(self, toks: list[Token]) -> DisplayStmt:
        parts = self._parse_display_parts(toks[1:])
        return DisplayStmt(parts)

    def _parse_print(self, toks: list[Token]) -> DisplayStmt:
        inner = self._parse_display_parts(toks[1:])
        return DisplayStmt(tuple([*inner, "crlf"]))

    def _parse_display_parts(self, toks: list[Token]) -> tuple[DisplayPart, ...]:
        out: list[DisplayPart] = []
        i = 0
        while i < len(toks):
            t = toks[i]
            if t.kind == TokenKind.IDENT and t.text in {"lf", "crlf"}:
                br: Literal["lf", "crlf"] = cast(Literal["lf", "crlf"], t.text)
                out.append(br)
                i += 1
                continue
            if (
                i + 2 < len(toks)
                and toks[i].kind == TokenKind.IDENT
                and toks[i + 1].kind == TokenKind.COLON
            ):
                base = self._expect_ident(toks[i], "base índice")
                key = self._parse_atomic_expr(toks[i + 2])
                out.append(IndexRef(base, key))
                i += 3
                continue
            out.append(self._parse_atomic_expr(t))
            i += 1
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
            raise self._err("sintaxis: in <var> [ : <clave> ] solve <expr>")
        target = self._expect_ident(toks[1], "destino de solve")
        key: Expr | None
        start_math: int
        if toks[2].text == "solve":
            key = None
            start_math = 3
        elif len(toks) >= 6 and toks[2].kind == TokenKind.COLON:
            key = self._parse_atomic_expr(toks[3])
            if toks[4].text != "solve":
                raise self._err("se esperaba solve tras índice")
            start_math = 5
        else:
            raise self._err("sintaxis: in <var> solve <expr>")
        math_toks = toks[start_math:]
        if not math_toks:
            raise self._err("expresión matemática vacía")
        expr, pos = self._parse_math_expr(math_toks, 0)
        if pos != len(math_toks):
            raise self._err("tokens sobrantes en expresión matemática")
        return SolveStmt(target, expr, key)

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
        cond, pos = self._parse_bool_expr(cond_toks, 0)
        if pos != len(cond_toks):
            raise self._err("condición if con tokens extra")
        self.i += 1
        branches: list[tuple[BoolExpr, list[Statement]]] = []
        first_body = self._parse_if_block_body()
        branches.append((cond, first_body))

        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                raise self._err("fin de archivo dentro de if (falta end if)")
            line_toks = self._tokens_here()
            if not line_toks:
                self.i += 1
                continue
            if line_toks[0].text == "end" and len(line_toks) == 2 and line_toks[1].text == "if":
                self.i += 1
                return IfStmt(tuple((c, tuple(s)) for c, s in branches), None)
            if line_toks[0].text == "else" and len(line_toks) >= 2 and line_toks[1].text == "if":
                if line_toks[-1].text != "then":
                    raise self._err("se esperaba then al final de la línea else if")
                ei_toks = line_toks[2:-1]
                c2, pos2 = self._parse_bool_expr(ei_toks, 0)
                if pos2 != len(ei_toks):
                    raise self._err("condición else if con tokens extra")
                self.i += 1
                body_ei = self._parse_if_block_body()
                branches.append((c2, body_ei))
                continue
            if line_toks[0].text == "else" and len(line_toks) == 1:
                self.i += 1
                else_stmts = self._parse_block_until_end_if()
                self._consume_end_if()
                return IfStmt(tuple((c, tuple(s)) for c, s in branches), tuple(else_stmts))
            raise self._err("se esperaba else, else if o end if")

    def _parse_if_block_body(self) -> list[Statement]:
        out: list[Statement] = []
        while True:
            self._skip_blanks()
            if self.i >= len(self.lines):
                raise self._err("fin de archivo dentro de if (falta end if)")
            toks = self._tokens_here()
            if not toks:
                self.i += 1
                continue
            if toks[0].text == "end" and len(toks) == 2 and toks[1].text == "if":
                return out
            if toks[0].text == "else":
                if len(toks) >= 2 and toks[1].text == "if":
                    return out
                if len(toks) == 1:
                    return out
                raise self._err("else mal formado")
            nxt = self._parse_statement()
            if nxt is None:
                raise self._err("sentencia esperada")
            out.append(nxt)

    def _parse_while(self) -> WhileStmt:
        toks = self._tokens_here()
        if not toks or toks[0].text != "while":
            raise self._err("while mal formado")
        if toks[-1].text != "do":
            raise self._err("se esperaba do al final de la línea while")
        cond_toks = toks[1:-1]
        cond, pos = self._parse_bool_expr(cond_toks, 0)
        if pos != len(cond_toks):
            raise self._err("condición while con tokens extra")
        self.i += 1
        self.loop_depth += 1
        try:
            body = self._parse_block_until_repeat()
        finally:
            self.loop_depth -= 1
        return WhileStmt(cond, tuple(body))

    def _parse_for(self) -> ForStmt:
        toks = self._tokens_here()
        if not toks or toks[0].text != "for":
            raise self._err("for mal formado")
        if len(toks) < 7:
            raise self._err("sintaxis: for <var> from <expr> to <expr> [step <expr>] do")
        counter = self._expect_ident(toks[1], "contador for")
        if toks[2].text != "from":
            raise self._err("se esperaba from en for")
        if toks[4].text != "to":
            raise self._err("se esperaba to en for")
        start = self._parse_atomic_expr(toks[3])
        end = self._parse_atomic_expr(toks[5])
        pos = 6
        step: Expr
        if pos < len(toks) and toks[pos].text == "step":
            if pos + 1 >= len(toks):
                raise self._err("falta expresión en step")
            step = self._parse_atomic_expr(toks[pos + 1])
            pos += 2
        else:
            step = NumberLit(1.0)
        if pos >= len(toks) or toks[pos].text != "do":
            raise self._err("se esperaba do al final del for")
        if pos != len(toks) - 1:
            raise self._err("tokens extra en línea for")
        self.i += 1
        self.loop_depth += 1
        try:
            body = self._parse_block_until_repeat()
        finally:
            self.loop_depth -= 1
        return ForStmt(counter, start, end, step, tuple(body))

    def _parse_for_each(self) -> ForEachStmt:
        toks = self._tokens_here()
        if len(toks) != 6:
            raise self._err("sintaxis: for each <var> in <lista> do")
        if toks[0].text != "for" or toks[1].text != "each":
            raise self._err("for each mal formado")
        item_var = self._expect_ident(toks[2], "variable de iteración")
        if toks[3].text != "in":
            raise self._err("se esperaba in en for each")
        container = self._expect_ident(toks[4], "lista en for each")
        if toks[5].text != "do":
            raise self._err("se esperaba do en for each")
        self.i += 1
        self.loop_depth += 1
        try:
            body = self._parse_block_until_repeat()
        finally:
            self.loop_depth -= 1
        return ForEachStmt(item_var, container, tuple(body))

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
                raise self._err("fin de archivo dentro de bucle (falta repeat)")
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

    def _parse_bool_expr(self, toks: list[Token], pos: int) -> tuple[BoolExpr, int]:
        return self._parse_bool_or(toks, pos)

    def _parse_bool_or(self, toks: list[Token], pos: int) -> tuple[BoolExpr, int]:
        left, pos = self._parse_bool_and(toks, pos)
        while pos < len(toks) and toks[pos].kind == TokenKind.IDENT and toks[pos].text == "or":
            pos += 1
            right, pos = self._parse_bool_and(toks, pos)
            left = BoolOr(left, right)
        return left, pos

    def _parse_bool_and(self, toks: list[Token], pos: int) -> tuple[BoolExpr, int]:
        left, pos = self._parse_bool_unary(toks, pos)
        while pos < len(toks) and toks[pos].kind == TokenKind.IDENT and toks[pos].text == "and":
            pos += 1
            right, pos = self._parse_bool_unary(toks, pos)
            left = BoolAnd(left, right)
        return left, pos

    def _parse_bool_unary(self, toks: list[Token], pos: int) -> tuple[BoolExpr, int]:
        if pos < len(toks) and toks[pos].kind == TokenKind.IDENT and toks[pos].text == "not":
            pos += 1
            inner, pos = self._parse_bool_unary(toks, pos)
            return BoolNot(inner), pos
        return self._parse_bool_primary(toks, pos)

    def _parse_bool_primary(self, toks: list[Token], pos: int) -> tuple[BoolExpr, int]:
        if pos < len(toks) and toks[pos].kind == TokenKind.LPAREN:
            pos += 1
            inner, pos = self._parse_bool_or(toks, pos)
            if pos >= len(toks) or toks[pos].kind != TokenKind.RPAREN:
                raise self._err("falta ) en condición")
            pos += 1
            return inner, pos
        pred, pos = self._parse_predicate(toks, pos)
        return pred, pos

    def _parse_predicate(self, toks: list[Token], pos: int) -> tuple[CmpPredicate, int]:
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
        return CmpPredicate(left, op, right), pos

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
        return self._parse_math_add(toks, pos)

    def _parse_math_add(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        left, pos = self._parse_math_mul(toks, pos)
        while pos < len(toks) and toks[pos].kind in (TokenKind.PLUS, TokenKind.MINUS):
            op: Literal["+", "-", "*", "/"] = "+" if toks[pos].kind == TokenKind.PLUS else "-"
            pos += 1
            right, pos = self._parse_math_mul(toks, pos)
            left = MathBin(op, left, right)
        return left, pos

    def _parse_math_mul(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        left, pos = self._parse_math_unary(toks, pos)
        while pos < len(toks) and toks[pos].kind in (TokenKind.STAR, TokenKind.SLASH):
            op: Literal["+", "-", "*", "/"] = "*" if toks[pos].kind == TokenKind.STAR else "/"
            pos += 1
            right, pos = self._parse_math_unary(toks, pos)
            left = MathBin(op, left, right)
        return left, pos

    def _parse_math_unary(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        if pos < len(toks) and toks[pos].kind == TokenKind.MINUS:
            pos += 1
            inner, pos = self._parse_math_unary(toks, pos)
            return MathNeg(inner), pos
        return self._parse_primary_math(toks, pos)

    def _parse_primary_math(self, toks: list[Token], pos: int) -> tuple[MathExpr, int]:
        if pos >= len(toks):
            raise self._err("expresión matemática incompleta")
        t = toks[pos]
        if t.kind == TokenKind.LPAREN:
            pos += 1
            expr, pos = self._parse_math_add(toks, pos)
            if pos >= len(toks) or toks[pos].kind != TokenKind.RPAREN:
                raise self._err("falta ) en expresión")
            pos += 1
            return expr, pos
        if t.kind == TokenKind.NUMBER and t.number_value is not None:
            return NumberLit(t.number_value), pos + 1
        if t.kind == TokenKind.IDENT:
            return VarRef(t.text), pos + 1
        raise self._err("token inválido en expresión matemática")


def parse_source(source: str, *, file_path: Path | None = None) -> Program:
    bp = (file_path or Path.cwd()).resolve()
    expanded = expand_includes(source, bp)
    lines = expanded.splitlines()
    p = _Parser(lines, 0)
    return p.parse_program()
