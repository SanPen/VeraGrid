# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import ast
import math
import pprint
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, BlkFrom, BlkGoto, BlkRef, BlkSig, BlkSlot, BlkSum, ElmComp, ElmDsl, DGSElement
from VeraGridEngine.Utils.procedural_logic import (
    AnalogFlipFlopLogic,
    FixedSampleLogic,
    FlipFlopLogic,
    PickupDropoffLogic,
    ResetOnRisingEdgeLogic,
    SampledValueLogic,
    clone_procedural_logic_entries,
)
from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Func2, Var, abs, cos, exp, hard_sat, log, max, min, sin, sqrt
from VeraGridEngine.enumerations import BlockScopeMode


STRICT_PROCEDURAL_LOGIC_ONLY: bool = True

def _safe_name(name: str) -> str:
    cleaned: str = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if cleaned == "":
        cleaned = "unnamed"
    if cleaned[0].isdigit():
        cleaned = f"v_{cleaned}"
    return cleaned


def _split_symbol_blob(raw: str) -> List[str]:
    values: List[str] = list()
    token: List[str] = list()

    for ch in raw:
        if ch in {',', ';'}:
            item = ''.join(token).strip()
            if item:
                values.append(item)
            token = list()
        else:
            token.append(ch)

    item = ''.join(token).strip()
    if item:
        values.append(item)

    return values


def _split_equation_statements(raw_equations: Iterable[str]) -> List[str]:
    statements: List[str] = list()

    for blob in raw_equations:
        token: List[str] = list()
        in_single_quote: bool = False
        in_double_quote: bool = False

        for ch in blob:
            if ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                token.append(ch)
            elif ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                token.append(ch)
            elif ch == ';' and not in_single_quote and not in_double_quote:
                stmt = ''.join(token).split('!', 1)[0].strip().strip('"')
                if stmt != "" and not stmt.startswith('!'):
                    statements.append(stmt)
                token = list()
            else:
                token.append(ch)

        stmt = ''.join(token).split('!', 1)[0].strip().strip('"')
        if stmt != "" and not stmt.startswith('!'):
            statements.append(stmt)

    return statements


def classify_dgs_statement(statement: str) -> tuple[str, str | None]:
    """
    Classify a single DGS equation statement.

    :param statement: One normalized statement.
    :return: Pair ``(kind, lhs_name_or_none)``.
    """
    stmt = statement.strip()

    if stmt == "" or stmt.startswith('!'):
        return 'ignored', None

    if (stmt.startswith("'") and stmt.endswith("'")) or (stmt.startswith('"') and stmt.endswith('"')):
        return 'ignored', None

    if stmt.startswith('vardef('):
        return 'ignored', None

    init_match = re.match(r'^(?P<kind>inc0?|inc)\((?P<lhs>[^\)]+)\)\s*=\s*(?P<rhs>.+)$', stmt)
    if init_match is not None:
        return init_match.group('kind').strip(), init_match.group('lhs').strip()

    diff_match = re.match(r'^(?P<lhs>.+?)\.\s*=\s*(?P<rhs>.+)$', stmt)
    if diff_match is not None:
        return 'state', diff_match.group('lhs').strip()

    if re.match(r'^reset\s*\(.+\)\s*$', stmt) is not None:
        return 'procedural', None

    alg_match = re.match(r'^(?P<lhs>[^=]+?)\s*=\s*(?P<rhs>.+)$', stmt)
    if alg_match is not None:
        return 'algebraic', alg_match.group('lhs').strip()

    return 'unsupported', None


def build_blkdef_statement_support_report(blkdef: BlkDef) -> List[DgsStatementReportEntry]:
    """
    Build a line-by-line support report for one DGS block definition.

    :param blkdef: Block definition to inspect.
    :return: Ordered support report entries.
    """
    shared_signals: Dict[str, Var] = dict()
    symbol_table, _state_vars, _state_var_map, _diff_var_map, _param_var_map = _build_symbol_table(blkdef, shared_signals)
    _predeclare_statement_lhs_symbols(blkdef, symbol_table)
    parser = DgsExpressionParser(symbol_table, block_name=blkdef.loc_name)

    report: List[DgsStatementReportEntry] = list()
    init_seen: Set[str] = set()

    for idx, stmt in enumerate(_split_equation_statements(blkdef.equations_raw), start=1):
        kind, lhs = classify_dgs_statement(stmt)

        if kind == 'ignored':
            report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'ignored', 'ignored by parser policy'))
            continue

        if kind == 'procedural':
            try:
                parser.parse_procedural_statement(stmt)
            except UnsupportedDgsExpression as exc:
                report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'unsupported', str(exc)))
                continue

            report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'supported', 'parsed successfully'))
            continue

        rhs_text: str | None = None
        if kind in {'inc', 'inc0'}:
            match = re.match(r'^(?P<kind>inc0?|inc)\((?P<lhs>[^\)]+)\)\s*=\s*(?P<rhs>.+)$', stmt)
            if match is not None:
                rhs_text = match.group('rhs').strip()
        elif kind == 'state':
            match = re.match(r'^(?P<lhs>.+?)\.\s*=\s*(?P<rhs>.+)$', stmt)
            if match is not None:
                rhs_text = match.group('rhs').strip()
        elif kind == 'algebraic':
            match = re.match(r'^(?P<lhs>[^=]+?)\s*=\s*(?P<rhs>.+)$', stmt)
            if match is not None:
                rhs_text = match.group('rhs').strip()
        else:
            report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'unsupported', 'statement shape unsupported'))
            continue

        if rhs_text is None:
            report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'unsupported', 'could not isolate RHS'))
            continue

        if lhs is not None and lhs not in symbol_table:
            symbol_table[lhs] = Var(name=f"{blkdef.loc_name}__{lhs}")
            parser._replacement_map[_safe_name(lhs)] = lhs

        try:
            rhs_expr = parser.parse(rhs_text)
        except UnsupportedDgsExpression as exc:
            report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'unsupported', str(exc)))
            continue

        if isinstance(rhs_expr, Comparison):
            rhs_expr = rhs_expr.to_expression()

        if kind == 'inc0' and lhs is not None and lhs in init_seen:
            report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'ignored', 'inc0 skipped because init already exists'))
            continue

        if kind in {'inc', 'inc0'} and lhs is not None:
            init_seen.add(lhs)

        report.append(DgsStatementReportEntry(idx, stmt, kind, lhs, 'supported', 'parsed successfully'))

    return report


def summarize_blkdef_support_report(entries: List[DgsStatementReportEntry]) -> Dict[str, int]:
    """
    Count statuses and statement kinds from a support report.

    :param entries: Statement report entries.
    :return: Summary counters.
    """
    summary: Dict[str, int] = {
        'supported': 0,
        'unsupported': 0,
        'ignored': 0,
        'state': 0,
        'algebraic': 0,
        'inc': 0,
        'inc0': 0,
        'procedural': 0,
    }

    for entry in entries:
        summary[entry.status] = summary.get(entry.status, 0) + 1
        summary[entry.kind] = summary.get(entry.kind, 0) + 1

    return summary


def _comparison_to_expr(obj: Expr | Comparison) -> Expr:
    if isinstance(obj, Comparison):
        return obj.to_expression()
    return obj

class ElmCompInstanceEntry:
    """
    One direct instance declared inside an ElmComp through pblk/pelm.

    :param slot_id: Slot identifier.
    :param slot_name: Slot display name.
    :param element_id: Instantiated element identifier.
    :param element_name: Instantiated element display name.
    :param element_kind: Element kind, for example ElmDsl or ElmComp.
    :param type_id: Underlying BlkDef identifier if available.
    :param type_name: Underlying BlkDef display name if available.
    """

    __slots__ = (
        "slot_id",
        "slot_name",
        "element_id",
        "element_name",
        "element_kind",
        "type_id",
        "type_name",
        "parameter_values",
    )

    def __init__(
        self,
        slot_id: str | None,
        slot_name: str | None,
        element_id: str | None,
        element_name: str | None,
        element_kind: str | None,
        type_id: str | None,
        type_name: str | None,
        parameter_values: Dict[str, Any] | None = None,
    ) -> None:
        self.slot_id: str | None = slot_id
        self.slot_name: str | None = slot_name
        self.element_id: str | None = element_id
        self.element_name: str | None = element_name
        self.element_kind: str | None = element_kind
        self.type_id: str | None = type_id
        self.type_name: str | None = type_name
        self.parameter_values: Dict[str, Any] = dict(parameter_values or {})


class DgsBlockInstanceSelection:
    """
    Selection result for a block resolved from the root ElmComp slots.

    :param instance_entry: Matched root instance entry.
    :param parsed_block: Parsed block definition associated to the entry.
    """

    __slots__ = ("instance_entry", "parsed_block")

    def __init__(
        self,
        instance_entry: ElmCompInstanceEntry,
        parsed_block: "ParsedDgsBlockDefinition",
    ) -> None:
        self.instance_entry: ElmCompInstanceEntry = instance_entry
        self.parsed_block: ParsedDgsBlockDefinition = parsed_block

class UnsupportedDgsExpression(Exception):
    pass


def _split_top_level_dsl_operator(expr: str, token: str) -> Tuple[str, str] | None:
    depth: int = 0
    text = expr.strip()
    token_len = len(token)
    idx: int = 0

    while idx <= len(text) - token_len:
        ch = text[idx]
        if ch == '(':
            depth += 1
            idx += 1
            continue
        if ch == ')':
            depth = max(0, depth - 1)
            idx += 1
            continue

        if depth == 0 and text[idx:idx + token_len].lower() == token:
            left = text[:idx].strip()
            right = text[idx + token_len:].strip()
            if left and right:
                return left, right
            return None

        idx += 1

    return None


def _predeclare_statement_lhs_symbols(blkdef: BlkDef, symbol_table: Dict[str, Var]) -> None:
    for stmt in _split_equation_statements(blkdef.equations_raw):
        kind, lhs = classify_dgs_statement(stmt)
        if kind in {'inc', 'inc0', 'state', 'algebraic'} and lhs is not None and lhs not in symbol_table:
            symbol_table[lhs] = Var(name=f"{blkdef.loc_name}__{lhs}")


