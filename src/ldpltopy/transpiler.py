"""Generación de código Python 3.13 a partir del AST."""

from __future__ import annotations

import re

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


def _sanitize_sub_name(name: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    if s and s[0].isdigit():
        s = "_" + s
    return s or "_sub"


def _num_literal(v: float) -> str:
    if v.is_integer():
        return str(int(v))
    return repr(v)


def _emit_var(name: str, param_boxes: frozenset[str] | None) -> str:
    py = _py_name(name)
    if param_boxes is not None and name in param_boxes:
        return f"{py}_box[0]"
    return py


def _emit_expr(expr: Expr, param_boxes: frozenset[str] | None) -> str:
    if isinstance(expr, NumberLit):
        return _num_literal(expr.value)
    if isinstance(expr, StringLit):
        return repr(expr.value)
    if isinstance(expr, VarRef):
        return _emit_var(expr.name, param_boxes)
    raise TypeError(expr)


def _emit_numeric_operand(
    expr: Expr,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    if isinstance(expr, NumberLit):
        return f"float({_num_literal(expr.value)})"
    if isinstance(expr, StringLit):
        return f"_ldpl_text_to_number({repr(expr.value)})"
    if isinstance(expr, VarRef):
        k = types[expr.name]
        v = _emit_var(expr.name, param_boxes)
        if k == VarKind.NUMBER:
            return f"float({v})"
        if k == VarKind.TEXT:
            return f"_ldpl_text_to_number(str({v}))"
        raise TypeError(k)
    raise TypeError(expr)


def _emit_text_operand(
    expr: Expr,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    if isinstance(expr, StringLit):
        return repr(expr.value)
    if isinstance(expr, NumberLit):
        return f"_ldpl_number_text(float({_num_literal(expr.value)}))"
    if isinstance(expr, VarRef):
        k = types[expr.name]
        v = _emit_var(expr.name, param_boxes)
        if k == VarKind.TEXT:
            return f"str({v})"
        if k == VarKind.NUMBER:
            return f"_ldpl_number_text({v})"
        raise TypeError(k)
    raise TypeError(expr)


def _emit_map_key(expr: Expr, types: dict[str, VarKind], param_boxes: frozenset[str] | None) -> str:
    if isinstance(expr, NumberLit):
        return repr(_ldpl_key_str_from_float(expr.value))
    if isinstance(expr, StringLit):
        return repr(expr.value)
    if isinstance(expr, VarRef):
        k = types[expr.name]
        v = _emit_var(expr.name, param_boxes)
        if k == VarKind.NUMBER:
            return f"_ldpl_map_key_num(float({v}))"
        return f"str({v})"
    raise TypeError(expr)


def _ldpl_key_str_from_float(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return str(v)


def _is_number_expr(expr: Expr, types: dict[str, VarKind]) -> bool:
    if isinstance(expr, NumberLit):
        return True
    if isinstance(expr, StringLit):
        return False
    if isinstance(expr, VarRef):
        k = types[expr.name]
        if k in (VarKind.NUMBER_LIST, VarKind.TEXT_LIST, VarKind.NUMBER_MAP, VarKind.TEXT_MAP):
            msg = "no se pueden usar contenedores en comparaciones escalares"
            raise TypeError(msg)
        return k == VarKind.NUMBER
    raise TypeError(expr)


def _emit_cmp(
    left: Expr,
    op: CmpOp,
    right: Expr,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    ln = _is_number_expr(left, types)
    rn = _is_number_expr(right, types)
    lcode = _emit_expr(left, param_boxes)
    rcode = _emit_expr(right, param_boxes)
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


def _emit_bool(
    expr: BoolExpr,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    if isinstance(expr, CmpPredicate):
        return _emit_cmp(expr.left, expr.op, expr.right, types, param_boxes)
    if isinstance(expr, BoolNot):
        return f"(not ({_emit_bool(expr.inner, types, param_boxes)}))"
    if isinstance(expr, BoolAnd):
        return (
            f"(({_emit_bool(expr.left, types, param_boxes)}) and "
            f"({_emit_bool(expr.right, types, param_boxes)}))"
        )
    if isinstance(expr, BoolOr):
        return (
            f"(({_emit_bool(expr.left, types, param_boxes)}) or "
            f"({_emit_bool(expr.right, types, param_boxes)}))"
        )
    raise TypeError(expr)


def _emit_math(
    expr: MathExpr,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    if isinstance(expr, NumberLit):
        return _num_literal(expr.value)
    if isinstance(expr, VarRef):
        return f"float({_emit_var(expr.name, param_boxes)})"
    if isinstance(expr, MathNeg):
        return f"(-({_emit_math(expr.inner, types, param_boxes)}))"
    if isinstance(expr, MathBin):
        left = _emit_math(expr.left, types, param_boxes)
        right = _emit_math(expr.right, types, param_boxes)
        return f"({left} {expr.op} {right})"
    raise TypeError(expr)


def _emit_text_chunk(
    part: DisplayPart,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    if part == "lf" or part == "crlf":
        return r"'\n'"
    if isinstance(part, StringLit):
        return repr(part.value)
    if isinstance(part, NumberLit):
        return f"_ldpl_number_text(float({_num_literal(part.value)}))"
    if isinstance(part, VarRef):
        k = types[part.name]
        v = _emit_var(part.name, param_boxes)
        if k == VarKind.NUMBER:
            return f"_ldpl_number_text({v})"
        if k == VarKind.TEXT:
            return f"str({v})"
        raise TypeError(k)
    if isinstance(part, IndexRef):
        b = part.base
        bk = types[b]
        bv = _emit_var(b, param_boxes)
        if bk == VarKind.NUMBER_LIST:
            ix = f"int(float({_emit_expr(part.key, param_boxes)}))"
            return f"_ldpl_number_text({bv}[{ix}])"
        if bk == VarKind.TEXT_LIST:
            ix = f"int(float({_emit_expr(part.key, param_boxes)}))"
            return f"str({bv}[{ix}])"
        if bk == VarKind.NUMBER_MAP:
            mk = _emit_map_key(part.key, types, param_boxes)
            return f"_ldpl_number_text({bv}[{mk}])"
        if bk == VarKind.TEXT_MAP:
            mk = _emit_map_key(part.key, types, param_boxes)
            return f"str({bv}[{mk}])"
        raise TypeError(bk)
    raise TypeError(part)


def _emit_display_parts(
    parts: tuple[DisplayPart, ...],
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> str:
    chunks = [_emit_text_chunk(p, types, param_boxes) for p in parts]
    return f"print(''.join([{', '.join(chunks)}]), end=\"\")"


def _emit_join_chunks(
    parts: tuple[DisplayPart, ...],
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> list[str]:
    return [_emit_text_chunk(p, types, param_boxes) for p in parts]


def _emit_store_lines(
    stmt: StoreStmt,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> list[str]:
    tk = types[stmt.target]
    val = stmt.value
    tgt_py = _emit_var(stmt.target, param_boxes)

    if stmt.key is not None:
        key = stmt.key
        if tk == VarKind.NUMBER_LIST:
            ix = f"int(float({_emit_expr(key, param_boxes)}))"
            rhs = _emit_numeric_operand(val, types, param_boxes)
            return [f"{tgt_py}[{ix}] = {rhs}"]
        if tk == VarKind.TEXT_LIST:
            ix = f"int(float({_emit_expr(key, param_boxes)}))"
            rhs = _emit_text_operand(val, types, param_boxes)
            return [f"{tgt_py}[{ix}] = {rhs}"]
        if tk == VarKind.NUMBER_MAP:
            mk = _emit_map_key(key, types, param_boxes)
            rhs = _emit_numeric_operand(val, types, param_boxes)
            return [f"{tgt_py}[{mk}] = {rhs}"]
        if tk == VarKind.TEXT_MAP:
            mk = _emit_map_key(key, types, param_boxes)
            rhs = _emit_text_operand(val, types, param_boxes)
            return [f"{tgt_py}[{mk}] = {rhs}"]
        raise TypeError(tk)

    if tk in (VarKind.NUMBER_LIST, VarKind.TEXT_LIST, VarKind.NUMBER_MAP, VarKind.TEXT_MAP):
        msg = "store a contenedor requiere : clave o índice"
        raise TypeError(msg)
    is_num_target = tk == VarKind.NUMBER
    if is_num_target:
        if isinstance(val, NumberLit):
            return [f"{tgt_py} = float({_num_literal(val.value)})"]
        if isinstance(val, StringLit):
            return [f"{tgt_py} = _ldpl_text_to_number({repr(val.value)})"]
        if isinstance(val, VarRef):
            vk = types[val.name]
            vv = _emit_var(val.name, param_boxes)
            if vk == VarKind.NUMBER:
                return [f"{tgt_py} = float({vv})"]
            if vk == VarKind.TEXT:
                return [f"{tgt_py} = _ldpl_text_to_number(str({vv}))"]
            raise TypeError(vk)
    else:
        if isinstance(val, NumberLit):
            return [f"{tgt_py} = str({_num_literal(val.value)})"]
        if isinstance(val, StringLit):
            return [f"{tgt_py} = {repr(val.value)}"]
        if isinstance(val, VarRef):
            return [f"{tgt_py} = str({_emit_var(val.name, param_boxes)})"]
    raise TypeError(val)


def _emit_push_lines(
    stmt: PushStmt,
    types: dict[str, VarKind],
    param_boxes: frozenset[str] | None,
) -> list[str]:
    target = _emit_var(stmt.target, param_boxes)
    tk = types[stmt.target]
    val = stmt.value
    if tk == VarKind.NUMBER_LIST:
        if isinstance(val, NumberLit):
            return [f"{target}.append(float({_num_literal(val.value)}))"]
        if isinstance(val, StringLit):
            return [f"{target}.append(_ldpl_text_to_number({repr(val.value)}))"]
        if isinstance(val, VarRef):
            vk = types[val.name]
            vv = _emit_var(val.name, param_boxes)
            if vk == VarKind.NUMBER:
                return [f"{target}.append(float({vv}))"]
            if vk == VarKind.TEXT:
                return [f"{target}.append(_ldpl_text_to_number(str({vv})))"]
            raise TypeError(vk)
    if tk == VarKind.TEXT_LIST:
        if isinstance(val, NumberLit):
            return [f"{target}.append(str({_num_literal(val.value)}))"]
        if isinstance(val, StringLit):
            return [f"{target}.append({repr(val.value)})"]
        if isinstance(val, VarRef):
            vk = types[val.name]
            vv = _emit_var(val.name, param_boxes)
            if vk == VarKind.NUMBER:
                return [f"{target}.append(_ldpl_number_text({vv}))"]
            if vk == VarKind.TEXT:
                return [f"{target}.append(str({vv}))"]
            raise TypeError(vk)
    msg = "push solo a variables lista"
    raise TypeError(msg)


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
        "def _ldpl_map_key_num(v: float) -> str:\n"
        "    if v == int(v):\n"
        "        return str(int(v))\n"
        "    return str(v)\n"
        "\n"
    )


def _emit_accept_lines(
    stmt: AcceptStmt,
    types: dict[str, VarKind],
    indent: str,
    param_boxes: frozenset[str] | None,
) -> list[str]:
    target = _emit_var(stmt.target, param_boxes)
    if types[stmt.target] == VarKind.NUMBER:
        return [
            f"{indent}while True:",
            f"{indent}    _raw = input()",
            f"{indent}    try:",
            f"{indent}        {target} = float(_raw)",
            f"{indent}        break",
            f"{indent}    except ValueError:",
            f'{indent}        print("Redo from start")',
        ]
    if types[stmt.target] == VarKind.TEXT:
        return [f"{indent}{target} = input()"]
    msg = "accept solo para escalares number/text"
    raise TypeError(msg)


def _find_sub(program: Program, name: str) -> SubDef:
    for s in program.subs:
        if s.name == name:
            return s
    msg = f"sub no encontrada: {name}"
    raise TypeError(msg)


def _emit_call(
    stmt: CallStmt,
    program: Program,
    types: dict[str, VarKind],
    indent: str,
    temp_id: list[int],
    param_boxes: frozenset[str] | None,
) -> list[str]:
    sub = _find_sub(program, stmt.name)
    if len(stmt.args) != len(sub.parameters):
        msg = "número de argumentos en call no coincide con la sub"
        raise TypeError(msg)
    fn = f"ldpl_sub_{_sanitize_sub_name(stmt.name)}"
    lines: list[str] = []
    box_names: list[str] = []
    for arg in stmt.args:
        box = f"_ldpl_cb_{temp_id[0]}"
        temp_id[0] += 1
        box_names.append(box)
        if isinstance(arg, VarRef):
            src = _emit_var(arg.name, param_boxes)
            lines.append(f"{indent}{box} = [{src}]")
        elif isinstance(arg, NumberLit):
            lines.append(f"{indent}{box} = [float({_num_literal(arg.value)})]")
        elif isinstance(arg, StringLit):
            lines.append(f"{indent}{box} = [{repr(arg.value)}]")
        else:
            raise TypeError(arg)
    lines.append(f"{indent}{fn}({', '.join(box_names)})")
    for arg, box in zip(stmt.args, box_names, strict=True):
        if isinstance(arg, VarRef):
            dst = _emit_var(arg.name, param_boxes)
            lines.append(f"{indent}{dst} = {box}[0]")
    return lines


def _emit_io_prologue(track: bool, indent: str) -> list[str]:
    if not track:
        return []
    return [
        f"{indent}_ldpl_ec: float = 0.0",
        f'{indent}_ldpl_et: str = ""',
    ]


def _sync_error_vars(io_track: bool, indent: str) -> list[str]:
    if not io_track:
        return []
    return [
        f"{indent}errorcode = _ldpl_ec",
        f"{indent}errortext = _ldpl_et",
    ]


def _wrap_load(path_code: str, target_py: str, indent: str, track: bool) -> list[str]:
    if not track:
        return [
            f"{indent}try:",
            f"{indent}    {target_py} = Path({path_code}).read_text(encoding='utf-8')",
            f"{indent}except OSError:",
            f'{indent}    {target_py} = ""',
        ]
    return [
        f"{indent}try:",
        f"{indent}    {target_py} = Path({path_code}).read_text(encoding='utf-8')",
        f"{indent}    _ldpl_ec = 0.0",
        f'{indent}    _ldpl_et = ""',
        f"{indent}except OSError:",
        f"{indent}    _ldpl_ec = 1.0",
        f'{indent}    _ldpl_et = "The file could not be opened."',
        f'{indent}    {target_py} = ""',
    ]


def _wrap_write(
    val_code: str,
    path_code: str,
    indent: str,
    track: bool,
    append: bool,
) -> list[str]:
    lines = [
        f"{indent}try:",
        f"{indent}    _p = Path({path_code})",
        f"{indent}    _p.parent.mkdir(parents=True, exist_ok=True)",
    ]
    if append:
        lines.append(f"{indent}    with _p.open('a', encoding='utf-8') as _f:")
        lines.append(f"{indent}        _f.write(str({val_code}))")
    else:
        lines.append(f"{indent}    _p.write_text(str({val_code}), encoding='utf-8')")
    if track:
        lines.extend(
            [
                f"{indent}    _ldpl_ec = 0.0",
                f'{indent}    _ldpl_et = ""',
            ]
        )
    lines.append(f"{indent}except OSError:")
    if track:
        lines.extend(
            [
                f"{indent}    _ldpl_ec = 1.0",
                f'{indent}    _ldpl_et = "Could not write to file"',
            ]
        )
    else:
        lines.append(f"{indent}    pass")
    return lines


def _emit_stmt(
    stmt: Statement,
    program: Program,
    types: dict[str, VarKind],
    indent: str,
    temp_id: list[int],
    param_boxes: frozenset[str] | None,
    io_track: bool,
) -> list[str]:
    def _inner(ch: Statement, ind: str) -> list[str]:
        return _emit_stmt(ch, program, types, ind, temp_id, param_boxes, io_track)

    if isinstance(stmt, StoreStmt):
        return [f"{indent}{line}" for line in _emit_store_lines(stmt, types, param_boxes)]
    if isinstance(stmt, PushStmt):
        return [f"{indent}{line}" for line in _emit_push_lines(stmt, types, param_boxes)]
    if isinstance(stmt, DisplayStmt):
        return [f"{indent}{_emit_display_parts(stmt.parts, types, param_boxes)}"]
    if isinstance(stmt, JoinStmt):
        parts = _emit_join_chunks(stmt.parts, types, param_boxes)
        target = _emit_var(stmt.target, param_boxes)
        return [f"{indent}{target} = ''.join([{', '.join(parts)}])"]
    if isinstance(stmt, SolveStmt):
        tk = types[stmt.target]
        rhs = _emit_math(stmt.expr, types, param_boxes)
        tgt = _emit_var(stmt.target, param_boxes)
        if stmt.key is None:
            if tk in (VarKind.NUMBER_LIST, VarKind.TEXT_LIST, VarKind.NUMBER_MAP, VarKind.TEXT_MAP):
                raise TypeError("solve indexado requiere : clave")
            return [f"{indent}{tgt} = {rhs}"]
        key = stmt.key
        if tk == VarKind.NUMBER_LIST:
            ix = f"int(float({_emit_expr(key, param_boxes)}))"
            return [f"{indent}{tgt}[{ix}] = {rhs}"]
        if tk == VarKind.TEXT_LIST:
            ix = f"int(float({_emit_expr(key, param_boxes)}))"
            return [f"{indent}{tgt}[{ix}] = str({rhs})"]
        if tk == VarKind.NUMBER_MAP:
            mk = _emit_map_key(key, types, param_boxes)
            return [f"{indent}{tgt}[{mk}] = {rhs}"]
        if tk == VarKind.TEXT_MAP:
            mk = _emit_map_key(key, types, param_boxes)
            return [f"{indent}{tgt}[{mk}] = str({rhs})"]
        raise TypeError(tk)
    if isinstance(stmt, AcceptStmt):
        return _emit_accept_lines(stmt, types, indent, param_boxes)
    if isinstance(stmt, AddStmt):
        t = _emit_var(stmt.target, param_boxes)
        a = _emit_numeric_operand(stmt.left, types, param_boxes)
        b = _emit_numeric_operand(stmt.right, types, param_boxes)
        return [f"{indent}{t} = ({a} + {b})"]
    if isinstance(stmt, SubtractStmt):
        t = _emit_var(stmt.target, param_boxes)
        a = _emit_numeric_operand(stmt.left, types, param_boxes)
        b = _emit_numeric_operand(stmt.right, types, param_boxes)
        return [f"{indent}{t} = ({b} - {a})"]
    if isinstance(stmt, MultiplyStmt):
        t = _emit_var(stmt.target, param_boxes)
        a = _emit_numeric_operand(stmt.left, types, param_boxes)
        b = _emit_numeric_operand(stmt.right, types, param_boxes)
        return [f"{indent}{t} = ({a} * {b})"]
    if isinstance(stmt, DivideStmt):
        t = _emit_var(stmt.target, param_boxes)
        a = _emit_numeric_operand(stmt.left, types, param_boxes)
        b = _emit_numeric_operand(stmt.right, types, param_boxes)
        return [f"{indent}{t} = ({a} / {b})"]
    if isinstance(stmt, ModuloStmt):
        t = _emit_var(stmt.target, param_boxes)
        a = _emit_numeric_operand(stmt.left, types, param_boxes)
        b = _emit_numeric_operand(stmt.right, types, param_boxes)
        return [f"{indent}{t} = ({a} % {b})"]
    if isinstance(stmt, FloorStmt):
        t = _emit_var(stmt.target, param_boxes)
        x = _emit_numeric_operand(stmt.src, types, param_boxes)
        return [f"{indent}{t} = float(math.floor({x}))"]
    if isinstance(stmt, CeilStmt):
        t = _emit_var(stmt.target, param_boxes)
        x = _emit_numeric_operand(stmt.src, types, param_boxes)
        return [f"{indent}{t} = float(math.ceil({x}))"]
    if isinstance(stmt, IncrementStmt):
        v = _emit_var(stmt.var, param_boxes)
        return [f"{indent}{v} = float({v}) + 1.0"]
    if isinstance(stmt, DecrementStmt):
        v = _emit_var(stmt.var, param_boxes)
        return [f"{indent}{v} = float({v}) - 1.0"]
    if isinstance(stmt, GetRandomStmt):
        t = _emit_var(stmt.target, param_boxes)
        return [f"{indent}{t} = float(random.random())"]
    if isinstance(stmt, GetLengthStmt):
        t = _emit_var(stmt.target, param_boxes)
        s = _emit_text_operand(stmt.source, types, param_boxes)
        return [f"{indent}{t} = float(len(str({s})))"]
    if isinstance(stmt, TrimStmt):
        t = _emit_var(stmt.target, param_boxes)
        s = _emit_text_operand(stmt.source, types, param_boxes)
        return [f"{indent}{t} = str({s}).strip()"]
    if isinstance(stmt, ReplaceStmt):
        t = _emit_var(stmt.target, param_boxes)
        old = _emit_text_operand(stmt.old, types, param_boxes)
        new = _emit_text_operand(stmt.new, types, param_boxes)
        return [f"{indent}{t} = str({t}).replace({old}, {new})"]
    if isinstance(stmt, LoadFileStmt):
        path_c = _emit_text_operand(stmt.path, types, param_boxes)
        tgt = _emit_var(stmt.target, param_boxes)
        io_lines = _wrap_load(path_c, tgt, indent, io_track)
        return [*io_lines, *_sync_error_vars(io_track, indent)]
    if isinstance(stmt, WriteFileStmt):
        val_c = _emit_text_operand(stmt.value, types, param_boxes)
        path_c = _emit_text_operand(stmt.path, types, param_boxes)
        io_lines = _wrap_write(val_c, path_c, indent, io_track, append=False)
        return [*io_lines, *_sync_error_vars(io_track, indent)]
    if isinstance(stmt, AppendFileStmt):
        val_c = _emit_text_operand(stmt.value, types, param_boxes)
        path_c = _emit_text_operand(stmt.path, types, param_boxes)
        io_lines = _wrap_write(val_c, path_c, indent, io_track, append=True)
        return [*io_lines, *_sync_error_vars(io_track, indent)]
    if isinstance(stmt, CallStmt):
        return _emit_call(stmt, program, types, indent, temp_id, param_boxes)
    if isinstance(stmt, ReturnStmt):
        return [f"{indent}return"]
    if isinstance(stmt, IfStmt):
        lines: list[str] = []
        first = True
        for cond, branch_body in stmt.branches:
            kw = "if" if first else "elif"
            first = False
            lines.append(f"{indent}{kw} {_emit_bool(cond, types, param_boxes)}:")
            if branch_body:
                for st_i in branch_body:
                    lines.extend(_inner(st_i, indent + "    "))
            else:
                lines.append(f"{indent}    pass")
        if stmt.else_body is not None:
            lines.append(f"{indent}else:")
            if stmt.else_body:
                for st_i in stmt.else_body:
                    lines.extend(_inner(st_i, indent + "    "))
            else:
                lines.append(f"{indent}    pass")
        return lines
    if isinstance(stmt, WhileStmt):
        wh_cond = _emit_bool(stmt.condition, types, param_boxes)
        wlines = [f"{indent}while {wh_cond}:"]
        if stmt.body:
            for st_i in stmt.body:
                wlines.extend(_inner(st_i, indent + "    "))
        else:
            wlines.append(f"{indent}    pass")
        return wlines
    if isinstance(stmt, ForStmt):
        tid = temp_id[0]
        temp_id[0] += 1
        c = _emit_var(stmt.counter, param_boxes)
        end_v = f"_ldpl_for_{tid}_end"
        step_v = f"_ldpl_for_{tid}_step"
        start_e = _emit_expr(stmt.start, param_boxes)
        end_e = _emit_expr(stmt.end, param_boxes)
        step_e = _emit_expr(stmt.step, param_boxes)
        lines = [
            f"{indent}{c} = float({start_e})",
            f"{indent}{end_v} = float({end_e})",
            f"{indent}{step_v} = float({step_e})",
            f"{indent}if {step_v} >= 0:",
            f"{indent}    while {c} < {end_v}:",
        ]
        if stmt.body:
            for st_i in stmt.body:
                lines.extend(_inner(st_i, indent + "        "))
        else:
            lines.append(f"{indent}        pass")
        lines.extend(
            [
                f"{indent}        {c} += {step_v}",
                f"{indent}else:",
                f"{indent}    while {c} > {end_v}:",
            ]
        )
        if stmt.body:
            for st_i in stmt.body:
                lines.extend(_inner(st_i, indent + "        "))
        else:
            lines.append(f"{indent}        pass")
        lines.append(f"{indent}        {c} += {step_v}")
        return lines
    if isinstance(stmt, ForEachStmt):
        item = _emit_var(stmt.item_var, param_boxes)
        container = _emit_var(stmt.container, param_boxes)
        flines = [f"{indent}for {item} in {container}:"]
        if stmt.body:
            for st_i in stmt.body:
                flines.extend(_inner(st_i, indent + "    "))
        else:
            flines.append(f"{indent}    pass")
        return flines
    if isinstance(stmt, BreakStmt):
        return [f"{indent}break"]
    if isinstance(stmt, ContinueStmt):
        return [f"{indent}continue"]
    raise TypeError(stmt)


def _init_decl_line(d: VarDecl, indent: str) -> str:
    name = _py_name(d.name)
    if d.kind == VarKind.NUMBER:
        return f"{indent}{name}: float = 0.0"
    if d.kind == VarKind.TEXT:
        return f'{indent}{name}: str = ""'
    if d.kind == VarKind.NUMBER_LIST:
        return f"{indent}{name}: list[float] = []"
    if d.kind == VarKind.TEXT_LIST:
        return f"{indent}{name}: list[str] = []"
    if d.kind == VarKind.NUMBER_MAP:
        return f"{indent}{name}: dict[str, float] = {{}}"
    if d.kind == VarKind.TEXT_MAP:
        return f"{indent}{name}: dict[str, str] = {{}}"
    raise TypeError(d.kind)


def _emit_sub_body(
    sub: SubDef,
    program: Program,
    gtypes: dict[str, VarKind],
    temp_id: list[int],
    io_track: bool,
) -> list[str]:
    merged: dict[str, VarKind] = {
        **gtypes,
        **{p.name: p.kind for p in sub.parameters},
        **{loc.name: loc.kind for loc in sub.locals},
    }
    pnames = frozenset(p.name for p in sub.parameters)
    fn = _sanitize_sub_name(sub.name)
    params_sig = ", ".join(f"{_py_name(p.name)}_box" for p in sub.parameters)
    lines = [f"    def ldpl_sub_{fn}({params_sig}) -> None:"]
    for loc in sub.locals:
        lines.append(_init_decl_line(loc, "        "))
    for st in sub.body:
        lines.extend(_emit_stmt(st, program, merged, "        ", temp_id, pnames, io_track))
    return lines


def _uses_io_stmts(program: Program) -> bool:
    io_types = (
        LoadFileStmt,
        WriteFileStmt,
        AppendFileStmt,
    )

    def walk(stmts: tuple[Statement, ...]) -> bool:
        for s in stmts:
            if isinstance(s, io_types):
                return True
            if isinstance(s, IfStmt):
                for _, b in s.branches:
                    if walk(b):
                        return True
                if s.else_body and walk(s.else_body):
                    return True
            if isinstance(s, (WhileStmt, ForStmt, ForEachStmt)) and walk(s.body):
                return True
        return False

    return walk(program.statements) or any(walk(sub.body) for sub in program.subs)


def transpile(program: Program) -> str:
    gtypes: dict[str, VarKind] = {d.name: d.kind for d in program.declarations}
    decl_names = {d.name.lower() for d in program.declarations}
    io_track = "errorcode" in decl_names and "errortext" in decl_names and _uses_io_stmts(program)
    temp_id = [0]
    lines: list[str] = [
        '"""Generado por ldpltopy — subset LDPL."""',
        "",
        "from __future__ import annotations",
        "",
        "import math",
        "import random",
        "from pathlib import Path",
        "",
        _ldpl_helpers(),
        "def main() -> None:",
    ]
    for d in program.declarations:
        lines.append(_init_decl_line(d, "    "))
    lines.extend(_emit_io_prologue(io_track, "    "))
    for sub in program.subs:
        lines.extend(_emit_sub_body(sub, program, gtypes, temp_id, io_track))
    sync_io = []
    if io_track:
        sync_io = [
            "    errorcode = _ldpl_ec",
            "    errortext = _ldpl_et",
        ]
    main_stmts: list[str] = []
    for stmt in program.statements:
        main_stmts.extend(_emit_stmt(stmt, program, gtypes, "    ", temp_id, None, io_track))
    if io_track and sync_io:
        # insert sync before last statements if any load ran — simplest: after all main
        lines.extend(main_stmts)
        lines.extend(sync_io)
    else:
        lines.extend(main_stmts)
    lines.extend(["", "", 'if __name__ == "__main__":', "    main()", ""])
    return "\n".join(lines)
