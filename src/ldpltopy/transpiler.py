"""Generación de código Python 3.13 a partir del AST."""

from __future__ import annotations

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
    VarRef,
    WhileStmt,
)

_PYTHON_KW: frozenset[str] = frozenset(
    {
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    }
)


def _py_name(ldpl_name: str) -> str:
    if ldpl_name in _PYTHON_KW:
        return f"{ldpl_name}_"
    return ldpl_name


def _num_literal(v: float) -> str:
    if v.is_integer():
        return str(int(v))
    return repr(v)


def _emit_expr(expr: Expr) -> str:
    if isinstance(expr, NumberLit):
        return _num_literal(expr.value)
    if isinstance(expr, StringLit):
        return repr(expr.value)
    if isinstance(expr, VarRef):
        return _py_name(expr.name)
    raise TypeError(expr)


def _is_number_expr(expr: Expr, types: dict[str, bool]) -> bool:
    if isinstance(expr, NumberLit):
        return True
    if isinstance(expr, StringLit):
        return False
    if isinstance(expr, VarRef):
        return types[expr.name]
    raise TypeError(expr)


def _emit_cmp(left: Expr, op: CmpOp, right: Expr, types: dict[str, bool]) -> str:
    ln = _is_number_expr(left, types)
    rn = _is_number_expr(right, types)
    lcode = _emit_expr(left)
    rcode = _emit_expr(right)
    if ln and rn:
        lfinal = f"float({lcode})"
        rfinal = f"float({rcode})"
    elif not ln and not rn:
        lfinal = f"str({lcode})"
        rfinal = f"str({rcode})"
    else:
        lfinal = f"str({lcode})"
        rfinal = f"str({rcode})"
    pyop = {
        CmpOp.EQ: "==",
        CmpOp.NE: "!=",
        CmpOp.GT: ">",
        CmpOp.LT: "<",
        CmpOp.GE: ">=",
        CmpOp.LE: "<=",
    }[op]
    return f"({lfinal} {pyop} {rfinal})"


def _emit_math(expr: MathExpr, types: dict[str, bool]) -> str:
    if isinstance(expr, NumberLit):
        return _num_literal(expr.value)
    if isinstance(expr, VarRef):
        return f"float({_py_name(expr.name)})"
    if isinstance(expr, MathNeg):
        return f"(-({_emit_math(expr.inner, types)}))"
    if isinstance(expr, MathBin):
        left = _emit_math(expr.left, types)
        right = _emit_math(expr.right, types)
        return f"({left} {expr.op} {right})"
    raise TypeError(expr)


def _emit_text_chunk(part: DisplayPart, types: dict[str, bool]) -> str:
    if part == "lf" or part == "crlf":
        return r"'\n'"
    if isinstance(part, StringLit):
        return repr(part.value)
    if isinstance(part, NumberLit):
        return f"_ldpl_number_text(float({_num_literal(part.value)}))"
    if isinstance(part, VarRef):
        if types[part.name]:
            return f"_ldpl_number_text({_py_name(part.name)})"
        return f"str({_py_name(part.name)})"
    raise TypeError(part)


def _emit_display_parts(parts: tuple[DisplayPart, ...], types: dict[str, bool]) -> str:
    chunks = [_emit_text_chunk(p, types) for p in parts]
    return f"print(''.join([{', '.join(chunks)}]), end=\"\")"


def _emit_join_chunks(parts: tuple[DisplayPart, ...], types: dict[str, bool]) -> list[str]:
    return [_emit_text_chunk(p, types) for p in parts]


def _emit_store_lines(stmt: StoreStmt, types: dict[str, bool]) -> list[str]:
    target = _py_name(stmt.target)
    is_num_target = types[stmt.target]
    val = stmt.value
    if is_num_target:
        if isinstance(val, NumberLit):
            return [f"{target} = float({_num_literal(val.value)})"]
        if isinstance(val, StringLit):
            return [f"{target} = _ldpl_text_to_number({repr(val.value)})"]
        if isinstance(val, VarRef):
            if types[val.name]:
                return [f"{target} = float({_py_name(val.name)})"]
            return [f"{target} = _ldpl_text_to_number(str({_py_name(val.name)}))"]
    else:
        if isinstance(val, NumberLit):
            return [f"{target} = str({_num_literal(val.value)})"]
        if isinstance(val, StringLit):
            return [f"{target} = {repr(val.value)}"]
        if isinstance(val, VarRef):
            return [f"{target} = str({_py_name(val.name)})"]
    raise TypeError(val)


