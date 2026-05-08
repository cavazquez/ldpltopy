"""Nodos AST del subset LDPL soportado."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal


class CmpOp(Enum):
    EQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()


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

DisplayPart = Expr | Literal["lf", "crlf"]


@dataclass(frozen=True, slots=True)
class VarDecl:
    name: str
    is_number: bool  # True = number, False = text


@dataclass(frozen=True, slots=True)
class StoreStmt:
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


@dataclass(frozen=True, slots=True)
class AcceptStmt:
    target: str


@dataclass(frozen=True, slots=True)
class IfStmt:
    condition_left: Expr
    op: CmpOp
    condition_right: Expr
    then_body: tuple[Statement, ...]
    else_body: tuple[Statement, ...] | None


@dataclass(frozen=True, slots=True)
class WhileStmt:
    condition_left: Expr
    op: CmpOp
    condition_right: Expr
    body: tuple[Statement, ...]


Statement = StoreStmt | DisplayStmt | JoinStmt | SolveStmt | AcceptStmt | IfStmt | WhileStmt


@dataclass(frozen=True, slots=True)
class Program:
    declarations: tuple[VarDecl, ...]
    statements: tuple[Statement, ...]