class DgsExpressionParser(ast.NodeVisitor):
    def __init__(self, symbol_table: Dict[str, Var], block_name: str = ""):
        self.symbol_table = symbol_table
        self.block_name = block_name
        self._replacement_map: Dict[str, str] = {_safe_name(name): name for name in symbol_table.keys()}
        self._procedural_mode_defaults: Dict[Var, Expr | Const] = dict()
        self._procedural_logic_entries: List[Any] = list()
        self._procedural_counter: int = 0
        self._time_var: Var | None = None

    @property
    def procedural_mode_defaults(self) -> Dict[Var, Expr | Const]:
        return self._procedural_mode_defaults

    @property
    def procedural_logic_entries(self) -> List[Any]:
        return self._procedural_logic_entries

    def _new_procedural_mode_var(self, prefix: str) -> Var:
        base_name = f"{self.block_name}__proc_{prefix}_{self._procedural_counter}" if self.block_name else f"proc_{prefix}_{self._procedural_counter}"
        self._procedural_counter += 1
        var = Var(name=base_name)
        self.symbol_table[base_name] = var
        self._replacement_map[_safe_name(base_name)] = base_name
        self._procedural_mode_defaults[var] = Const(0.0)
        return var

    def _get_time_var(self) -> Var:
        if self._time_var is None:
            self._time_var = Var(name='glob_time')
        return self._time_var

    def parse_procedural_statement(self, statement: str) -> None:
        try:
            tree = ast.parse(self.preprocess(statement), mode='eval')
        except SyntaxError as exc:
            raise UnsupportedDgsExpression(str(exc)) from exc

        node = tree.body
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            raise UnsupportedDgsExpression("Unsupported procedural statement")

        if node.func.id != 'reset' or len(node.args) != 3:
            raise UnsupportedDgsExpression(f"Unsupported procedural helper '{node.func.id}'")

        target_node = node.args[0]
        if not isinstance(target_node, ast.Name):
            raise UnsupportedDgsExpression("reset target must be a DSL variable name")

        target_original = self._replacement_map.get(target_node.id)
        if target_original is None or target_original not in self.symbol_table:
            raise UnsupportedDgsExpression(f"Unknown reset target '{target_node.id}'")

        target_var = self.symbol_table[target_original]
        reset_expr = self.visit(node.args[1])
        value_expr = self.visit(node.args[2])

        self._procedural_logic_entries.append(
            ResetOnRisingEdgeLogic(
                target_var_name=target_var.name,
                reset_expr=reset_expr,
                value_expr=value_expr,
                name=f"{target_var.name}_reset",
            )
        )

    def preprocess(self, expr: str) -> str:
        text: str = expr.strip()
        text = text.replace('^', '**')
        text = text.replace('.and.', ' and ')
        text = text.replace('.or.', ' or ')
        text = text.replace('.not.', ' not ')
        text = re.sub(r'(?<![<>=!])=(?!=)', '==', text)

        replacements: List[Tuple[str, str]] = list()
        for name in sorted(self.symbol_table.keys(), key=len, reverse=True):
            replacements.append((name, _safe_name(name)))

        for original, safe in replacements:
            text = re.sub(re.escape(original), safe, text)

        return text

    def parse(self, expr: str) -> Expr | Comparison:
        for token in ['.nor.', '.nand.', '.eor.']:
            split_parts = _split_top_level_dsl_operator(expr, token)
            if split_parts is not None:
                left_raw, right_raw = split_parts
                left_expr = _comparison_to_expr(self.parse(left_raw))
                right_expr = _comparison_to_expr(self.parse(right_raw))

                if token == '.nor.':
                    return (Const(1.0) - left_expr) * (Const(1.0) - right_expr)
                if token == '.nand.':
                    return Const(1.0) - left_expr * right_expr
                return left_expr + right_expr - Const(2.0) * left_expr * right_expr

        try:
            tree = ast.parse(self.preprocess(expr), mode='eval')
        except SyntaxError as exc:
            raise UnsupportedDgsExpression(str(exc)) from exc
        return self.visit(tree.body)

    def visit_Name(self, node: ast.Name) -> Expr:
        original: str | None = self._replacement_map.get(node.id)
        if original is None or original not in self.symbol_table:
            raise UnsupportedDgsExpression(f"Unknown symbol '{node.id}'")
        return self.symbol_table[original]

    def visit_Constant(self, node: ast.Constant) -> Expr:
        if isinstance(node.value, (int, float)):
            return Const(float(node.value))
        raise UnsupportedDgsExpression(f"Unsupported constant '{node.value}'")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Expr:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.Not):
            return Const(1.0) - _comparison_to_expr(operand)
        raise UnsupportedDgsExpression(ast.dump(node))

    def visit_BinOp(self, node: ast.BinOp) -> Expr:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left ** right
        raise UnsupportedDgsExpression(ast.dump(node))

    def visit_Compare(self, node: ast.Compare) -> Comparison:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsupportedDgsExpression("Only simple comparisons are supported")
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        op = node.ops[0]
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Eq):
            return left == right
        raise UnsupportedDgsExpression(ast.dump(node))

    def visit_BoolOp(self, node: ast.BoolOp) -> Expr:
        values = [_comparison_to_expr(self.visit(v)) for v in node.values]
        if isinstance(node.op, ast.And):
            result = values[0]
            for value in values[1:]:
                result = result * value
            return result
        if isinstance(node.op, ast.Or):
            result = values[0]
            for value in values[1:]:
                result = Const(1.0) - (Const(1.0) - result) * (Const(1.0) - value)
            return result
        raise UnsupportedDgsExpression(ast.dump(node))

    def visit_Call(self, node: ast.Call) -> Expr:
        if not isinstance(node.func, ast.Name):
            raise UnsupportedDgsExpression(ast.dump(node))

        name = node.func.id
        args = [self.visit(arg) for arg in node.args]

        if name == 'sin' and len(args) == 1:
            return sin(args[0])
        if name == 'cos' and len(args) == 1:
            return cos(args[0])
        if name == 'sqrt' and len(args) == 1:
            return sqrt(args[0])
        if name == 'abs' and len(args) == 1:
            return abs(args[0])
        if name == 'exp' and len(args) == 1:
            return exp(args[0])
        if name == 'log' and len(args) == 1:
            return log(args[0])
        if name == 'atan2' and len(args) == 2:
            return Func2('atan2', args[0], args[1])
        if name == 'max' and len(args) == 2:
            return max(args[0], args[1])
        if name == 'min' and len(args) == 2:
            return min(args[0], args[1])
        if name == 'sqr' and len(args) == 1:
            return args[0] * args[0]
        if name in {'lim', 'lim_const'} and len(args) == 3:
            return hard_sat(args[0], args[1], args[2])
        if name == 'limstate' and len(args) == 3:
            return hard_sat(args[0], args[1], args[2])
        if name in {'select', 'select_const', 'ifelse'} and len(args) == 3:
            if isinstance(args[0], Const) and args[0].value is not None:
                return args[1] if float(args[0].value) > 0.5 else args[2]

            selector = self._new_procedural_mode_var(name)
            self._procedural_logic_entries.append(
                SampledValueLogic(
                    output_var_name=selector.name,
                    source_expr=args[0],
                    name=selector.name,
                )
            )
            return selector * args[1] + (Const(1.0) - selector) * args[2]
        if name in {'selfix', 'selfix_const'} and len(args) == 3:
            if isinstance(args[0], Const) and args[0].value is not None:
                return args[1] if float(args[0].value) > 0.5 else args[2]
            selector = self._new_procedural_mode_var(name)
            self._procedural_logic_entries.append(
                FixedSampleLogic(
                    output_var_name=selector.name,
                    condition_expr=args[0],
                    name=selector.name,
                )
            )
            return selector * args[1] + (Const(1.0) - selector) * args[2]
        if name == 'lastvalue' and len(args) == 1:
            sampled = self._new_procedural_mode_var(name)
            self._procedural_logic_entries.append(
                SampledValueLogic(
                    output_var_name=sampled.name,
                    source_expr=args[0],
                    name=sampled.name,
                )
            )
            return sampled
        if name == 'flipflop' and len(args) == 2:
            latch = self._new_procedural_mode_var(name)
            self._procedural_logic_entries.append(
                FlipFlopLogic(
                    output_var_name=latch.name,
                    set_expr=args[0],
                    reset_expr=args[1],
                    name=latch.name,
                )
            )
            return latch
        if name == 'aflipflop' and len(args) == 3:
            latch = self._new_procedural_mode_var(name)
            self._procedural_logic_entries.append(
                AnalogFlipFlopLogic(
                    output_var_name=latch.name,
                    input_expr=args[0],
                    set_expr=args[1],
                    reset_expr=args[2],
                    name=latch.name,
                )
            )
            return latch
        if name in {'picdro', 'picdro_const'} and len(args) == 3:
            latch = self._new_procedural_mode_var(name)
            self._procedural_logic_entries.append(
                PickupDropoffLogic(
                    output_var_name=latch.name,
                    bool_expr=args[0],
                    pickup_delay_expr=args[1],
                    drop_delay_expr=args[2],
                    name=latch.name,
                )
            )
            return latch
        if name == 'pi' and len(args) == 0:
            return Const(math.pi)
        if name == 'twopi' and len(args) == 0:
            return Const(2.0 * math.pi)
        if name == 'time' and len(args) == 0:
            return self._get_time_var()
        if name == 'rms' and len(args) == 0:
            return Const(1.0)

        if name in {'inc', 'reset', 'lapprox', 'vardef'}:
            raise UnsupportedDgsExpression(f"Unsupported PowerFactory helper '{name}'")

        raise UnsupportedDgsExpression(f"Unsupported function '{name}'")

    def generic_visit(self, node: ast.AST):
        raise UnsupportedDgsExpression(ast.dump(node))


@dataclass
class ParsedDgsBlockDefinition:
    blkdef: BlkDef
    symbol_table: Dict[str, Var]
    state_rhs: Dict[str, Expr]
    algebraic_rhs: Dict[str, Expr]
    init_rhs: Dict[str, Expr]
    mode_dict: Dict[Var, Expr | Const]
    procedural_logic: List[Any]
    unsupported_lines: List[str]
    signal_dependencies: Dict[str, Set[str]]


@dataclass
class DgsRootBlockResult:
    root_block: Block
    root_blkdef: ParsedDgsBlockDefinition
    root_element: ElmComp
    parsed_blocks: Dict[str, ParsedDgsBlockDefinition]
    dependency_graph: Dict[str, Set[str]]
    producer_map: Dict[str, Set[str]]
    consumer_map: Dict[str, Set[str]]


@dataclass
class DgsBlockSubgraphResult:
    selected_block: ParsedDgsBlockDefinition
    view_block: Block
    node_ids: Set[str]
    dependency_graph: Dict[str, Set[str]]
    upstream: Dict[str, Set[str]]
    downstream: Dict[str, Set[str]]


@dataclass
class GraphicConnectionInstruction:
    consumer_node_id: str
    consumer_input_name: str
    source_kind: str
    consumer_input_index: int | None = None
    source_output_name: str | None = None
    source_output_index: int | None = None
    source_node_id: str | None = None
    source_root_name: str | None = None


class DgsGraphicTreeResult:
    """
    Graphical internal tree reconstruction result.

    :param selected_block: Parsed selected block definition.
    :param view_block: Reconstructed block tree view.
    :param node_ids: Internal graphical node identifiers.
    :param adjacency: Undirected adjacency between graphical nodes.
    :param node_labels: Display label per graphical node.
    :param node_kinds: DGS object kind per graphical node.
    """

    __slots__ = (
        "selected_block",
        "view_block",
        "node_ids",
        "adjacency",
        "node_labels",
        "node_kinds",
        "child_node_ids",
        "connections",
    )

    def __init__(
        self,
        selected_block: ParsedDgsBlockDefinition,
        view_block: Block,
        node_ids: Set[str],
        adjacency: Dict[str, Set[str]],
        node_labels: Dict[str, str],
        node_kinds: Dict[str, str],
        child_node_ids: List[str],
        connections: List[GraphicConnectionInstruction],
    ) -> None:
        self.selected_block = selected_block
        self.view_block = view_block
        self.node_ids = node_ids
        self.adjacency = adjacency
        self.node_labels = node_labels
        self.node_kinds = node_kinds
        self.child_node_ids = child_node_ids
        self.connections = connections


class DgsStatementReportEntry:
    """
    One line-by-line parsing report entry for a DGS block statement.

    :param index: 1-based statement index.
    :type index: int
    :param statement: Original normalized statement.
    :type statement: str
    :param kind: Classified statement kind.
    :type kind: str
    :param lhs: Left-hand side symbol when available.
    :type lhs: str | None
    :param status: Parsing result status.
    :type status: str
    :param detail: Additional explanation.
    :type detail: str
    """

    __slots__ = ("index", "statement", "kind", "lhs", "status", "detail")

    def __init__(
        self,
        index: int,
        statement: str,
        kind: str,
        lhs: str | None,
        status: str,
        detail: str,
    ) -> None:
        self.index = index
        self.statement = statement
        self.kind = kind
        self.lhs = lhs
        self.status = status
        self.detail = detail