def _ldpl_helpers() -> str:
    return (
        "def _ldpl_text_to_number(t: str) -> float:\n"
        "    s = t.strip()\n"
        "    if not s:\n"
        "        return 0.0\n"
        "    try:\n"
        "        return float(s)\n"
        "    except ValueError:\n"
        "        return 0.0\n"
        "\n"
        "def _ldpl_number_text(v: float) -> str:\n"
        "    if v == int(v):\n"
        "        return str(int(v))\n"
        "    return str(v)\n"
        "\n"
    )


def _emit_accept_lines(stmt: AcceptStmt, types: dict[str, bool], indent: str) -> list[str]:
    target = _py_name(stmt.target)
    if types[stmt.target]:
        return [
            f"{indent}while True:",
            f"{indent}    _raw = input()",
            f"{indent}    try:",
            f"{indent}        {target} = float(_raw)",
            f"{indent}        break",
            f"{indent}    except ValueError:",
            f'{indent}        print("Redo from start")',
        ]
    return [f"{indent}{target} = input()"]


def _emit_stmt(stmt: Statement, types: dict[str, bool], indent: str) -> list[str]:
    if isinstance(stmt, StoreStmt):
        return [f"{indent}{line}" for line in _emit_store_lines(stmt, types)]
    if isinstance(stmt, DisplayStmt):
        return [f"{indent}{_emit_display_parts(stmt.parts, types)}"]
    if isinstance(stmt, JoinStmt):
        parts = _emit_join_chunks(stmt.parts, types)
        target = _py_name(stmt.target)
        return [f"{indent}{target} = ''.join([{', '.join(parts)}])"]
    if isinstance(stmt, SolveStmt):
        target = _py_name(stmt.target)
        return [f"{indent}{target} = {_emit_math(stmt.expr, types)}"]
    if isinstance(stmt, AcceptStmt):
        return _emit_accept_lines(stmt, types, indent)
    if isinstance(stmt, IfStmt):
        cond = _emit_cmp(stmt.condition_left, stmt.op, stmt.condition_right, types)
        lines: list[str] = [f"{indent}if {cond}:"]
        if stmt.then_body:
            for s in stmt.then_body:
                lines.extend(_emit_stmt(s, types, indent + "    "))
        else:
            lines.append(f"{indent}    pass")
        if stmt.else_body is not None:
            lines.append(f"{indent}else:")
            if stmt.else_body:
                for s in stmt.else_body:
                    lines.extend(_emit_stmt(s, types, indent + "    "))
            else:
                lines.append(f"{indent}    pass")
        return lines
    if isinstance(stmt, WhileStmt):
        cond = _emit_cmp(stmt.condition_left, stmt.op, stmt.condition_right, types)
        wlines = [f"{indent}while {cond}:"]
        if stmt.body:
            for s in stmt.body:
                wlines.extend(_emit_stmt(s, types, indent + "    "))
        else:
            wlines.append(f"{indent}    pass")
        return wlines
    raise TypeError(stmt)


def transpile(program: Program) -> str:
    types: dict[str, bool] = {d.name: d.is_number for d in program.declarations}
    lines: list[str] = [
        '"""Generado por ldpltopy — subset LDPL."""',
        "",
        "from __future__ import annotations",
        "",
        _ldpl_helpers(),
        "def main() -> None:",
    ]
    for d in program.declarations:
        name = _py_name(d.name)
        if d.is_number:
            lines.append(f"    {name}: float = 0.0")
        else:
            lines.append(f'    {name}: str = ""')
    for stmt in program.statements:
        lines.extend(_emit_stmt(stmt, types, "    "))
    lines.extend(["", "", 'if __name__ == "__main__":', "    main()", ""])
    return "\n".join(lines)
