"""Nodos AST del subset LDPL soportado."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Literal


class CmpOp(Enum):
    EQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()


class VarKind(Enum):
    NUMBER = auto()
    TEXT = auto()
    NUMBER_LIST = auto()
    TEXT_LIST = auto()
    NUMBER_MAP = auto()
    TEXT_MAP = auto()


@dataclass(frozen=True, slots=True)
class NumberLit:
    value: float


@dataclass(frozen=True, slots=True)
class StringLit:
    value: str


@dataclass(frozen=True, slots=True)
class VarRef:
    name: str


Expr = NumberLit | StringLit | VarRef


@dataclass(frozen=True, slots=True)
class IndexRef:
    """Acceso `base : clave` en display/join (mapa o lista)."""

    base: str
    key: Expr


DisplayPart = Expr | IndexRef | Literal["lf", "crlf"]


@dataclass(frozen=True, slots=True)
class VarDecl:
    name: str
    kind: VarKind


@dataclass(frozen=True, slots=True)
class CmpPredicate:
    left: Expr
    op: CmpOp
    right: Expr


@dataclass(frozen=True, slots=True)
class BoolNot:
    inner: BoolExpr


@dataclass(frozen=True, slots=True)
class BoolAnd:
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True, slots=True)
class BoolOr:
    left: BoolExpr
    right: BoolExpr


BoolExpr = CmpPredicate | BoolNot | BoolAnd | BoolOr


@dataclass(frozen=True, slots=True)
class StoreStmt:
    value: Expr
    target: str
    key: Expr | None = None


@dataclass(frozen=True, slots=True)
class PushStmt:
    value: Expr
    target: str


@dataclass(frozen=True, slots=True)
class DisplayStmt:
    parts: tuple[DisplayPart, ...]


@dataclass(frozen=True, slots=True)
class JoinStmt:
    target: str
    parts: tuple[DisplayPart, ...]


@dataclass(frozen=True, slots=True)
class MathBin:
    op: Literal["+", "-", "*", "/"]
    left: MathExpr
    right: MathExpr


@dataclass(frozen=True, slots=True)
class MathNeg:
    inner: MathExpr


MathExpr = NumberLit | VarRef | MathBin | MathNeg


@dataclass(frozen=True, slots=True)
class SolveStmt:
    target: str
    expr: MathExpr
    key: Expr | None = None


@dataclass(frozen=True, slots=True)
class AcceptStmt:
    target: str


# --- Aritmética “por sentencia” (Fase 2) ---


@dataclass(frozen=True, slots=True)
class AddStmt:
    left: Expr
    right: Expr
    target: str


@dataclass(frozen=True, slots=True)
class SubtractStmt:
    left: Expr
    right: Expr
    target: str


@dataclass(frozen=True, slots=True)
class MultiplyStmt:
    left: Expr
    right: Expr
    target: str


@dataclass(frozen=True, slots=True)
class DivideStmt:
    left: Expr
    right: Expr
    target: str


@dataclass(frozen=True, slots=True)
class ModuloStmt:
    left: Expr
    right: Expr
    target: str


@dataclass(frozen=True, slots=True)
class FloorStmt:
    src: Expr
    target: str


@dataclass(frozen=True, slots=True)
class CeilStmt:
    src: Expr
    target: str


@dataclass(frozen=True, slots=True)
class IncrementStmt:
    var: str


@dataclass(frozen=True, slots=True)
class DecrementStmt:
    var: str


@dataclass(frozen=True, slots=True)
class GetRandomStmt:
    target: str


# --- Texto (Fase 2) ---


@dataclass(frozen=True, slots=True)
class GetLengthStmt:
    source: Expr
    target: str


@dataclass(frozen=True, slots=True)
class TrimStmt:
    source: Expr
    target: str


@dataclass(frozen=True, slots=True)
class ReplaceStmt:
    old: Expr
    new: Expr
    target: str


# --- I/O archivos (Fase 5) ---


@dataclass(frozen=True, slots=True)
class LoadFileStmt:
    path: Expr
    target: str


@dataclass(frozen=True, slots=True)
class WriteFileStmt:
    value: Expr
    path: Expr


@dataclass(frozen=True, slots=True)
class AppendFileStmt:
    value: Expr
    path: Expr


# --- Subrutinas (Fase 4) ---


@dataclass(frozen=True, slots=True)
class CallStmt:
    name: str
    args: tuple[Expr, ...]


@dataclass(frozen=True, slots=True)
class ReturnStmt:
    pass


@dataclass(frozen=True, slots=True)
class IfStmt:
    branches: tuple[tuple[BoolExpr, tuple[Statement, ...]], ...]
    else_body: tuple[Statement, ...] | None


@dataclass(frozen=True, slots=True)
class WhileStmt:
    condition: BoolExpr
    body: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class ForStmt:
    counter: str
    start: Expr
    end: Expr
    step: Expr
    body: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class ForEachStmt:
    item_var: str
    container: str
    body: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class BreakStmt:
    pass


@dataclass(frozen=True, slots=True)
class ContinueStmt:
    pass


Statement = (
    StoreStmt
    | PushStmt
    | DisplayStmt
    | JoinStmt
    | SolveStmt
    | AcceptStmt
    | AddStmt
    | SubtractStmt
    | MultiplyStmt
    | DivideStmt
    | ModuloStmt
    | FloorStmt
    | CeilStmt
    | IncrementStmt
    | DecrementStmt
    | GetRandomStmt
    | GetLengthStmt
    | TrimStmt
    | ReplaceStmt
    | LoadFileStmt
    | WriteFileStmt
    | AppendFileStmt
    | CallStmt
    | ReturnStmt
    | IfStmt
    | WhileStmt
    | ForStmt
    | ForEachStmt
    | BreakStmt
    | ContinueStmt
)


@dataclass(frozen=True, slots=True)
class SubDef:
    name: str
    parameters: tuple[VarDecl, ...]
    locals: tuple[VarDecl, ...]
    body: tuple[Statement, ...]


@dataclass(frozen=True, slots=True)
class Program:
    declarations: tuple[VarDecl, ...]
    statements: tuple[Statement, ...]
    subs: tuple[SubDef, ...] = field(default_factory=tuple)