def _graph_to_serializable(graph: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    return {key: sorted(values) for key, values in graph.items()}


def _normalize_graph_signal_name(name: str) -> str:
    text = name.strip().strip('"')
    text = re.sub(r'\(\d+\)$', '', text).strip()
    return text


def _iter_blocks_recursive(block: Block) -> Iterable[Block]:
    yield block
    for child in block.children:
        yield from _iter_blocks_recursive(child)


def _make_identifier_map(block: Block) -> Dict[int, str]:
    vars_out: Dict[int, Var] = dict()
    consts_out: Dict[int, Const] = dict()
    _collect_block_vars_recursive(block, vars_out, consts_out)

    used: Dict[str, int] = dict()
    mapping: Dict[int, str] = dict()
    for var in sorted(vars_out.values(), key=lambda item: item.name):
        base = _safe_name(var.name)
        count = used.get(base, 0)
        used[base] = count + 1
        mapping[var.uid] = base if count == 0 else f"{base}_{count}"
    return mapping


def _expr_to_python(expr: Expr, identifier_map: Dict[int, str]) -> str:
    if isinstance(expr, Var):
        return identifier_map[expr.uid]
    if isinstance(expr, Const):
        return f"sym.Const({repr(expr.value)})"
    if isinstance(expr, Func2):
        return f"sym.{expr.name}({_expr_to_python(expr.arg1, identifier_map)}, {_expr_to_python(expr.arg2, identifier_map)})"
    from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, UnOp, Func
    if isinstance(expr, BinOp):
        return f"({_expr_to_python(expr.left, identifier_map)} {expr.op} {_expr_to_python(expr.right, identifier_map)})"
    if isinstance(expr, UnOp):
        return f"({expr.op}{_expr_to_python(expr.operand, identifier_map)})"
    if isinstance(expr, Func):
        return f"sym.{expr.op}({_expr_to_python(expr.arg, identifier_map)})"
    raise TypeError(f"Unsupported expression type for Python export: {type(expr).__name__}")


def _const_or_expr_to_python(value: Expr | Const, identifier_map: Dict[int, str]) -> str:
    if isinstance(value, Const):
        return f"vf.add_const({repr(value.value)}, name={repr(value.name)})"
    return _expr_to_python(value, identifier_map)


def _expr_to_python_natural(expr: Expr, identifier_map: Dict[int, str]) -> str:
    if isinstance(expr, Var):
        return identifier_map[expr.uid]
    if isinstance(expr, Const):
        return repr(expr.value)
    if isinstance(expr, Func2):
        return f"sym.{expr.name}({_expr_to_python_natural(expr.arg1, identifier_map)}, {_expr_to_python_natural(expr.arg2, identifier_map)})"

    from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Func, UnOp

    if isinstance(expr, BinOp):
        return f"({_expr_to_python_natural(expr.left, identifier_map)} {expr.op} {_expr_to_python_natural(expr.right, identifier_map)})"
    if isinstance(expr, UnOp):
        return f"({expr.op}{_expr_to_python_natural(expr.operand, identifier_map)})"
    if isinstance(expr, Func):
        return f"sym.{expr.op}({_expr_to_python_natural(expr.arg, identifier_map)})"
    raise TypeError(f"Unsupported expression type for natural Python export: {type(expr).__name__}")


def _expr_like_to_python(expr: Expr | Comparison, identifier_map: Dict[int, str]) -> str:
    if isinstance(expr, Comparison):
        cmp_op_map = {
            CmpOp.EQ: "==",
            CmpOp.LE: "<=",
            CmpOp.GE: ">=",
            CmpOp.LT: "<",
            CmpOp.GT: ">",
        }
        rhs = _expr_to_python_natural(expr.rhs, identifier_map) if isinstance(expr.rhs, Expr) else repr(expr.rhs)
        return f"({_expr_to_python_natural(expr.lhs, identifier_map)} {cmp_op_map[expr.op]} {rhs})"
    return _expr_to_python_natural(expr, identifier_map)


def _iter_block_local_vars(block: Block) -> List[Var]:
    vars_found: List[Var] = list()
    vars_found.extend(block.state_vars)
    vars_found.extend(block.algebraic_vars)
    vars_found.extend(block.diff_vars)
    vars_found.extend(block.in_vars)
    vars_found.extend(block.out_vars)
    vars_found.extend(list(block.event_dict.keys()))
    vars_found.extend(list(block.mode_dict.keys()))
    return vars_found


def _find_local_var_by_name(block: Block, var_name: str) -> Var:
    for var in _iter_block_local_vars(block):
        if var.name == var_name:
            return var
    raise KeyError(f"Variable '{var_name}' not found in block '{block.name}'")


def _procedural_logic_import_names(block: Block) -> List[str]:
    names: Set[str] = set()
    for item in _iter_blocks_recursive(block):
        for logic in item.procedural_logic:
            if isinstance(logic, FixedSampleLogic):
                names.add("selfix")
            elif isinstance(logic, SampledValueLogic):
                if logic.output_var_name.startswith("proc_select_") or "__proc_select_" in logic.output_var_name or logic.output_var_name.startswith("proc_ifelse_") or "__proc_ifelse_" in logic.output_var_name:
                    names.add("sampled_value")
                else:
                    names.add("lastvalue")
            elif isinstance(logic, FlipFlopLogic):
                names.add("flipflop")
            elif isinstance(logic, AnalogFlipFlopLogic):
                names.add("aflipflop")
            elif isinstance(logic, PickupDropoffLogic):
                names.add("picdro")
            elif isinstance(logic, ResetOnRisingEdgeLogic):
                names.add("reset")
    return sorted(names)


def _procedural_logic_entry_to_python(logic: Any, block: Block, identifier_map: Dict[int, str]) -> str:
    if isinstance(logic, FixedSampleLogic):
        output_var = _find_local_var_by_name(block, logic.output_var_name)
        text = f"selfix({_expr_like_to_python(logic.condition_expr, identifier_map)}, output={identifier_map[output_var.uid]})"
        if logic.name != "" and logic.name != logic.output_var_name:
            text = text[:-1] + f", name={repr(logic.name)})"
        return text

    if isinstance(logic, SampledValueLogic):
        output_var = _find_local_var_by_name(block, logic.output_var_name)
        if logic.output_var_name.startswith("proc_select_") or "__proc_select_" in logic.output_var_name or logic.output_var_name.startswith("proc_ifelse_") or "__proc_ifelse_" in logic.output_var_name:
            text = f"sampled_value(output={identifier_map[output_var.uid]}, source={_expr_like_to_python(logic.source_expr, identifier_map)})"
        else:
            text = f"lastvalue({_expr_like_to_python(logic.source_expr, identifier_map)}, output={identifier_map[output_var.uid]})"
        if logic.name != "" and logic.name != logic.output_var_name:
            text = text[:-1] + f", name={repr(logic.name)})"
        return text

    if isinstance(logic, FlipFlopLogic):
        output_var = _find_local_var_by_name(block, logic.output_var_name)
        text = (
            f"flipflop({_expr_like_to_python(logic.set_expr, identifier_map)}, "
            f"{_expr_like_to_python(logic.reset_expr, identifier_map)}, output={identifier_map[output_var.uid]})"
        )
        if logic.name != "" and logic.name != logic.output_var_name:
            text = text[:-1] + f", name={repr(logic.name)})"
        return text

    if isinstance(logic, AnalogFlipFlopLogic):
        output_var = _find_local_var_by_name(block, logic.output_var_name)
        text = (
            f"aflipflop({_expr_like_to_python(logic.input_expr, identifier_map)}, "
            f"{_expr_like_to_python(logic.set_expr, identifier_map)}, "
            f"{_expr_like_to_python(logic.reset_expr, identifier_map)}, output={identifier_map[output_var.uid]})"
        )
        if logic.name != "" and logic.name != logic.output_var_name:
            text = text[:-1] + f", name={repr(logic.name)})"
        return text

    if isinstance(logic, PickupDropoffLogic):
        output_var = _find_local_var_by_name(block, logic.output_var_name)
        text = (
            f"picdro({_expr_like_to_python(logic.bool_expr, identifier_map)}, "
            f"{_expr_like_to_python(logic.pickup_delay_expr, identifier_map)}, "
            f"{_expr_like_to_python(logic.drop_delay_expr, identifier_map)}, output={identifier_map[output_var.uid]})"
        )
        if logic.name != "" and logic.name != logic.output_var_name:
            text = text[:-1] + f", name={repr(logic.name)})"
        return text

    if isinstance(logic, ResetOnRisingEdgeLogic):
        target_var = _find_local_var_by_name(block, logic.target_var_name)
        default_name = f"{logic.target_var_name}_reset"
        text = (
            f"reset({identifier_map[target_var.uid]}, "
            f"{_expr_like_to_python(logic.reset_expr, identifier_map)}, "
            f"{_expr_like_to_python(logic.value_expr, identifier_map)})"
        )
        if logic.name != "" and logic.name != default_name:
            text = text[:-1] + f", name={repr(logic.name)})"
        return text

    raise TypeError(f"Unsupported procedural logic export type: {type(logic).__name__}")


def _emit_block_code(
    block: Block,
    identifier_map: Dict[int, str],
    block_var_name: str,
    lines: List[str],
    child_ref_names: Dict[int, str],
) -> None:
    lines.append(f"    {block_var_name} = Block(")
    if block.state_eqs:
        lines.append("        state_eqs=[")
        for eq in block.state_eqs:
            lines.append(f"            {_expr_to_python(eq, identifier_map)},")
        lines.append("        ],")
        lines.append("        state_vars=[" + ", ".join(identifier_map[v.uid] for v in block.state_vars) + "],")
    if block.algebraic_eqs:
        lines.append("        algebraic_eqs=[")
        for eq in block.algebraic_eqs:
            lines.append(f"            {_expr_to_python(eq, identifier_map)},")
        lines.append("        ],")
        lines.append("        algebraic_vars=[" + ", ".join(identifier_map[v.uid] for v in block.algebraic_vars) + "],")
    if block.children:
        lines.append("        children=[" + ", ".join(child_ref_names[id(child)] for child in block.children) + "],")
    if block.in_vars:
        lines.append("        in_vars=[" + ", ".join(identifier_map[v.uid] for v in block.in_vars) + "],")
    if block.out_vars:
        lines.append("        out_vars=[" + ", ".join(identifier_map[v.uid] for v in block.out_vars) + "],")
    lines.append(f"        name={repr(block.name)}")
    lines.append("    )")

    if block.diff_vars:
        lines.append(f"    {block_var_name}.diff_vars = [" + ", ".join(identifier_map[v.uid] for v in block.diff_vars) + "]")

    if block.event_dict:
        lines.append(f"    # --- Parameter Values ---")
        lines.append(f"    {block_var_name}.event_dict = {{")
        for key, value in block.event_dict.items():
            lines.append(f"        {identifier_map[key.uid]}: {_const_or_expr_to_python(value, identifier_map)},")
        lines.append("    }")

    if block.mode_dict:
        lines.append(f"    # --- Retained Runtime Modes ---")
        lines.append(f"    {block_var_name}.mode_dict = {{")
        for key, value in block.mode_dict.items():
            lines.append(f"        {identifier_map[key.uid]}: {_const_or_expr_to_python(value, identifier_map)},")
        lines.append("    }")

    if block.init_eqs:
        lines.append(f"    # --- Initial Equations and Guesses ---")
        lines.append(f"    {block_var_name}.init_eqs = {{")
        for key, value in block.init_eqs.items():
            lines.append(f"        {identifier_map[key.uid]}: {_const_or_expr_to_python(value, identifier_map)},")
        lines.append("    }")

    if block.diff_init_eqs:
        lines.append(f"    # --- Differential Initial Equations ---")
        lines.append(f"    {block_var_name}.diff_init_eqs = {{")
        for key, value in block.diff_init_eqs.items():
            lines.append(f"        {identifier_map[key.uid]}: {_const_or_expr_to_python(value, identifier_map)},")
        lines.append("    }")

    if block.procedural_logic:
        lines.append(f"    {block_var_name}.procedural_logic = [")
        for logic in block.procedural_logic:
            lines.append(f"        {_procedural_logic_entry_to_python(logic, block, identifier_map)},")
        lines.append("    ]")


def _emit_template_style_module(
    result: DgsRootBlockResult,
    subgraph: DgsBlockSubgraphResult,
    dgs_path: str,
    template_name: str | None = None,
) -> str:
    block = subgraph.view_block
    identifier_map = _make_identifier_map(block)
    resolved_template_name = template_name if template_name is not None else subgraph.selected_block.blkdef.loc_name
    func_base_name = _safe_name(resolved_template_name).lower()
    has_procedural_logic = any(len(item.procedural_logic) > 0 for item in _iter_blocks_recursive(block))
    procedural_import_names = _procedural_logic_import_names(block)

    vars_out: Dict[int, Var] = dict()
    consts_out: Dict[int, Const] = dict()
    _collect_block_vars_recursive(block, vars_out, consts_out)

    all_vars = list(vars_out.values())
    state_uids = {v.uid for b in _iter_blocks_recursive(block) for v in b.state_vars}
    diff_uids = {v.uid for b in _iter_blocks_recursive(block) for v in b.diff_vars}
    param_uids = {k.uid for b in _iter_blocks_recursive(block) for k in b.event_dict.keys()} | {k.uid for b in _iter_blocks_recursive(block) for k in b.parameters.keys()}

    state_vars = [v for v in all_vars if v.uid in state_uids and v.uid not in diff_uids]
    diff_vars = [v for v in all_vars if v.uid in diff_uids]
    param_vars = [v for v in all_vars if v.uid in param_uids and v.uid not in diff_uids]
    algebraic_vars = [
        v for v in all_vars
        if v.uid not in state_uids and v.uid not in diff_uids and v.uid not in param_uids
    ]

    lines: List[str] = list()
    lines.append("# --- AUTO-GENERATED EMT TEMPLATE FROM DGS ---")
    lines.append(f"# Source: {dgs_path}")
    lines.append("")
    lines.append("from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory")
    lines.append("from VeraGridEngine.Utils.Symbolic import symbolic as sym")
    lines.append("from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate")
    if isinstance(subgraph, DgsGraphicTreeResult) and len(subgraph.connections) > 0:
        lines.append("from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block")
    else:
        lines.append("from VeraGridEngine.Utils.Symbolic.block import Block")
    if has_procedural_logic:
        lines.append("from VeraGridEngine.Utils.procedural_logic import " + ", ".join(procedural_import_names))
    lines.append("from VeraGridEngine.enumerations import DeviceType")
    lines.append("")
    lines.append(f"def get_{func_base_name}_emt_template(vf: VarFactory, name: str = {repr(resolved_template_name)}) -> EmtModelTemplate:")
    lines.append("    templ = EmtModelTemplate()")
    lines.append("    templ.tpe = DeviceType.NoDevice")
    lines.append("    templ.name = name")
    lines.append("")
    lines.append("    # --- Parameters ---")
    for var in sorted(param_vars, key=lambda item: item.name):
        lines.append(f"    {identifier_map[var.uid]} = vf.add_var({repr(var.name + '_')} + name)")
    lines.append("")
    lines.append("    # --- State Variables ---")
    for var in sorted(state_vars, key=lambda item: item.name):
        lines.append(f"    {identifier_map[var.uid]} = vf.add_var({repr(var.name + '_')} + name)")
    lines.append("")
    lines.append("    # --- Algebraic / Shared Variables ---")
    for var in sorted(algebraic_vars, key=lambda item: item.name):
        lines.append(f"    {identifier_map[var.uid]} = vf.add_var({repr(var.name + '_')} + name)")
    lines.append("")
    lines.append("    # --- Derivative Variables ---")
    for var in sorted(diff_vars, key=lambda item: item.name):
        base_name = identifier_map[var.base_var.uid]
        lines.append(f"    {identifier_map[var.uid]} = vf.add_diff_var({repr(var.name + '_')} + name, base_var={base_name})")
    lines.append("")
    lines.append("    # --- Block Assembly ---")
    if isinstance(subgraph, DgsGraphicTreeResult):
        child_ref_names_by_node: Dict[str, str] = {
            node_id: f"{_safe_name(block.children[idx].name)}_{idx}"
            for idx, node_id in enumerate(subgraph.child_node_ids)
        }
    else:
        child_ref_names_by_node = dict()
    child_ref_names: Dict[int, str] = {
        id(child): child_ref_names_by_node.get(getattr(subgraph, 'child_node_ids', [])[idx], f"{_safe_name(child.name)}_{idx}")
        if isinstance(subgraph, DgsGraphicTreeResult) else f"{_safe_name(child.name)}_{idx}"
        for idx, child in enumerate(block.children)
    }
    for child in block.children:
        _emit_block_code(child, identifier_map, child_ref_names[id(child)], lines, child_ref_names)
        lines.append("")
    if isinstance(subgraph, DgsGraphicTreeResult) and len(subgraph.connections) > 0:
        lines.append("    # --- Graphical Connections (resolved from From/To) ---")
        for item in subgraph.connections:
            consumer_ref = child_ref_names_by_node[item.consumer_node_id]
            if item.source_kind == "block_output" and item.source_node_id is not None and item.source_output_index is not None and item.consumer_input_index is not None:
                producer_ref = child_ref_names_by_node[item.source_node_id]
                lines.append(
                    f"    {consumer_ref}.connect([{consumer_ref}.in_vars[{item.consumer_input_index}]], "
                    f"[{producer_ref}.out_vars[{item.source_output_index}]])"
                )
            elif item.source_kind == "root_input" and item.source_root_name is not None and item.consumer_input_index is not None:
                lines.append(
                    f"    {consumer_ref}.connect([{consumer_ref}.in_vars[{item.consumer_input_index}]], "
                    f"[{identifier_map[find_name_in_block(item.source_root_name, block).uid]}])"
                )
        lines.append("")
    _emit_block_code(block, identifier_map, "templ.block", lines, child_ref_names)
    lines.append("    templ.block.name = name")
    lines.append("")
    lines.append("    return templ")
    lines.append("")
    lines.append("def get_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:")
    lines.append(f"    return get_{func_base_name}_emt_template(vf=vf, name={repr(resolved_template_name)} if name is None else name)")

    return "\n".join(lines) + "\n"


def _emit_tree_style_module(
    result: DgsRootBlockResult,
    subgraph: DgsBlockSubgraphResult,
    dgs_path: str,
) -> str:
    block_data_repr = pprint.pformat(subgraph.view_block.to_dict(), width=120, sort_dicts=False)
    graph_repr = pprint.pformat(_graph_to_serializable(subgraph.dependency_graph), width=120, sort_dicts=False)
    upstream_repr = pprint.pformat(_graph_to_serializable(subgraph.upstream), width=120, sort_dicts=False)
    downstream_repr = pprint.pformat(_graph_to_serializable(subgraph.downstream), width=120, sort_dicts=False)
    metadata_repr = pprint.pformat({
        "dgs_path": str(dgs_path),
        "root_element_name": result.root_element.loc_name,
        "root_element_typ_id": result.root_element.typ_id,
        "root_blkdef_id": result.root_blkdef.blkdef.ID,
        "root_blkdef_name": result.root_blkdef.blkdef.loc_name,
        "selected_block_id": subgraph.selected_block.blkdef.ID,
        "selected_block_name": subgraph.selected_block.blkdef.loc_name,
        "selected_inputs": subgraph.selected_block.blkdef.inputs,
        "selected_outputs": subgraph.selected_block.blkdef.outputs,
        "selected_states": subgraph.selected_block.blkdef.states,
        "selected_params": subgraph.selected_block.blkdef.params,
        "unsupported_lines": subgraph.selected_block.unsupported_lines,
        "child_block_names": sorted(child.name for child in subgraph.view_block.children),
        "node_ids": sorted(subgraph.node_ids),
    }, width=120, sort_dicts=False)

    return f'''# Auto-generated DGS block tree export.
# Source: {dgs_path}

from VeraGridEngine.Utils.Symbolic.block import Block


BLOCK_DATA = {block_data_repr}

DEPENDENCY_GRAPH = {graph_repr}

UPSTREAM_GRAPH = {upstream_repr}

DOWNSTREAM_GRAPH = {downstream_repr}

METADATA = {metadata_repr}


def get_block() -> Block:
    return Block.parse(BLOCK_DATA)


def get_dependency_graph() -> dict:
    return DEPENDENCY_GRAPH


def get_upstream_graph() -> dict:
    return UPSTREAM_GRAPH


def get_downstream_graph() -> dict:
    return DOWNSTREAM_GRAPH


def get_metadata() -> dict:
    return METADATA
'''


def _clone_const_with_factory(value: Const | Expr, const_factory: callable) -> Const | Expr:
    if isinstance(value, Const):
        return const_factory(value=value.value, name=value.name)
    return value


def _collect_block_vars_recursive(block: Block, vars_out: Dict[int, Var], consts_out: Dict[int, Const]) -> None:
    var_lists = [block.state_vars, block.algebraic_vars, block.diff_vars, block.in_vars, block.out_vars]
    for var_list in var_lists:
        for var in var_list:
            vars_out[var.uid] = var

    dict_like = [block.event_dict, block.mode_dict, block.init_eqs, block.diff_init_eqs, block.parameters, block.init_values]
    for mapping in dict_like:
        for key, value in mapping.items():
            if isinstance(key, Var):
                vars_out[key.uid] = key
            if isinstance(value, Var):
                vars_out[value.uid] = value
            if isinstance(value, Const):
                consts_out[value.uid] = value
            if isinstance(value, Expr):
                for var in value.get_vars():
                    vars_out[var.uid] = var

    expr_lists = [block.state_eqs, block.algebraic_eqs, block.differential_eqs]
    for expr_list in expr_lists:
        for expr in expr_list:
            if isinstance(expr, Expr):
                for var in expr.get_vars():
                    vars_out[var.uid] = var

    for child in block.children:
        _collect_block_vars_recursive(child, vars_out, consts_out)


def materialize_block_with_var_factory(block_data: dict | Block, vf: Any, name: str) -> Block:
    """
    Recreate a serialized block using the target VarFactory and a runtime suffix.

    :param block_data: Serialized block dict or an already-built Block.
    :param vf: VarFactory-like object exposing add_var/add_diff_var/add_const.
    :param name: Runtime suffix used to make names unique.
    :return: Materialized Block.
    """
    source_block = Block.parse(block_data) if isinstance(block_data, dict) else block_data.copy()

    vars_out: Dict[int, Var] = dict()
    consts_out: Dict[int, Const] = dict()
    _collect_block_vars_recursive(source_block, vars_out, consts_out)

    var_mapping: Dict[Any, Expr] = dict()
    created_vars: Dict[int, Var] = dict()
    created_consts: Dict[int, Const] = dict()

    non_diff_vars = [var for var in vars_out.values() if var.base_var is None]
    diff_vars = [var for var in vars_out.values() if var.base_var is not None]

    for var in sorted(non_diff_vars, key=lambda item: item.name):
        new_var = vf.add_var(f"{var.name}_{name}")
        created_vars[var.uid] = new_var
        var_mapping[var] = new_var
        var_mapping[var.name] = new_var

    for var in sorted(diff_vars, key=lambda item: item.name):
        base_var = created_vars[var.base_var.uid]
        new_var = vf.add_diff_var(f"{var.name}_{name}", base_var=base_var)
        created_vars[var.uid] = new_var
        var_mapping[var] = new_var
        var_mapping[var.name] = new_var

    for const in consts_out.values():
        new_const = vf.add_const(value=const.value, name=const.name)
        created_consts[const.uid] = new_const
        var_mapping[const] = new_const

    def clone_block_recursive(block: Block) -> Block:
        cloned = Block(name=f"{block.name}_{name}")
        cloned.state_vars = [created_vars[v.uid] for v in block.state_vars]
        cloned.algebraic_vars = [created_vars[v.uid] for v in block.algebraic_vars]
        cloned.diff_vars = [created_vars[v.uid] for v in block.diff_vars]
        cloned.in_vars = [created_vars[v.uid] for v in block.in_vars]
        cloned.out_vars = [created_vars[v.uid] for v in block.out_vars]

        cloned.state_eqs = [expr.subs(var_mapping) for expr in block.state_eqs]
        cloned.algebraic_eqs = [expr.subs(var_mapping) for expr in block.algebraic_eqs]
        cloned.differential_eqs = [expr.subs(var_mapping) for expr in block.differential_eqs]

        cloned.event_dict = {created_vars[k.uid]: _clone_const_with_factory(v.subs(var_mapping) if isinstance(v, Expr) else v, vf.add_const) for k, v in block.event_dict.items()}
        cloned.mode_dict = {created_vars[k.uid]: (v.subs(var_mapping) if isinstance(v, Expr) else v) for k, v in block.mode_dict.items()}
        cloned.init_eqs = {created_vars[k.uid]: v.subs(var_mapping) for k, v in block.init_eqs.items()}
        cloned.diff_init_eqs = {created_vars[k.uid]: v.subs(var_mapping) for k, v in block.diff_init_eqs.items()}
        cloned.parameters = {created_vars[k.uid]: _clone_const_with_factory(v, vf.add_const) for k, v in block.parameters.items()}
        cloned.init_values = {created_vars[k.uid]: _clone_const_with_factory(v, vf.add_const) for k, v in block.init_values.items()}
        cloned.procedural_logic = clone_procedural_logic_entries(block.procedural_logic, var_mapping)
        cloned.children = [clone_block_recursive(child) for child in block.children]
        return cloned

    return clone_block_recursive(source_block)


def _build_symbol_table(
    blkdef: BlkDef,
    shared_signals: Dict[str, Var],
) -> Tuple[Dict[str, Var], List[Var], Dict[str, Var], Dict[str, Var], Dict[str, Var]]:
    symbol_table: Dict[str, Var] = dict()
    shared_names: Set[str] = set(blkdef.inputs + blkdef.outputs + blkdef.internals)

    for name in shared_names:
        if name not in shared_signals:
            shared_signals[name] = Var(name=name)
        symbol_table[name] = shared_signals[name]

    state_vars: List[Var] = list()
    state_var_map: Dict[str, Var] = dict()
    diff_var_map: Dict[str, Var] = dict()
    param_var_map: Dict[str, Var] = dict()

    for state_name in blkdef.states:
        state_var = Var(name=f"{blkdef.loc_name}__{state_name}")
        diff_var = Var(name=f"d_{blkdef.loc_name}__{state_name}", base_var=state_var)
        symbol_table[state_name] = state_var
        state_vars.append(state_var)
        state_var_map[state_name] = state_var
        diff_var_map[state_name] = diff_var

    for param_name in blkdef.params:
        param_var = Var(name=f"{blkdef.loc_name}__{param_name}")
        symbol_table[param_name] = param_var
        param_var_map[param_name] = param_var

    return symbol_table, state_vars, state_var_map, diff_var_map, param_var_map


def _parse_blkdef(blkdef: BlkDef, shared_signals: Dict[str, Var]) -> ParsedDgsBlockDefinition:
    symbol_table, state_vars, state_var_map, diff_var_map, _param_var_map = _build_symbol_table(blkdef, shared_signals)
    _predeclare_statement_lhs_symbols(blkdef, symbol_table)
    parser = DgsExpressionParser(symbol_table, block_name=blkdef.loc_name)

    state_rhs: Dict[str, Expr] = dict()
    algebraic_rhs: Dict[str, Expr] = dict()
    init_rhs: Dict[str, Expr] = dict()
    unsupported_lines: List[str] = list()
    signal_dependencies: Dict[str, Set[str]] = dict()

    for stmt in _split_equation_statements(blkdef.equations_raw):
        stmt_kind, lhs_hint = classify_dgs_statement(stmt)

        if stmt_kind == 'ignored':
            continue

        if stmt_kind == 'procedural':
            try:
                parser.parse_procedural_statement(stmt)
            except UnsupportedDgsExpression:
                unsupported_lines.append(stmt)
                continue

            signal_dependencies[stmt] = set()
            continue

        init_match = re.match(r'^(?P<kind>inc0?|inc)\((?P<lhs>[^\)]+)\)\s*=\s*(?P<rhs>.+)$', stmt)
        diff_match = re.match(r'^(?P<lhs>.+?)\.\s*=\s*(?P<rhs>.+)$', stmt)
        alg_match = re.match(r'^(?P<lhs>[^=]+?)\s*=\s*(?P<rhs>.+)$', stmt)

        if init_match is not None:
            init_kind = init_match.group('kind').strip()
            lhs_name = init_match.group('lhs').strip()
            rhs_text = init_match.group('rhs').strip()

            if lhs_name not in symbol_table:
                symbol_table[lhs_name] = Var(name=f"{blkdef.loc_name}__{lhs_name}")
                parser._replacement_map[_safe_name(lhs_name)] = lhs_name

            try:
                rhs_expr = parser.parse(rhs_text)
            except UnsupportedDgsExpression:
                unsupported_lines.append(stmt)
                continue

            if isinstance(rhs_expr, Comparison):
                rhs_expr = rhs_expr.to_expression()

            if init_kind == 'inc0' and lhs_name in init_rhs:
                continue

            init_rhs[lhs_name] = rhs_expr
            signal_dependencies[f"{init_kind}({lhs_name})"] = {v.name for v in rhs_expr.get_vars()}
        elif diff_match is not None:
            lhs_name = diff_match.group('lhs').strip()
            rhs_text = diff_match.group('rhs').strip()

            if lhs_name not in symbol_table:
                symbol_table[lhs_name] = Var(name=f"{blkdef.loc_name}__{lhs_name}")
                parser._replacement_map[_safe_name(lhs_name)] = lhs_name

            try:
                rhs_expr = parser.parse(rhs_text)
            except UnsupportedDgsExpression:
                unsupported_lines.append(stmt)
                continue

            if not isinstance(rhs_expr, Expr):
                unsupported_lines.append(stmt)
                continue

            state_rhs[lhs_name] = rhs_expr
            signal_dependencies[lhs_name] = {v.name for v in rhs_expr.get_vars()}
        elif alg_match is not None:
            lhs_name = alg_match.group('lhs').strip()
            rhs_text = alg_match.group('rhs').strip()

            if lhs_name not in symbol_table:
                symbol_table[lhs_name] = Var(name=f"{blkdef.loc_name}__{lhs_name}")
                parser._replacement_map[_safe_name(lhs_name)] = lhs_name

            try:
                rhs_expr = parser.parse(rhs_text)
            except UnsupportedDgsExpression:
                unsupported_lines.append(stmt)
                continue

            if isinstance(rhs_expr, Comparison):
                rhs_expr = rhs_expr.to_expression()

            algebraic_rhs[lhs_name] = rhs_expr
            signal_dependencies[lhs_name] = {v.name for v in rhs_expr.get_vars()}
        else:
            unsupported_lines.append(stmt)

    return ParsedDgsBlockDefinition(
        blkdef=blkdef,
        symbol_table=dict(symbol_table),
        state_rhs=state_rhs,
        algebraic_rhs=algebraic_rhs,
        init_rhs=init_rhs,
        mode_dict=dict(parser.procedural_mode_defaults),
        procedural_logic=list(parser.procedural_logic_entries),
        unsupported_lines=unsupported_lines,
        signal_dependencies=signal_dependencies,
    )


def _score_root_candidate(blkdef: ParsedDgsBlockDefinition) -> Tuple[int, int, int, int, int]:
    return (
        len(blkdef.blkdef.inputs),
        len(blkdef.blkdef.outputs),
        len(blkdef.blkdef.states),
        len(blkdef.algebraic_rhs) + len(blkdef.state_rhs),
        len(blkdef.blkdef.internals),
    )


def _select_root_element(circuit: DgsCircuit, parsed_blocks: Dict[str, ParsedDgsBlockDefinition], root_name: str | None, root_typ_id: str | None) -> Tuple[ElmComp, ParsedDgsBlockDefinition]:
    candidates: List[ElmComp] = list(circuit.elmcomps)
    if root_name is not None:
        candidates = [elm for elm in candidates if elm.loc_name == root_name]

    if root_typ_id is not None:
        candidates = [elm for elm in candidates if str(elm.typ_id).strip() == str(root_typ_id).strip()]

    if not candidates:
        raise ValueError("No matching ElmComp root candidate found in the DGS file")

    best_element: ElmComp | None = None
    best_block: ParsedDgsBlockDefinition | None = None
    best_score: Tuple[int, int, int, int, int] | None = None

    for elm in candidates:
        blk = parsed_blocks.get(str(elm.typ_id).strip())
        if blk is None:
            continue
        score = _score_root_candidate(blk)
        if best_score is None or score > best_score:
            best_element = elm
            best_block = blk
            best_score = score

    if best_element is None or best_block is None:
        raise ValueError("No ElmComp candidate could be resolved to a parsed BlkDef")

    return best_element, best_block


def _collect_reachable_blocks(root_blkdef: ParsedDgsBlockDefinition, parsed_blocks: Dict[str, ParsedDgsBlockDefinition]) -> Dict[str, ParsedDgsBlockDefinition]:
    frontier: Set[str] = set(root_blkdef.blkdef.inputs + root_blkdef.blkdef.outputs + root_blkdef.blkdef.internals)
    reachable: Dict[str, ParsedDgsBlockDefinition] = dict()
    changed = True

    while changed:
        changed = False
        for block_id, parsed in parsed_blocks.items():
            if block_id == root_blkdef.blkdef.ID or block_id in reachable:
                continue
            io_names = set(parsed.blkdef.inputs + parsed.blkdef.outputs + parsed.blkdef.internals)
            if io_names & frontier:
                reachable[block_id] = parsed
                frontier |= io_names
                changed = True

    return reachable

def _collect_internal_candidate_blocks(
    selected_block: ParsedDgsBlockDefinition,
    parsed_blocks: Dict[str, ParsedDgsBlockDefinition],
) -> Dict[str, ParsedDgsBlockDefinition]:
    """
    Collect candidate internal blocks for a selected composite block using only
    signal-name overlap and dependency closure.

    :param selected_block: Selected composite parsed block.
    :param parsed_blocks: All parsed blocks.
    :return: Internal candidate blocks keyed by block identifier.
    """
    seed_signals: Set[str] = set()
    seed_signals |= set(selected_block.blkdef.inputs)
    seed_signals |= set(selected_block.blkdef.outputs)
    seed_signals |= set(selected_block.blkdef.internals)

    reachable: Dict[str, ParsedDgsBlockDefinition] = dict()
    frontier_signals: Set[str] = set(seed_signals)

    changed: bool = True
    while changed:
        changed = False

        for block_id, parsed in parsed_blocks.items():
            if block_id == selected_block.blkdef.ID:
                pass
            elif block_id in reachable:
                pass
            else:
                block_signals: Set[str] = set()
                block_signals |= set(parsed.blkdef.inputs)
                block_signals |= set(parsed.blkdef.outputs)
                block_signals |= set(parsed.blkdef.internals)

                if len(block_signals & frontier_signals) > 0:
                    reachable[block_id] = parsed
                    frontier_signals |= block_signals
                    changed = True
                else:
                    pass

    return reachable

def _score_internal_candidate(
    selected_block: ParsedDgsBlockDefinition,
    candidate_block: ParsedDgsBlockDefinition,
) -> int:
    """
    Score how likely a block is to belong to the internal structure of a selected block.

    :param selected_block: Selected composite block.
    :param candidate_block: Candidate internal block.
    :return: Integer score.
    """
    selected_inputs: Set[str] = set(selected_block.blkdef.inputs)
    selected_outputs: Set[str] = set(selected_block.blkdef.outputs)
    selected_internals: Set[str] = set(selected_block.blkdef.internals)

    candidate_inputs: Set[str] = set(candidate_block.blkdef.inputs)
    candidate_outputs: Set[str] = set(candidate_block.blkdef.outputs)
    candidate_internals: Set[str] = set(candidate_block.blkdef.internals)

    score: int = 0

    score += 4 * len(candidate_inputs & selected_inputs)
    score += 4 * len(candidate_outputs & selected_outputs)
    score += 3 * len(candidate_outputs & selected_internals)
    score += 3 * len(candidate_inputs & selected_internals)
    score += 2 * len(candidate_internals & selected_internals)
    score += 1 * len(candidate_internals & selected_inputs)
    score += 1 * len(candidate_internals & selected_outputs)

    return score

def _filter_internal_candidates(
    selected_block: ParsedDgsBlockDefinition,
    candidates: Dict[str, ParsedDgsBlockDefinition],
    min_score: int = 2,
) -> Dict[str, ParsedDgsBlockDefinition]:
    """
    Filter candidate internal blocks using signal-overlap scoring.

    :param selected_block: Selected composite block.
    :param candidates: Candidate blocks.
    :param min_score: Minimum score to keep.
    :return: Filtered candidate blocks.
    """
    filtered: Dict[str, ParsedDgsBlockDefinition] = dict()

    for block_id, parsed in candidates.items():
        score: int = _score_internal_candidate(selected_block, parsed)
        if score >= min_score:
            filtered[block_id] = parsed
        else:
            pass

    return filtered

def _parameter_values_by_type_id(entries: Iterable[ElmCompInstanceEntry]) -> Dict[str, Dict[str, Any]]:
    """
    Build a unique parameter lookup keyed by block-definition identifier.

    :param entries: Direct instance entries extracted from one ElmComp.
    :return: Parameter values keyed by BlkDef identifier when the type appears only once.
    """
    parameter_values_by_type: Dict[str, Dict[str, Any]] = dict()
    duplicated_type_ids: Set[str] = set()

    for entry in entries:
        # We only propagate values when one block type appears once inside the parent ElmComp.
        if entry.type_id is None or len(entry.parameter_values) == 0:
            pass
        else:
            if entry.type_id in parameter_values_by_type:
                duplicated_type_ids.add(entry.type_id)
            else:
                parameter_values_by_type[entry.type_id] = dict(entry.parameter_values)

    for type_id in duplicated_type_ids:
        parameter_values_by_type.pop(type_id, None)

    return parameter_values_by_type


def _build_block_from_parsed(
    parsed: ParsedDgsBlockDefinition,
    shared_signals: Dict[str, Var],
    parameter_values: Dict[str, Any] | None = None,
) -> Block:
    """
    Materialize one parsed DGS block into a runtime Block.

    :param parsed: Parsed DGS block definition.
    :param shared_signals: Shared signal table reused across sibling blocks.
    :param parameter_values: Optional instance values obtained from ElmDsl rows.
    :return: Runtime block ready to be composed or exported.
    """
    symbol_table, state_vars, _state_map, diff_var_map, param_var_map = _build_symbol_table(parsed.blkdef, shared_signals)

    for name, old_var in parsed.symbol_table.items():
        if name not in symbol_table:
            symbol_table[name] = Var(name=old_var.name)

    var_mapping: Dict[Any, Expr] = dict()
    for name, old_var in parsed.symbol_table.items():
        new_var = symbol_table.get(name, None)
        if new_var is not None:
            var_mapping[old_var] = new_var
            var_mapping[old_var.name] = new_var

    algebraic_pairs: List[Tuple[Var, Expr]] = list()
    used_alg_names: Set[str] = set()
    for lhs_name, rhs_expr in parsed.algebraic_rhs.items():
        if lhs_name in symbol_table:
            lhs_var = symbol_table[lhs_name]
        else:
            lhs_var = Var(name=f"{parsed.blkdef.loc_name}__{lhs_name}")
            symbol_table[lhs_name] = lhs_var

        old_lhs_var = parsed.symbol_table.get(lhs_name, None)
        if old_lhs_var is not None:
            var_mapping[old_lhs_var] = lhs_var
            var_mapping[old_lhs_var.name] = lhs_var

        algebraic_pairs.append((lhs_var, lhs_var - rhs_expr.subs(var_mapping)))
        used_alg_names.add(lhs_name)

    algebraic_vars: List[Var] = [pair[0] for pair in algebraic_pairs]
    algebraic_eqs: List[Expr] = [pair[1] for pair in algebraic_pairs]

    state_eqs: List[Expr] = list()
    effective_state_vars: List[Var] = list()
    effective_diff_vars: List[Var] = list()
    for state_name in parsed.blkdef.states:
        if state_name in parsed.state_rhs:
            effective_state_vars.append(symbol_table[state_name])
            effective_diff_vars.append(diff_var_map[state_name])
            state_eqs.append(parsed.state_rhs[state_name].subs(var_mapping))

    # The BlkDef stores the parameter names, while the ElmDsl instance stores the concrete numbers.
    resolved_parameter_values: Dict[str, Any] = dict(parameter_values or {})
    event_dict: Dict[Var, Const] = {
        param_var: Const(resolved_parameter_values.get(param_name, None), name=param_name)
        for param_name, param_var in param_var_map.items()
    }

    init_eqs: Dict[Var, Expr] = dict()
    for lhs_name, rhs_expr in parsed.init_rhs.items():
        lhs_var: Var
        if lhs_name in symbol_table:
            lhs_var = symbol_table[lhs_name]
        else:
            lhs_var = Var(name=f"{parsed.blkdef.loc_name}__{lhs_name}")
            symbol_table[lhs_name] = lhs_var

        old_lhs_var = parsed.symbol_table.get(lhs_name, None)
        if old_lhs_var is not None:
            var_mapping[old_lhs_var] = lhs_var
            var_mapping[old_lhs_var.name] = lhs_var

        init_eqs[lhs_var] = rhs_expr.subs(var_mapping)

    mode_dict: Dict[Var, Expr | Const] = dict()
    for mode_var, rhs_expr in parsed.mode_dict.items():
        mapped_var = var_mapping.get(mode_var, None)
        if not isinstance(mapped_var, Var):
            mapped_var = symbol_table.get(mode_var.name, None)
        if not isinstance(mapped_var, Var):
            mapped_var = Var(name=mode_var.name)
            symbol_table[mode_var.name] = mapped_var
        mode_dict[mapped_var] = rhs_expr.subs(var_mapping) if isinstance(rhs_expr, Expr) else rhs_expr

    procedural_logic = clone_procedural_logic_entries(parsed.procedural_logic, var_mapping)

    return Block(
        name=parsed.blkdef.loc_name,
        state_vars=effective_state_vars,
        state_eqs=state_eqs,
        diff_vars=effective_diff_vars,
        algebraic_vars=algebraic_vars,
        algebraic_eqs=algebraic_eqs,
        in_vars=[shared_signals[name] for name in parsed.blkdef.inputs if name in shared_signals],
        out_vars=[shared_signals[name] for name in parsed.blkdef.outputs if name in shared_signals],
        event_dict=event_dict,
        mode_dict=mode_dict,
        init_eqs=init_eqs,
        procedural_logic=procedural_logic,
    )


def _build_dependency_graph(parsed_blocks: Dict[str, ParsedDgsBlockDefinition]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
    producer_map: Dict[str, Set[str]] = dict()
    consumer_map: Dict[str, Set[str]] = dict()

    for block_id, parsed in parsed_blocks.items():
        produced_names = set(parsed.blkdef.outputs) | set(parsed.algebraic_rhs.keys()) | set(parsed.state_rhs.keys())
        for name in produced_names:
            producer_map.setdefault(name, set()).add(block_id)

        for dep_names in parsed.signal_dependencies.values():
            for name in dep_names:
                consumer_map.setdefault(name, set()).add(block_id)

    dependency_graph: Dict[str, Set[str]] = {block_id: set() for block_id in parsed_blocks.keys()}

    for signal_name, producers in producer_map.items():
        consumers = consumer_map.get(signal_name, set())
        for producer in producers:
            for consumer in consumers:
                if producer != consumer:
                    dependency_graph[producer].add(consumer)

    return dependency_graph, producer_map, consumer_map


def dgs_to_root_block(path: str, root_name: str = "Grid Forming Converter", root_typ_id: str | None = None) -> DgsRootBlockResult:
    circuit = DgsCircuit()
    circuit.parse_dgs(path)

    shared_signals: Dict[str, Var] = dict()
    parsed_blocks: Dict[str, ParsedDgsBlockDefinition] = {
        blk.ID: _parse_blkdef(blk, shared_signals)
        for blk in circuit.blkdefs
    }

    root_element, root_blkdef = _select_root_element(circuit, parsed_blocks, root_name=root_name, root_typ_id=root_typ_id)
    reachable_blocks = _collect_reachable_blocks(root_blkdef, parsed_blocks)
    parameter_values_by_type_id = _parameter_values_by_type_id(extract_elmcomp_direct_instances(circuit, root_element))

    child_blocks: List[Block] = [
        _build_block_from_parsed(parsed, shared_signals, parameter_values=parameter_values_by_type_id.get(parsed.blkdef.ID, None))
        for _, parsed in sorted(reachable_blocks.items(), key=lambda item: item[1].blkdef.loc_name)
    ]

    root_block = Block(
        name=root_element.loc_name,
        children=child_blocks,
        in_vars=[shared_signals[name] for name in root_blkdef.blkdef.inputs if name in shared_signals],
        out_vars=[shared_signals[name] for name in root_blkdef.blkdef.outputs if name in shared_signals],
        algebraic_vars=[shared_signals[name] for name in root_blkdef.blkdef.internals if name in shared_signals],
    )

    combined_blocks: Dict[str, ParsedDgsBlockDefinition] = {root_blkdef.blkdef.ID: root_blkdef, **reachable_blocks}
    dependency_graph, producer_map, consumer_map = _build_dependency_graph(combined_blocks)

    return DgsRootBlockResult(
        root_block=root_block,
        root_blkdef=root_blkdef,
        root_element=root_element,
        parsed_blocks=combined_blocks,
        dependency_graph=dependency_graph,
        producer_map=producer_map,
        consumer_map=consumer_map,
    )


def _build_direct_root_elmcomp_block(
    circuit: DgsCircuit,
    result: DgsRootBlockResult,
) -> Block:
    """
    Build a root ElmComp block using only its direct DGS child instances.

    :param circuit: Parsed DGS circuit.
    :param result: Root selection result.
    :return: Root runtime block with direct DSL children only.
    """
    shared_signals: Dict[str, Var] = dict()
    root_signal_names: List[str] = list()
    for root_var in result.root_block.in_vars:
        root_signal_names.append(root_var.name)
    for root_var in result.root_block.out_vars:
        root_signal_names.append(root_var.name)
    for root_var in result.root_block.algebraic_vars:
        root_signal_names.append(root_var.name)

    for signal_name in root_signal_names:
        if signal_name not in shared_signals:
            shared_signals[signal_name] = Var(name=signal_name)
        else:
            pass

    child_blocks: List[Block] = list()
    direct_entries = extract_elmcomp_direct_instances(circuit, result.root_element)
    for entry in direct_entries:
        if entry.type_id is None:
            pass
        else:
            parsed_block = result.parsed_blocks.get(entry.type_id, None)
            if parsed_block is None:
                pass
            else:
                # Each direct ElmDsl instance provides the concrete parameter constants for its block type.
                child_block = _build_block_from_parsed(
                    parsed_block,
                    shared_signals,
                    parameter_values=entry.parameter_values,
                )
                child_blocks.append(child_block)

    return Block(
        name=result.root_element.loc_name,
        children=child_blocks,
        in_vars=[shared_signals[var.name] for var in result.root_block.in_vars if var.name in shared_signals],
        out_vars=[shared_signals[var.name] for var in result.root_block.out_vars if var.name in shared_signals],
        algebraic_vars=[shared_signals[var.name] for var in result.root_block.algebraic_vars if var.name in shared_signals],
    )

def _build_dgs_element_index(circuit: DgsCircuit) -> dict[str, object]:
    """
    Build a flat DGS object index by identifier.

    :param circuit: Parsed DGS circuit.
    :return: Dictionary from identifier to object.
    """
    element_by_id: dict[str, object] = dict()

    for elmcomp in circuit.elmcomps:
        element_by_id[elmcomp.ID] = elmcomp

    for elmdsl in circuit.elmdsls:
        element_by_id[elmdsl.ID] = elmdsl

    for blkdef in circuit.blkdefs:
        element_by_id[blkdef.ID] = blkdef

    return element_by_id


def _build_blkdef_index(circuit: DgsCircuit) -> dict[str, BlkDef]:
    """
    Build a BlkDef index by identifier.

    :param circuit: Parsed DGS circuit.
    :return: Dictionary from BlkDef identifier to BlkDef.
    """
    blkdef_by_id: dict[str, BlkDef] = dict()

    for blkdef in circuit.blkdefs:
        blkdef_by_id[blkdef.ID] = blkdef

    return blkdef_by_id


def _build_graphic_node_index(circuit: DgsCircuit) -> dict[str, object]:
    """
    Build index of graphical-model DGS nodes by identifier.

    :param circuit: Parsed DGS circuit.
    :return: Mapping from node id to graphic object.
    """
    node_by_id: dict[str, object] = dict()

    for obj in circuit.blkdefs:
        node_by_id[obj.ID] = obj
    for obj in circuit.blkrefs:
        node_by_id[obj.ID] = obj
    for obj in circuit.blkslots:
        node_by_id[obj.ID] = obj
    for obj in circuit.blkfroms:
        node_by_id[obj.ID] = obj
    for obj in circuit.blkgotos:
        node_by_id[obj.ID] = obj
    for obj in circuit.blksums:
        node_by_id[obj.ID] = obj

    return node_by_id


def build_graphic_node_index(circuit: DgsCircuit) -> Dict[str, object]:
    """
    Build a public index of graphical DGS nodes by identifier.

    :param circuit: Parsed DGS circuit.
    :return: Mapping from node id to graphical object.
    """
    return _build_graphic_node_index(circuit)


def _build_blksig_adjacency(circuit: DgsCircuit) -> dict[str, set[str]]:
    """
    Build undirected adjacency graph over graphical nodes connected by BlkSig.

    :param circuit: Parsed DGS circuit.
    :return: Undirected adjacency map.
    """
    adjacency: dict[str, set[str]] = dict()

    for sig in circuit.blksigs:
        src = sig.pnodfrom.strip() if isinstance(sig.pnodfrom, str) else ''
        dst = sig.pnodto.strip() if isinstance(sig.pnodto, str) else ''

        if src == '' or dst == '':
            continue

        adjacency.setdefault(src, set()).add(dst)
        adjacency.setdefault(dst, set()).add(src)

    return adjacency


def _graphic_connected_component(adjacency: dict[str, set[str]], root_id: str) -> set[str]:
    """
    Return the connected component of a root graphical node.

    :param adjacency: Undirected graphical adjacency.
    :param root_id: Root node identifier.
    :return: Connected component node ids.
    """
    visited: set[str] = set()
    frontier: list[str] = [root_id]

    while frontier:
        node_id = frontier.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        for nxt in adjacency.get(node_id, set()):
            if nxt not in visited:
                frontier.append(nxt)

    return visited


def _graphic_node_label(node: object) -> str:
    """
    Return a human-readable label for a graphical node.

    :param node: DGS graphical node.
    :return: Display label.
    """
    if isinstance(node, BlkRef):
        return node.cdisName if node.cdisName != '' else node.typ_id
    if isinstance(node, BlkSum):
        return node.loc_name
    if isinstance(node, BlkFrom):
        return node.loc_name
    if isinstance(node, BlkGoto):
        return node.loc_name
    if isinstance(node, BlkSlot):
        return node.loc_name
    if isinstance(node, BlkDef):
        return node.loc_name
    return str(node)


def _graphic_node_kind(node: object) -> str:
    """
    Return a short kind label for a graphical node.

    :param node: DGS graphical node.
    :return: Kind label.
    """
    if isinstance(node, BlkRef):
        return 'BlkRef'
    if isinstance(node, BlkSum):
        return 'BlkSum'
    if isinstance(node, BlkFrom):
        return 'BlkFrom'
    if isinstance(node, BlkGoto):
        return 'BlkGoto'
    if isinstance(node, BlkSlot):
        return 'BlkSlot'
    if isinstance(node, BlkDef):
        return 'BlkDef'
    return type(node).__name__


def _graphic_node_to_block(
    node_id: str,
    node: object,
    parsed_blocks: Dict[str, ParsedDgsBlockDefinition],
) -> Block:
    """
    Convert one graphical node into a lightweight Block for visualization.

    :param node_id: Node identifier.
    :param node: Graphical node object.
    :param parsed_blocks: Parsed block definitions.
    :return: Visualization block.
    """
    if isinstance(node, BlkRef):
        parsed = parsed_blocks.get(node.typ_id)
        if parsed is not None:
            blk = _build_block_from_parsed(parsed, dict())
            blk.name = _graphic_node_label(node)
            return blk

    blk = Block(name=_graphic_node_label(node))
    return blk


def _build_graphic_node_signal_map(circuit: DgsCircuit) -> dict[str, set[str]]:
    """
    Collect normalized signal labels attached to each graphical node through BlkSig and BlkFrom definitions.

    :param circuit: Parsed DGS circuit.
    :return: Mapping from node id to normalized signal labels.
    """
    node_signals: dict[str, set[str]] = dict()

    for sig in circuit.blksigs:
        sig_name = _normalize_graph_signal_name(sig.loc_name)
        if sig_name == '':
            continue

        if isinstance(sig.pnodfrom, str) and sig.pnodfrom.strip() != '':
            node_signals.setdefault(sig.pnodfrom.strip(), set()).add(sig_name)

        if isinstance(sig.pnodto, str) and sig.pnodto.strip() != '':
            node_signals.setdefault(sig.pnodto.strip(), set()).add(sig_name)

    for blk_from in circuit.blkfroms:
        for sig_name in blk_from.signals:
            clean = _normalize_graph_signal_name(sig_name)
            if clean != '':
                node_signals.setdefault(blk_from.ID, set()).add(clean)

    return node_signals


def _build_graph_signal_alias_map(
    node_ids: Set[str],
    node_by_id: Dict[str, object],
    node_signals: Dict[str, Set[str]],
) -> Dict[str, Set[str]]:
    parent: Dict[str, str] = dict()

    def _find(name: str) -> str:
        root = parent.setdefault(name, name)
        while root != parent[root]:
            parent[root] = parent[parent[root]]
            root = parent[root]
        return root

    def _union(a: str, b: str) -> None:
        ra = _find(a)
        rb = _find(b)
        if ra != rb:
            parent[rb] = ra

    for node_id in node_ids:
        node = node_by_id.get(node_id)
        if not isinstance(node, BlkFrom):
            continue

        aliases = sorted(node_signals.get(node_id, set()))
        if len(aliases) < 2:
            continue

        head = aliases[0]
        for alias in aliases[1:]:
            _union(head, alias)

    groups: Dict[str, Set[str]] = dict()
    for signal_names in node_signals.values():
        for sig in signal_names:
            root = _find(sig)
            groups.setdefault(root, set()).add(sig)

    alias_map: Dict[str, Set[str]] = dict()
    for group in groups.values():
        for sig in group:
            alias_map[sig] = set(group)

    return alias_map


def _build_augmented_graphical_adjacency(
    node_ids: Set[str],
    adjacency: Dict[str, Set[str]],
    node_by_id: Dict[str, object],
    node_signals: Dict[str, Set[str]],
    alias_map: Dict[str, Set[str]],
) -> Dict[str, Set[str]]:
    expanded: Dict[str, Set[str]] = {node_id: set(neigh for neigh in adjacency.get(node_id, set()) if neigh in node_ids) for node_id in node_ids}

    routing_nodes: List[str] = [
        node_id for node_id in node_ids
        if isinstance(node_by_id.get(node_id), (BlkFrom, BlkGoto))
    ]

    for idx, left_id in enumerate(routing_nodes):
        left_aliases: Set[str] = set()
        for sig in node_signals.get(left_id, set()):
            left_aliases |= alias_map.get(sig, {sig})

        if len(left_aliases) == 0:
            continue

        for right_id in routing_nodes[idx + 1:]:
            right_aliases: Set[str] = set()
            for sig in node_signals.get(right_id, set()):
                right_aliases |= alias_map.get(sig, {sig})

            if len(left_aliases & right_aliases) == 0:
                continue

            expanded.setdefault(left_id, set()).add(right_id)
            expanded.setdefault(right_id, set()).add(left_id)

    return expanded


def _graph_distance(adjacency: Dict[str, Set[str]], start_node: str, target_node: str) -> int:
    if start_node == target_node:
        return 0

    visited: Set[str] = set()
    frontier: List[Tuple[str, int]] = [(start_node, 0)]

    while frontier:
        node_id, dist = frontier.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)

        for nxt in adjacency.get(node_id, set()):
            if nxt == target_node:
                return dist + 1
            if nxt not in visited:
                frontier.append((nxt, dist + 1))

    return 10**9


def _node_signal_aliases(node_id: str, node_signals: Dict[str, Set[str]], alias_map: Dict[str, Set[str]]) -> Set[str]:
    aliases: Set[str] = set()
    for sig in node_signals.get(node_id, set()):
        aliases |= alias_map.get(sig, {sig})
    return aliases


def _resolve_graphic_block_connections(
    selected_block: ParsedDgsBlockDefinition,
    child_node_ids: List[str],
    child_blocks: Dict[str, Block],
    child_input_specs: Dict[str, List[str]],
    child_output_specs: Dict[str, List[str]],
    adjacency: Dict[str, Set[str]],
    node_by_id: Dict[str, object],
    node_signals: Dict[str, Set[str]],
    alias_map: Dict[str, Set[str]],
    root_runtime_block: Block,
) -> Tuple[List[GraphicConnectionInstruction], List[Var]]:
    producer_entries: List[Tuple[str, str, Var]] = list()
    root_inputs = {var.name: var for var in root_runtime_block.in_vars}
    root_signal_vars = {var.name: var for var in (root_runtime_block.in_vars + root_runtime_block.out_vars + root_runtime_block.algebraic_vars + root_runtime_block.state_vars)}

    for node_id in child_node_ids:
        block = child_blocks[node_id]
        for output_index, output_name in enumerate(child_output_specs.get(node_id, list())):
            if output_index < len(block.out_vars):
                producer_entries.append((node_id, output_name, block.out_vars[output_index]))

    connections: List[GraphicConnectionInstruction] = list()

    for consumer_node_id in child_node_ids:
        for input_index, input_name in enumerate(child_input_specs.get(consumer_node_id, list())):
            input_aliases = alias_map.get(input_name, {input_name})
            candidates: List[Tuple[int, int, str, str]] = list()

            for producer_node_id, output_name, _out_var in producer_entries:
                if producer_node_id == consumer_node_id:
                    continue
                if len(input_aliases & alias_map.get(output_name, {output_name})) == 0:
                    continue
                distance = _graph_distance(adjacency, consumer_node_id, producer_node_id)
                exact_score = 0 if output_name == input_name else 1
                candidates.append((exact_score, distance, producer_node_id, output_name))

            if len(candidates) > 0:
                candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
                best = candidates[0]
                connections.append(
                    GraphicConnectionInstruction(
                        consumer_node_id=consumer_node_id,
                        consumer_input_name=input_name,
                        source_kind="block_output",
                        consumer_input_index=input_index,
                        source_node_id=best[2],
                        source_output_name=best[3],
                        source_output_index=child_output_specs.get(best[2], list()).index(best[3]),
                    )
                )
                continue

            root_candidates = [name for name in root_signal_vars.keys() if len(alias_map.get(name, {name}) & input_aliases) > 0]
            if len(root_candidates) > 0:
                root_candidates.sort(key=lambda name: (0 if name == input_name else 1, name))
                connections.append(
                    GraphicConnectionInstruction(
                        consumer_node_id=consumer_node_id,
                        consumer_input_name=input_name,
                        source_kind="root_input",
                        consumer_input_index=input_index,
                        source_root_name=root_candidates[0],
                    )
                )

    resolved_outputs: List[Var] = list()
    for output_var in root_runtime_block.out_vars:
        output_name = output_var.name
        output_aliases = alias_map.get(output_name, {output_name})
        candidates: List[Tuple[int, int, str, Var]] = list()
        for producer_node_id, producer_output_name, out_var in producer_entries:
            if len(output_aliases & alias_map.get(producer_output_name, {producer_output_name})) == 0:
                continue
            distance = _graph_distance(adjacency, producer_node_id, selected_block.blkdef.ID)
            exact_score = 0 if producer_output_name == output_name else 1
            candidates.append((exact_score, distance, producer_node_id, out_var))

        if len(candidates) > 0:
            candidates.sort(key=lambda item: (item[0], item[1], item[2]))
            resolved_outputs.append(candidates[0][3])
        else:
            resolved_outputs.append(output_var)

    return connections, resolved_outputs


def _blk_sum_slot_raw_mode(blk_sum: BlkSum, slot: int) -> int:
    if slot == 0:
        return int(blk_sum.iInput0)
    if slot == 1:
        return int(blk_sum.iInput1)
    if slot == 2:
        return int(blk_sum.iInput2)
    if slot == 3:
        return int(blk_sum.iInput3)
    return 2


def get_blk_sum_slot_raw_mode(blk_sum: BlkSum, slot: int) -> int:
    """
    Return the raw sign/mode code stored in a BlkSum input slot.

    :param blk_sum: DGS sum block.
    :param slot: Input slot index.
    :return: Raw DGS slot mode.
    """
    return _blk_sum_slot_raw_mode(blk_sum, slot)


def _blk_sum_slot_active_mode(blk_sum: BlkSum, slot: int) -> int:
    if slot == 0:
        return int(blk_sum.iInput0_act)
    if slot == 1:
        return int(blk_sum.iInput1_act)
    if slot == 2:
        return int(blk_sum.iInput2_act)
    if slot == 3:
        return int(blk_sum.iInput3_act)
    return 2


def get_blk_sum_slot_active_mode(blk_sum: BlkSum, slot: int) -> int:
    """
    Return the active sign/mode code stored in a BlkSum input slot.

    :param blk_sum: DGS sum block.
    :param slot: Input slot index.
    :return: Active DGS slot mode.
    """
    return _blk_sum_slot_active_mode(blk_sum, slot)


def _blk_sum_slot_mode(blk_sum: BlkSum, slot: int) -> int:
    active_mode = _blk_sum_slot_active_mode(blk_sum, slot)
    if active_mode in {0, 1, 2}:
        return active_mode
    return _blk_sum_slot_raw_mode(blk_sum, slot)


def _blk_sum_signal_specs(
    blk_sum: BlkSum,
    circuit: DgsCircuit,
) -> Tuple[List[Tuple[str, float]], List[str]]:
    incoming_by_slot: Dict[int, str] = dict()
    outgoing_signals: List[str] = list()

    for sig in circuit.blksigs:
        clean = _normalize_graph_signal_name(sig.loc_name)
        if clean == '':
            continue
        if sig.pnodto == blk_sum.ID:
            incoming_by_slot[int(sig.inodto)] = clean
        if sig.pnodfrom == blk_sum.ID:
            outgoing_signals.append(clean)

    input_terms: List[Tuple[str, float]] = list()
    for slot in range(4):
        sig_name = incoming_by_slot.get(slot, None)
        if sig_name is None:
            continue
        mode = _blk_sum_slot_mode(blk_sum, slot)
        if mode == 2:
            continue
        coeff = 1.0 if mode == 0 else -1.0
        input_terms.append((sig_name, coeff))

    outputs: List[str] = list()
    for sig_name in outgoing_signals:
        if sig_name not in outputs:
            outputs.append(sig_name)

    return input_terms, outputs


def get_blk_sum_signal_specs(
    blk_sum: BlkSum,
    circuit: DgsCircuit,
) -> Tuple[List[Tuple[str, float]], List[str]]:
    """
    Return the effective input terms and outputs of a DGS sum block.

    :param blk_sum: DGS sum block.
    :param circuit: Parsed DGS circuit.
    :return: Tuple with signed input terms and output signal names.
    """
    return _blk_sum_signal_specs(blk_sum, circuit)


def _build_sum_block_from_graphic_node(blk_sum: BlkSum, circuit: DgsCircuit) -> Tuple[Block, List[str], List[str]]:
    input_terms, outputs = _blk_sum_signal_specs(blk_sum, circuit)

    if len(outputs) == 0:
        output_name = _safe_name(blk_sum.loc_name if blk_sum.loc_name != '' else blk_sum.ID)
        outputs = [output_name]

    out_var = Var(name=outputs[0])
    in_vars: List[Var] = list()
    rhs: Expr = Const(0.0)
    input_names: List[str] = list()

    for input_name, coeff in input_terms:
        in_var = Var(name=input_name)
        in_vars.append(in_var)
        input_names.append(input_name)
        rhs = rhs + (Const(coeff) * in_var)

    block = Block(
        algebraic_eqs=[out_var - rhs],
        algebraic_vars=[out_var],
        in_vars=in_vars,
        out_vars=[out_var],
        name=blk_sum.loc_name if blk_sum.loc_name != '' else 'Sum',
    )
    return block, input_names, outputs


def _selected_block_signal_universe(parsed_block: ParsedDgsBlockDefinition) -> set[str]:
    """
    Return the relevant signal universe of a selected composite block.

    :param parsed_block: Parsed composite block definition.
    :return: Signal-name universe.
    """
    return set(parsed_block.blkdef.inputs) | set(parsed_block.blkdef.outputs) | set(parsed_block.blkdef.internals) | set(parsed_block.blkdef.states)


def _rescue_graphic_internal_nodes(
    selected_block: ParsedDgsBlockDefinition,
    node_by_id: dict[str, object],
    node_signals: dict[str, set[str]],
    explicit_component: set[str],
) -> set[str]:
    """
    Rescue disconnected graphical nodes whose signal labels belong to the selected composite universe.

    :param selected_block: Selected parsed block.
    :param node_by_id: Graphic-node index.
    :param node_signals: Signal labels per node.
    :param explicit_component: Nodes already obtained from explicit BlkSig connectivity.
    :return: Additional rescued node ids.
    """
    universe = _selected_block_signal_universe(selected_block)
    rescued: set[str] = set()

    for node_id, node in node_by_id.items():
        if node_id in explicit_component:
            continue
        if not isinstance(node, (BlkRef, BlkFrom, BlkGoto, BlkSum)):
            continue

        sigs = node_signals.get(node_id, set())
        if sigs & universe:
            rescued.add(node_id)

    return rescued

def extract_elmcomp_direct_instances(
    circuit: DgsCircuit,
    root_element: ElmComp,
) -> list[ElmCompInstanceEntry]:
    """
    Extract direct root instances from ElmComp pblk/pelm relations.

    :param circuit: Parsed DGS circuit.
    :param root_element: Root ElmComp.
    :return: Direct instance list.
    """
    element_by_id: dict[str, object] = _build_dgs_element_index(circuit)
    blkdef_by_id: dict[str, BlkDef] = _build_blkdef_index(circuit)

    entries: list[ElmCompInstanceEntry] = list()

    len_pblk: int = len(root_element.pblk)
    len_pelm: int = len(root_element.pelm)

    if len_pblk <= len_pelm:
        n_pairs: int = len_pblk
    else:
        n_pairs = len_pelm

    for idx in range(n_pairs):
        slot_id: str | None = root_element.pblk[idx]
        element_id: str | None = root_element.pelm[idx]

        slot_name: str | None = None
        element_name: str | None = None
        element_kind: str | None = None
        type_id: str | None = None
        type_name: str | None = None
        parameter_values: Dict[str, Any] = dict()

        if slot_id is not None:
            slot_obj: object | None = element_by_id.get(slot_id, None)
            if isinstance(slot_obj, DGSElement):
                slot_name = slot_obj.loc_name
            else:
                slot_name = None
        else:
            slot_name = None

        if element_id is not None:
            element_obj: object | None = element_by_id.get(element_id, None)
            if isinstance(element_obj, ElmDsl):
                element_name = element_obj.loc_name
                element_kind = "ElmDsl"
                if element_obj.typ_id != "":
                    type_id = element_obj.typ_id
                else:
                    type_id = None
                parameter_values = element_obj.get_parameter_map()
            elif isinstance(element_obj, ElmComp):
                element_name = element_obj.loc_name
                element_kind = "ElmComp"
                if element_obj.typ_id != "":
                    type_id = element_obj.typ_id
                else:
                    type_id = None
                parameter_values = dict()
            else:
                element_name = None
                element_kind = None
                type_id = None
                parameter_values = dict()
        else:
            element_name = None
            element_kind = None
            type_id = None
            parameter_values = dict()

        if type_id is not None:
            blkdef_obj: BlkDef | None = blkdef_by_id.get(type_id, None)
            if blkdef_obj is not None:
                type_name = blkdef_obj.loc_name
            else:
                type_name = None
        else:
            type_name = None

        if slot_name is None:
            if type_name is not None:
                slot_name = type_name
            else:
                slot_name = element_name
        else:
            pass

        entry = ElmCompInstanceEntry(
            slot_id=slot_id,
            slot_name=slot_name,
            element_id=element_id,
            element_name=element_name,
            element_kind=element_kind,
            type_id=type_id,
            type_name=type_name,
            parameter_values=parameter_values,
        )

        entries.append(entry)

    return entries

def select_block_instance_from_root(
    circuit: DgsCircuit,
    result: DgsRootBlockResult,
    slot_name: str,
) -> DgsBlockInstanceSelection | None:
    """
    Resolve a parsed block from the explicit root ElmComp slot mapping.

    :param circuit: Parsed DGS circuit.
    :param result: Root block parsing result.
    :param slot_name: Slot name in the root ElmComp.
    :return: Block selection or None.
    """
    entries: list[ElmCompInstanceEntry] = extract_elmcomp_direct_instances(circuit, result.root_element)

    selected_entry: ElmCompInstanceEntry | None = None

    for entry in entries:
        if entry.slot_name == slot_name:
            selected_entry = entry
            break
        elif entry.type_name == slot_name:
            selected_entry = entry
            break
        else:
            pass

    if selected_entry is None:
        return None
    else:
        pass

    if selected_entry.type_id is None:
        return None
    else:
        pass

    parsed_block: ParsedDgsBlockDefinition | None = result.parsed_blocks.get(selected_entry.type_id, None)

    if parsed_block is None:
        return None
    else:
        selection = DgsBlockInstanceSelection(
            instance_entry=selected_entry,
            parsed_block=parsed_block,
        )
        return selection



def _reverse_dependency_graph(graph: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    reverse_graph: Dict[str, Set[str]] = {node_id: set() for node_id in graph.keys()}
    for src, dsts in graph.items():
        for dst in dsts:
            reverse_graph.setdefault(dst, set()).add(src)
    return reverse_graph


def _closure_from_node(graph: Dict[str, Set[str]], start_node: str) -> Set[str]:
    visited: Set[str] = set()
    frontier: List[str] = [start_node]

    while frontier:
        node = frontier.pop()
        if node in visited:
            continue
        visited.add(node)
        for nxt in graph.get(node, set()):
            if nxt not in visited:
                frontier.append(nxt)

    return visited


def _select_named_block(parsed_blocks: Dict[str, ParsedDgsBlockDefinition], block_name: str, block_id: str | None = None) -> Tuple[str, ParsedDgsBlockDefinition]:
    if block_id is not None:
        selected = parsed_blocks.get(block_id)
        if selected is None:
            raise ValueError(f"Block id '{block_id}' not found")
        if selected.blkdef.loc_name != block_name:
            raise ValueError(f"Block id '{block_id}' does not match block name '{block_name}'")
        return block_id, selected

    candidates = [(bid, parsed) for bid, parsed in parsed_blocks.items() if parsed.blkdef.loc_name == block_name]
    if not candidates:
        raise ValueError(f"Block name '{block_name}' not found")

    candidates.sort(key=lambda item: _score_root_candidate(item[1]), reverse=True)
    return candidates[0]


def extract_named_block_subgraph(
    result: DgsRootBlockResult,
    block_name: str,
    block_id: str | None = None,
    mode: BlockScopeMode = BlockScopeMode.InternalOnly) -> DgsBlockSubgraphResult:

    selected_id, selected_block = _select_named_block(result.parsed_blocks, block_name, block_id)
    reverse_graph: Dict[str, Set[str]] = _reverse_dependency_graph(result.dependency_graph)

    node_ids: Set[str] = set()
    node_ids.add(selected_id)

    upstream: Dict[str, Set[str]] = dict()
    downstream: Dict[str, Set[str]] = dict()

    if mode == BlockScopeMode.DownstreamOnly:
        downstream_nodes: Set[str] = _closure_from_node(result.dependency_graph, selected_id)
        node_ids |= downstream_nodes
    elif mode == BlockScopeMode.UpstreamOnly:
        upstream_nodes: Set[str] = _closure_from_node(reverse_graph, selected_id)
        node_ids |= upstream_nodes
    elif mode == BlockScopeMode.FullDependency:
        upstream_nodes = _closure_from_node(reverse_graph, selected_id)
        downstream_nodes = _closure_from_node(result.dependency_graph, selected_id)
        node_ids |= upstream_nodes
        node_ids |= downstream_nodes
    else:
        pass

    sub_children: List[Block] = list()
    shared_signals: Dict[str, Var] = dict()
    for node_id in sorted(node_ids, key=lambda nid: result.parsed_blocks[nid].blkdef.loc_name):
        sub_children.append(_build_block_from_parsed(result.parsed_blocks[node_id], shared_signals))

    for node_id in node_ids:
        if mode == BlockScopeMode.DownstreamOnly:
            downstream[node_id] = {dst for dst in result.dependency_graph.get(node_id, set()) if dst in node_ids}
        elif mode == BlockScopeMode.UpstreamOnly:
            upstream[node_id] = {src for src in reverse_graph.get(node_id, set()) if src in node_ids}
        elif mode == BlockScopeMode.FullDependency:
            upstream[node_id] = {src for src in reverse_graph.get(node_id, set()) if src in node_ids}
            downstream[node_id] = {dst for dst in result.dependency_graph.get(node_id, set()) if dst in node_ids}
        else:
            pass

    selected_runtime_block = _build_block_from_parsed(selected_block, shared_signals)

    if mode == BlockScopeMode.InternalOnly:
        view_block = selected_runtime_block
        view_block.name = selected_block.blkdef.loc_name
    else:
        view_block_name = f"{selected_block.blkdef.loc_name}_{str(mode)}"
        view_block = Block(
            name=view_block_name,
            children=sub_children,
            in_vars=selected_runtime_block.in_vars,
            out_vars=selected_runtime_block.out_vars,
            algebraic_vars=selected_runtime_block.algebraic_vars,
        )

    subgraph = {node_id: {dst for dst in result.dependency_graph.get(node_id, set()) if dst in node_ids} for node_id in node_ids}

    return DgsBlockSubgraphResult(
        selected_block=selected_block,
        view_block=view_block,
        node_ids=node_ids,
        dependency_graph=subgraph,
        upstream=upstream,
        downstream=downstream,
    )

def extract_named_block_internal_only(
    result: DgsRootBlockResult,
    block_name: str,
    block_id: str | None = None,
) -> DgsBlockSubgraphResult:
    """
    Extract only the selected block without any dependency closure.

    :param result: Root block parsing result.
    :param block_name: Target block name.
    :param block_id: Optional exact block identifier.
    :return: Minimal block subgraph result.
    """
    return extract_named_block_subgraph(
        result=result,
        block_name=block_name,
        block_id=block_id,
        mode=BlockScopeMode.InternalOnly,
    )

def extract_root_slot_block_internal_only(
    dgs_path: str,
    slot_name: str,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> DgsBlockSubgraphResult | None:
    """
    Extract the block associated to a root ElmComp slot and keep only that block.

    :param dgs_path: Source DGS path.
    :param slot_name: Root slot name.
    :param root_name: Root ElmComp name.
    :param root_typ_id: Optional root type identifier.
    :return: Internal-only block subgraph or None.
    """
    circuit = DgsCircuit()
    circuit.parse_dgs(dgs_path)

    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    selection: DgsBlockInstanceSelection | None = select_block_instance_from_root(
        circuit=circuit,
        result=result,
        slot_name=slot_name,
    )

    if selection is None:
        return None
    else:
        return extract_named_block_internal_only(
            result=result,
            block_name=selection.parsed_block.blkdef.loc_name,
            block_id=selection.parsed_block.blkdef.ID,
        )

def extract_root_slot_block_internal_signal_tree(
    dgs_path: str,
    slot_name: str,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> DgsBlockSubgraphResult | None:
    """
    Extract an internal hierarchy approximation for a selected root slot using
    signal-name matching only.

    :param dgs_path: Source DGS path.
    :param slot_name: Root slot name or type name fallback.
    :param root_name: Root ElmComp name.
    :param root_typ_id: Optional root type identifier.
    :return: Subgraph result or None.
    """
    circuit = DgsCircuit()
    circuit.parse_dgs(dgs_path)

    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    selection: DgsBlockInstanceSelection | None = select_block_instance_from_root(
        circuit=circuit,
        result=result,
        slot_name=slot_name,
    )

    if selection is None:
        return None
    else:
        pass

    candidates: Dict[str, ParsedDgsBlockDefinition] = _collect_internal_candidate_blocks(
        selected_block=selection.parsed_block,
        parsed_blocks=result.parsed_blocks,
    )

    filtered: Dict[str, ParsedDgsBlockDefinition] = _filter_internal_candidates(
        selected_block=selection.parsed_block,
        candidates=candidates,
        min_score=2,
    )

    node_ids: Set[str] = set()
    node_ids.add(selection.parsed_block.blkdef.ID)
    node_ids |= set(filtered.keys())

    reverse_graph: Dict[str, Set[str]] = _reverse_dependency_graph(result.dependency_graph)
    upstream: Dict[str, Set[str]] = dict()
    downstream: Dict[str, Set[str]] = dict()

    for node_id in node_ids:
        upstream[node_id] = {src for src in reverse_graph.get(node_id, set()) if src in node_ids}
        downstream[node_id] = {dst for dst in result.dependency_graph.get(node_id, set()) if dst in node_ids}

    shared_signals: Dict[str, Var] = dict()
    sub_children: List[Block] = list()
    element_by_id = _build_dgs_element_index(circuit)
    selected_element_obj = element_by_id.get(selection.instance_entry.element_id or "", None)
    nested_parameter_values_by_type_id: Dict[str, Dict[str, Any]] = dict()
    if isinstance(selected_element_obj, ElmComp):
        nested_parameter_values_by_type_id = _parameter_values_by_type_id(extract_elmcomp_direct_instances(circuit, selected_element_obj))

    ordered_ids: List[str] = list(node_ids)
    ordered_ids.sort()

    for node_id in ordered_ids:
        parsed = result.parsed_blocks[node_id]
        parameter_values = selection.instance_entry.parameter_values if node_id == selection.parsed_block.blkdef.ID else nested_parameter_values_by_type_id.get(parsed.blkdef.ID, None)
        sub_children.append(_build_block_from_parsed(parsed, shared_signals, parameter_values=parameter_values))

    selected_runtime_block: Block = _build_block_from_parsed(
        selection.parsed_block,
        shared_signals,
        parameter_values=selection.instance_entry.parameter_values,
    )

    view_block = Block(
        name=f"{selection.parsed_block.blkdef.loc_name}_InternalSignalTree",
        children=sub_children,
        in_vars=selected_runtime_block.in_vars,
        out_vars=selected_runtime_block.out_vars,
        algebraic_vars=selected_runtime_block.algebraic_vars,
    )

    local_graph: Dict[str, Set[str]] = dict()
    for node_id in node_ids:
        local_graph[node_id] = {dst for dst in result.dependency_graph.get(node_id, set()) if dst in node_ids}

    return DgsBlockSubgraphResult(
        selected_block=selection.parsed_block,
        node_ids=node_ids,
        dependency_graph=local_graph,
        upstream=upstream,
        downstream=downstream,
        view_block=view_block,
    )


def extract_root_slot_block_graphical_tree(
    dgs_path: str,
    slot_name: str,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> DgsGraphicTreeResult | None:
    """
    Extract the exact graphical internal tree of a root slot using BlkRef/BlkSig/BlkSum structures.

    :param dgs_path: Source DGS path.
    :param slot_name: Root slot name or type-name fallback.
    :param root_name: Root ElmComp name.
    :param root_typ_id: Optional root type identifier.
    :return: Graphical tree result or None.
    """
    circuit = DgsCircuit()
    circuit.parse_dgs(dgs_path)

    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    selection = select_block_instance_from_root(circuit=circuit, result=result, slot_name=slot_name)

    if selection is None or selection.instance_entry.type_id is None:
        return None

    adjacency = _build_blksig_adjacency(circuit)
    root_node_id = str(selection.instance_entry.type_id)
    explicit_component = _graphic_connected_component(adjacency, root_node_id)

    node_by_id = _build_graphic_node_index(circuit)
    if len(explicit_component) <= 1:
        node_ids = explicit_component
    else:
        node_signals = _build_graphic_node_signal_map(circuit)
        rescued_component = _rescue_graphic_internal_nodes(
            selection.parsed_block,
            node_by_id,
            node_signals,
            explicit_component,
        )
        node_ids = explicit_component | rescued_component
    if len(explicit_component) <= 1:
        node_signals = _build_graphic_node_signal_map(circuit)
    node_labels: dict[str, str] = dict()
    node_kinds: dict[str, str] = dict()
    child_blocks: list[Block] = list()
    child_blocks_by_node: dict[str, Block] = dict()
    child_input_specs: dict[str, List[str]] = dict()
    child_output_specs: dict[str, List[str]] = dict()
    child_node_ids: list[str] = list()

    alias_map = _build_graph_signal_alias_map(node_ids, node_by_id, node_signals)
    local_adj = _build_augmented_graphical_adjacency(node_ids, adjacency, node_by_id, node_signals, alias_map)
    element_by_id = _build_dgs_element_index(circuit)
    selected_element_obj = element_by_id.get(selection.instance_entry.element_id or "", None)
    nested_entries_by_label: Dict[str, ElmCompInstanceEntry] = dict()
    nested_entries_by_type_name: Dict[str, ElmCompInstanceEntry] = dict()
    nested_parameter_values_by_type_id: Dict[str, Dict[str, Any]] = dict()
    if isinstance(selected_element_obj, ElmComp):
        nested_entries = extract_elmcomp_direct_instances(circuit, selected_element_obj)
        nested_entries_by_label = {entry.slot_name: entry for entry in nested_entries if entry.slot_name is not None}
        nested_entries_by_type_name = {entry.type_name: entry for entry in nested_entries if entry.type_name is not None}
        nested_parameter_values_by_type_id = _parameter_values_by_type_id(nested_entries)

    for node_id in sorted(node_ids, key=lambda nid: _graphic_node_label(node_by_id.get(nid, nid))):
        node_obj = node_by_id.get(node_id)
        if node_obj is None:
            continue
        node_labels[node_id] = _graphic_node_label(node_obj)
        node_kinds[node_id] = _graphic_node_kind(node_obj)

        if node_id == root_node_id:
            continue

        if isinstance(node_obj, BlkRef):
            parsed = result.parsed_blocks.get(node_obj.typ_id, None)
            if parsed is None:
                continue
            instance_entry = nested_entries_by_label.get(node_obj.cdisName, None)
            if instance_entry is None:
                instance_entry = nested_entries_by_type_name.get(parsed.blkdef.loc_name, None)

            parameter_values = nested_parameter_values_by_type_id.get(parsed.blkdef.ID, None)
            if instance_entry is not None and len(instance_entry.parameter_values) > 0:
                parameter_values = instance_entry.parameter_values

            blk = _build_block_from_parsed(parsed, dict(), parameter_values=parameter_values)
            blk.name = _graphic_node_label(node_obj)
            child_blocks.append(blk)
            child_blocks_by_node[node_id] = blk
            child_input_specs[node_id] = list(parsed.blkdef.inputs)
            child_output_specs[node_id] = list(parsed.blkdef.outputs)
            child_node_ids.append(node_id)
        elif isinstance(node_obj, BlkSum):
            blk, input_specs, output_specs = _build_sum_block_from_graphic_node(node_obj, circuit)
            child_blocks.append(blk)
            child_blocks_by_node[node_id] = blk
            child_input_specs[node_id] = input_specs
            child_output_specs[node_id] = output_specs
            child_node_ids.append(node_id)

    selected_runtime_block = _build_block_from_parsed(
        selection.parsed_block,
        dict(),
        parameter_values=selection.instance_entry.parameter_values,
    )
    connections, resolved_outputs = _resolve_graphic_block_connections(
        selected_block=selection.parsed_block,
        child_node_ids=child_node_ids,
        child_blocks=child_blocks_by_node,
        child_input_specs=child_input_specs,
        child_output_specs=child_output_specs,
        adjacency=local_adj,
        node_by_id=node_by_id,
        node_signals=node_signals,
        alias_map=alias_map,
        root_runtime_block=selected_runtime_block,
    )

    child_lookup = {node_id: child_blocks_by_node[node_id] for node_id in child_node_ids}
    root_in_lookup = {var.name: var for var in selected_runtime_block.in_vars}
    for instruction in connections:
        consumer_block = child_lookup[instruction.consumer_node_id]
        if instruction.consumer_input_index is None or instruction.consumer_input_index >= len(consumer_block.in_vars):
            continue
        consumer_var = consumer_block.in_vars[instruction.consumer_input_index]

        if instruction.source_kind == "block_output" and instruction.source_node_id is not None and instruction.source_output_index is not None:
            producer_block = child_lookup[instruction.source_node_id]
            if instruction.source_output_index < len(producer_block.out_vars):
                consumer_block.connect([consumer_var], [producer_block.out_vars[instruction.source_output_index]])
        elif instruction.source_kind == "root_input" and instruction.source_root_name is not None:
            root_var = root_in_lookup.get(instruction.source_root_name, None)
            if root_var is not None:
                consumer_block.connect([consumer_var], [root_var])

    view_block = Block(
        name=selection.parsed_block.blkdef.loc_name,
        children=child_blocks,
        in_vars=selected_runtime_block.in_vars,
        out_vars=resolved_outputs,
        algebraic_vars=selected_runtime_block.algebraic_vars,
    )

    return DgsGraphicTreeResult(
        selected_block=selection.parsed_block,
        view_block=view_block,
        node_ids=node_ids,
        adjacency=local_adj,
        node_labels=node_labels,
        node_kinds=node_kinds,
        child_node_ids=child_node_ids,
        connections=connections,
    )

def export_named_block_subgraph_to_python(
    dgs_path: str,
    output_path: str,
    block_name: str,
    *,
    block_id: str | None = None,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
    mode: BlockScopeMode = BlockScopeMode.InternalOnly,
) -> Path:
    """
    Export a selected DGS block subgraph as a standalone Python module.

    :param dgs_path: Source DGS file.
    :param output_path: Destination `.py` file.
    :param block_name: Target block name inside the parsed DGS library.
    :param block_id: Optional exact DGS block identifier.
    :param root_name: Root ElmComp display name.
    :param root_typ_id: Optional exact root typ_id.
    :return: Path to the generated Python module.
    """
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    subgraph = extract_named_block_subgraph(
        result,
        block_name=block_name,
        block_id=block_id,
        mode=mode,
    )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    module_text = _emit_template_style_module(result, subgraph, dgs_path)

    out_path.write_text(module_text, encoding="utf-8")
    return out_path


def export_named_block_subgraph_tree_to_python(
    dgs_path: str,
    output_path: str,
    block_name: str,
    *,
    block_id: str | None = None,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
    mode: BlockScopeMode = BlockScopeMode.InternalOnly,
) -> Path:
    """
    Export a selected DGS block subgraph as a serialized block-tree Python module.
    """
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    subgraph = extract_named_block_subgraph(
        result,
        block_name=block_name,
        block_id=block_id,
        mode=mode,
    )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    module_text = _emit_tree_style_module(result, subgraph, dgs_path)
    out_path.write_text(module_text, encoding="utf-8")
    return out_path

def export_root_slot_block_internal_signal_tree_to_python(
    dgs_path: str,
    output_path: str,
    slot_name: str,
    *,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> Path:
    """
    Export a root-slot internal signal-tree approximation as a serialized block-tree module.

    :param dgs_path: Source DGS file.
    :param output_path: Destination `.py` file.
    :param slot_name: Root slot name or type-name fallback.
    :param root_name: Root ElmComp display name.
    :param root_typ_id: Optional exact root typ_id.
    :return: Path to the generated Python module.
    """
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    subgraph = extract_root_slot_block_internal_signal_tree(
        dgs_path=dgs_path,
        slot_name=slot_name,
        root_name=root_name,
        root_typ_id=root_typ_id,
    )

    if subgraph is None:
        raise ValueError(f"Could not resolve internal signal tree for slot '{slot_name}'")
    else:
        pass

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    module_text = _emit_tree_style_module(result, subgraph, dgs_path)
    out_path.write_text(module_text, encoding="utf-8")
    return out_path


def export_root_slot_block_graphical_tree_to_python(
    dgs_path: str,
    output_path: str,
    slot_name: str,
    *,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> Path:
    """
    Export the exact graphical internal tree of a root slot as a serialized block-tree module.

    :param dgs_path: Source DGS file.
    :param output_path: Destination `.py` file.
    :param slot_name: Root slot name.
    :param root_name: Root ElmComp display name.
    :param root_typ_id: Optional root type identifier.
    :return: Path to the generated Python module.
    """
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    graph_tree = extract_root_slot_block_graphical_tree(
        dgs_path=dgs_path,
        slot_name=slot_name,
        root_name=root_name,
        root_typ_id=root_typ_id,
    )

    if graph_tree is None:
        raise ValueError(f"Could not resolve graphical tree for slot '{slot_name}'")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    graph_repr = pprint.pformat(_graph_to_serializable(graph_tree.adjacency), width=120, sort_dicts=False)
    metadata_repr = pprint.pformat({
        "dgs_path": str(dgs_path),
        "root_element_name": result.root_element.loc_name,
        "root_element_typ_id": result.root_element.typ_id,
        "selected_block_id": graph_tree.selected_block.blkdef.ID,
        "selected_block_name": graph_tree.selected_block.blkdef.loc_name,
        "node_ids": sorted(graph_tree.node_ids),
        "node_labels": graph_tree.node_labels,
        "node_kinds": graph_tree.node_kinds,
    }, width=120, sort_dicts=False)

    module_text = f'''# Auto-generated DGS graphical block tree export.
# Source: {dgs_path}

from VeraGridEngine.Utils.Symbolic.block import Block


BLOCK_DATA = {pprint.pformat(graph_tree.view_block.to_dict(), width=120, sort_dicts=False)}

GRAPHICAL_ADJACENCY = {graph_repr}

METADATA = {metadata_repr}


def get_block() -> Block:
    return Block.parse(BLOCK_DATA)


def get_graphical_adjacency() -> dict:
    return GRAPHICAL_ADJACENCY


def get_metadata() -> dict:
    return METADATA
'''

    out_path.write_text(module_text, encoding="utf-8")
    return out_path


def export_root_slot_block_graphical_template_to_python(
    dgs_path: str,
    output_path: str,
    slot_name: str,
    *,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> Path:
    """
    Export the exact graphical tree of a root slot as a standalone EMT template module.

    :param dgs_path: Source DGS file.
    :param output_path: Destination `.py` file.
    :param slot_name: Root slot name.
    :param root_name: Root ElmComp display name.
    :param root_typ_id: Optional exact root typ_id.
    :return: Path to the generated Python module.
    """
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    graph_tree = extract_root_slot_block_graphical_tree(
        dgs_path=dgs_path,
        slot_name=slot_name,
        root_name=root_name,
        root_typ_id=root_typ_id,
    )
    if graph_tree is None:
        raise ValueError(f"Could not extract graphical tree for slot '{slot_name}'")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    module_text = _emit_template_style_module(result, graph_tree, dgs_path)

    out_path.write_text(module_text, encoding="utf-8")
    return out_path


def export_root_elmcomp_template_to_python(
    dgs_path: str,
    output_path: str,
    root_name: str,
    *,
    root_typ_id: str | None = None,
) -> Path:
    """
    Export one root ElmComp as a standalone EMT template module.

    :param dgs_path: Source DGS file.
    :param output_path: Destination `.py` file.
    :param root_name: Root ElmComp display name.
    :param root_typ_id: Optional exact root typ_id.
    :return: Path to the generated Python module.
    """
    circuit = DgsCircuit()
    circuit.parse_dgs(dgs_path)
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    direct_root_block = _build_direct_root_elmcomp_block(circuit, result)
    root_subgraph = DgsBlockSubgraphResult(
        selected_block=result.root_blkdef,
        view_block=direct_root_block,
        node_ids=set(result.dependency_graph.keys()),
        dependency_graph=result.dependency_graph,
        upstream=dict(),
        downstream=dict(),
    )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    module_text = _emit_template_style_module(
        result,
        root_subgraph,
        dgs_path,
        template_name=result.root_element.loc_name,
    )
    out_path.write_text(module_text, encoding="utf-8")
    return out_path

def export_root_slot_block_internal_signal_template_to_python(
    dgs_path: str,
    output_path: str,
    slot_name: str,
    *,
    root_name: str = "Grid Forming Converter",
    root_typ_id: str | None = None,
) -> Path:
    """
    Export a root-slot internal signal-tree approximation as an EMT template module.

    :param dgs_path: Source DGS file.
    :param output_path: Destination `.py` file.
    :param slot_name: Root slot name or type-name fallback.
    :param root_name: Root ElmComp display name.
    :param root_typ_id: Optional exact root typ_id.
    :return: Path to the generated Python module.
    """
    result = dgs_to_root_block(dgs_path, root_name=root_name, root_typ_id=root_typ_id)
    subgraph = extract_root_slot_block_internal_signal_tree(
        dgs_path=dgs_path,
        slot_name=slot_name,
        root_name=root_name,
        root_typ_id=root_typ_id,
    )

    if subgraph is None:
        raise ValueError(f"Could not resolve internal signal tree for slot '{slot_name}'")
    else:
        pass

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    module_text = _emit_template_style_module(result, subgraph, dgs_path)
    out_path.write_text(module_text, encoding="utf-8")
    return out_path
