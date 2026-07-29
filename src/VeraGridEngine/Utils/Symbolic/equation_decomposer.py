# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections import deque
from typing import List, Tuple, Dict, Optional, Any, Set
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import BlockType

try:
    from VeraGridEngine.Utils.Symbolic.hierarchical_layout_v2 import compute_layout as _compute_layout_v2
    _HAVE_LAYOUT_V2 = True
except ImportError as e:
    _HAVE_LAYOUT_V2 = False
    _layout_import_error = str(e)


class EquationDecomposer:
    """
    Decomposes a Block containing algebraic_eqs and state_eqs
    into a hierarchical Block with children representing basic operations
    (gain, sum, product, divide, etc.) connected as a block diagram.

    This is the inverse of Block.unify_blocks(). Instead of flattening
    child blocks into a single equation set, it takes a monolithic block
    of equations and produces a tree of simple operation blocks that can
    be visually rendered in the DynamicBlockEditorGUI.
    """

    def __init__(self, var_factory: VarFactory):
        self.vf = var_factory
        self._counter: int = 0
        self._param_uids: set = set()
        self._orig_block: Block | None = None
        self.block2blocktype: Dict[int, BlockType] = dict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decompose(self, block: Block) -> Tuple[Block, Dict[int, BlockType]]:
        """
        Decompose a block's equations into child operation blocks.

        Returns a new Block with ``children`` and a populated
        ``BlockDiagram`` suitable for the graphical editor.
        """
        self._counter = 0
        self._orig_block = block
        self.block2blocktype = dict()

        self._collect_parameter_uids(block)
        self._prepare_block_signal_variables(block)

        child_blocks: List[Block] = []
        algebraic_entries = self._collect_algebraic_entries(block)
        state_entries = self._collect_state_entries(block)

        for state_var, rhs in state_entries:
            self._ensure_connectable_var(state_var)
            rhs_signal, rhs_blocks = self._lower_signal_expr(rhs)
            child_blocks.extend(rhs_blocks)

            integrator_in_vars = [rhs_signal] if isinstance(rhs_signal, sym.Var) else list()
            integrator_block = Block(
                state_vars=[state_var],
                state_eqs=[rhs_signal],
                in_vars=integrator_in_vars,
                out_vars=[state_var],
                name="integrator",
                is_decomposable=False,
            )
            self.block2blocktype[integrator_block.uid] = BlockType.INTEGRATOR
            child_blocks.append(integrator_block)

        for algebraic_var, rhs in algebraic_entries:
            self._ensure_connectable_var(algebraic_var)
            rhs_signal, rhs_blocks = self._lower_signal_expr(rhs)
            if len(rhs_blocks) == 0:
                child_blocks.append(self._make_direct_definition_block(algebraic_var, rhs))
            else:
                self._remap_last_output(rhs_blocks, rhs_signal, algebraic_var)
                child_blocks.extend(rhs_blocks)

        new_event_dict = dict(block.event_dict) if block.event_dict else {}
        new_mode_dict = dict(block.mode_dict) if block.mode_dict else {}
        new_parameters = dict(block.parameters) if block.parameters else {}
        new_init_eqs = dict(block.init_eqs) if block.init_eqs else {}
        new_init_values = dict(block.init_values) if block.init_values else {}
        new_diff_init_eqs = dict(block.diff_init_eqs) if block.diff_init_eqs else {}

        result = Block(
            name=block.name,
            children=child_blocks,
            in_vars=list(block.in_vars),
            out_vars=list(block.out_vars),
            event_dict=new_event_dict,
            mode_dict=new_mode_dict,
            parameters=new_parameters,
            init_eqs=new_init_eqs,
            init_values=new_init_values,
            diff_init_eqs=new_diff_init_eqs,
            external_mapping=dict(block.external_mapping) if block.external_mapping else None,
            api_obj_mapping=dict(block.api_obj_mapping) if block.api_obj_mapping else None,
        )
        result.uid = block.uid
        # result.diagram = diagram

        return result, self.block2blocktype

    # ------------------------------------------------------------------
    # Parameter collection
    # ------------------------------------------------------------------

    def _collect_parameter_uids(self, block: Block) -> None:
        self._param_uids.clear()
        for p in block.event_dict or {}:
            self._param_uids.add(p.non_mutable_uid)
        for p in block.mode_dict or {}:
            self._param_uids.add(p.non_mutable_uid)
        for p in block.parameters or {}:
            self._param_uids.add(p.non_mutable_uid)

    def _is_parameter(self, expr: sym.Expr) -> bool:
        if isinstance(expr, sym.Var):
            return expr.non_mutable_uid in self._param_uids
        return False

    def _prepare_block_signal_variables(self, block: Block) -> None:
        for var in block.in_vars:
            self._ensure_connectable_var(var)
        for var in block.out_vars:
            self._ensure_connectable_var(var)
        for var in block.state_vars:
            self._ensure_connectable_var(var)
        for var in block.algebraic_vars:
            self._ensure_connectable_var(var)

    def _ensure_connectable_var(self, var: sym.Var) -> None:
        if var.shared_ref is None and var.ref is None:
            self.vf.add_shared_ref_to_var(var, f"eqdec_{var.non_mutable_uid}")

    def _is_in_var(self, var: sym.Var) -> bool:
        if self._orig_block is None:
            return False
        for v in self._orig_block.in_vars:
            if v.non_mutable_uid == var.non_mutable_uid:
                return True
        return False

    @staticmethod
    def _contains_var(expr: sym.Expr, target: sym.Var) -> bool:
        for v in expr.get_vars():
            if v.non_mutable_uid == target.non_mutable_uid:
                return True
        return False

    # ------------------------------------------------------------------
    # Naming helpers
    # ------------------------------------------------------------------

    def _new_name(self, prefix: str = "x") -> str:
        self._counter += 1
        return f"_{prefix}_{self._counter}"

    def _new_signal_var(self, prefix: str = "x") -> sym.Var:
        name = self._new_name(prefix)
        return self.vf.add_var(name, shared_reference=f"eqdec_{name}")

    # ------------------------------------------------------------------
    # Equation mapping
    # ------------------------------------------------------------------

    def _collect_algebraic_entries(self, block: Block) -> List[Tuple[sym.Var, sym.Expr]]:
        entries: List[Tuple[sym.Var, sym.Expr]] = list()
        for eq in block.algebraic_eqs:
            defined_var = self._find_defined_var(eq, block.algebraic_vars)
            if defined_var is None:
                continue
            rhs = self._extract_rhs(eq, defined_var)
            if rhs is None:
                rhs = self._extract_rhs_fallback(eq, defined_var)
            if rhs is None:
                rhs = eq
            entries.append((defined_var, rhs))
        return entries

    def _collect_state_entries(self, block: Block) -> List[Tuple[sym.Var, sym.Expr]]:
        entries: List[Tuple[sym.Var, sym.Expr]] = list()
        count = min(len(block.state_vars), len(block.state_eqs))
        for idx in range(count):
            entries.append((block.state_vars[idx], block.state_eqs[idx]))
        return entries

    @staticmethod
    def _find_defined_var(eq: sym.Expr, candidates: List[sym.Var]) -> Optional[sym.Var]:
        if isinstance(eq, sym.BinOp) and eq.op == "-":
            if isinstance(eq.left, sym.Var):
                for candidate in candidates:
                    if eq.left.non_mutable_uid == candidate.non_mutable_uid:
                        return candidate
            if isinstance(eq.right, sym.Var):
                for candidate in candidates:
                    if eq.right.non_mutable_uid == candidate.non_mutable_uid:
                        return candidate
        return None

    # ------------------------------------------------------------------
    # RHS extraction
    # ------------------------------------------------------------------

    def _extract_rhs(self, eq: sym.Expr, defined_var: sym.Var) -> sym.Expr | None:
        if isinstance(eq, sym.BinOp) and eq.op == "-":
            if isinstance(eq.left, sym.Var) and eq.left.non_mutable_uid == defined_var.non_mutable_uid:
                return eq.right
            if isinstance(eq.right, sym.Var) and eq.right.non_mutable_uid == defined_var.non_mutable_uid:
                return eq.left
        return None

    def _extract_factor_for_var(self, expr: sym.Expr, var: sym.Var) -> sym.Expr | None:
        """
        If *expr* has the form ``factor * var`` or ``var * factor`` return
        the *factor* sub-expression, otherwise return ``None``.
        """
        if isinstance(expr, sym.Var):
            if expr.non_mutable_uid == var.non_mutable_uid:
                return sym.Const(1.0)
            return None
        if isinstance(expr, sym.BinOp) and expr.op == "*":
            if isinstance(expr.left, sym.Var) and expr.left.non_mutable_uid == var.non_mutable_uid:
                return expr.right
            if isinstance(expr.right, sym.Var) and expr.right.non_mutable_uid == var.non_mutable_uid:
                return expr.left
        return None

    def _extract_rhs_fallback(self, eq: sym.Expr, defined_var: sym.Var) -> sym.Expr | None:
        if isinstance(eq, sym.BinOp):
            left_has = self._contains_var(eq.left, defined_var)
            right_has = self._contains_var(eq.right, defined_var)

            if eq.op == "-":
                if left_has and not right_has:
                    factor = self._extract_factor_for_var(eq.left, defined_var)
                    if factor is not None and not (isinstance(factor, sym.Const) and factor.value == 1.0):
                        return eq.right / factor
                    return eq.right
                if right_has and not left_has:
                    factor = self._extract_factor_for_var(eq.right, defined_var)
                    if factor is not None and not (isinstance(factor, sym.Const) and factor.value == 1.0):
                        return eq.left / factor
                    return eq.left

            elif eq.op == "+":
                if left_has and not right_has:
                    return -eq.right
                if right_has and not left_has:
                    return -eq.left

        if self._contains_var(eq, defined_var):
            return eq

        return None

    # ------------------------------------------------------------------
    # Expression decomposition (core)
    # ------------------------------------------------------------------

    def _lower_signal_expr(self, expr: sym.Expr) -> Tuple[sym.Var, List[Block]]:
        if isinstance(expr, sym.Var):
            self._ensure_connectable_var(expr)
            return expr, []
        elif isinstance(expr, sym.Const):
            y = self._new_signal_var("const")
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - expr],
                out_vars=[y],
                name="const",
                is_decomposable=False
            )
            self.block2blocktype[blk.uid] = BlockType.CONST
            return y, [blk]
        elif isinstance(expr, sym.BinOp):
            return self._lower_binop(expr)
        elif isinstance(expr, sym.UnOp):
            return self._lower_unop(expr)
        elif isinstance(expr, sym.Func):
            return self._lower_func(expr)
        elif isinstance(expr, sym.Func2):
            return self._lower_func2(expr)
        else:
            raise TypeError(f"Unsupported expression type: {type(expr)}")

    def _lower_operand(self, expr: sym.Expr) -> Tuple[sym.Expr, sym.Var | None, List[Block]]:
        if isinstance(expr, sym.Const):
            return expr, None, []
        elif isinstance(expr, sym.Var) and self._is_parameter(expr):
            return expr, None, []
        else:
            signal_var, blocks = self._lower_signal_expr(expr)
            return signal_var, signal_var, blocks

    def _lower_binop(self, expr: sym.BinOp) -> Tuple[sym.Var, List[Block]]:
        if expr.op in {"+", "-"}:
            return self._lower_sum_like(expr)
        elif expr.op in {"*", "/"}:
            return self._lower_product_like(expr)
        elif expr.op == "**":
            return self._lower_power(expr)
        else:
            raise ValueError(f"Unsupported binary operator: {expr.op}")

    def _lower_unop(self, expr: sym.UnOp) -> Tuple[sym.Var, List[Block]]:
        if expr.op == "-":
            inner_expr, inner_var, inner_blocks = self._lower_operand(expr.operand)
            if inner_var is not None:
                y = self._new_signal_var("gain")
                blk = Block(
                    algebraic_vars=[y],
                    algebraic_eqs=[y - (-inner_expr)],
                    in_vars=[inner_var],
                    out_vars=[y],
                    name="gain",
                    is_decomposable=False,
                )
                self.block2blocktype[blk.uid] = BlockType.GAIN
                return y, inner_blocks + [blk]
            return self._make_expression_block(-inner_expr, "neg", BlockType.NOTYPE)
        else:
            raise ValueError(f"Unsupported unary operator: {expr.op}")

    def _lower_func(self, expr: sym.Func) -> Tuple[sym.Var, List[Block]]:
        arg_expr, arg_var, arg_blocks = self._lower_operand(expr.arg)
        return self._make_expression_block(
            expr=self._rebuild_func(expr.op, arg_expr),
            name=expr.op,
            block_type=self._block_type_for_unary_func(expr.op),
            in_vars=[arg_var] if arg_var is not None else [],
            prefix=expr.op,
            preceding_blocks=arg_blocks,
        )

    def _lower_func2(self, expr: sym.Func2) -> Tuple[sym.Var, List[Block]]:
        arg1_expr, arg1_var, arg1_blocks = self._lower_operand(expr.arg1)
        arg2_expr, arg2_var, arg2_blocks = self._lower_operand(expr.arg2)
        return self._make_expression_block(
            expr=self._rebuild_func2(expr.name, arg1_expr, arg2_expr),
            name=expr.name,
            block_type=self._block_type_for_binary_func(expr.name),
            in_vars=[var for var in [arg1_var, arg2_var] if var is not None],
            prefix=expr.name,
            preceding_blocks=arg1_blocks + arg2_blocks,
        )

    def _lower_sum_like(self, expr: sym.BinOp) -> Tuple[sym.Var, List[Block]]:
        terms = self._flatten_sum_terms(expr)
        rhs_expr: sym.Expr | None = None
        in_vars: List[sym.Var] = list()
        blocks: List[Block] = list()

        for term_expr, sign in terms:
            lowered_expr, input_var, term_blocks = self._lower_operand(term_expr)
            blocks.extend(term_blocks)
            signed_expr = lowered_expr if sign > 0 else -lowered_expr
            rhs_expr = signed_expr if rhs_expr is None else rhs_expr + signed_expr
            if input_var is not None:
                in_vars.append(input_var)

        if rhs_expr is None:
            rhs_expr = sym.Const(0.0)

        block_type = BlockType.SUM if len(in_vars) > 0 else BlockType.NOTYPE
        return self._make_expression_block(
            expr=rhs_expr,
            name="sum",
            block_type=block_type,
            in_vars=in_vars,
            prefix="sum",
            preceding_blocks=blocks,
        )

    def _lower_product_like(self, expr: sym.BinOp) -> Tuple[sym.Var, List[Block]]:
        numerator_terms, denominator_terms = self._flatten_product_terms(expr)
        operand_exprs: List[sym.Expr] = list()
        signal_vars: List[sym.Var] = list()
        blocks: List[Block] = list()

        for term in numerator_terms:
            lowered_expr, input_var, term_blocks = self._lower_operand(term)
            blocks.extend(term_blocks)
            operand_exprs.append(lowered_expr)
            if input_var is not None:
                signal_vars.append(input_var)

        denominator_exprs: List[sym.Expr] = list()
        for term in denominator_terms:
            lowered_expr, input_var, term_blocks = self._lower_operand(term)
            blocks.extend(term_blocks)
            denominator_exprs.append(lowered_expr)
            if input_var is not None:
                signal_vars.append(input_var)

        numerator_expr = self._combine_factors(operand_exprs)
        denominator_expr = self._combine_factors(denominator_exprs) if len(denominator_exprs) > 0 else None
        rhs_expr = numerator_expr if denominator_expr is None else numerator_expr / denominator_expr

        if len(signal_vars) == 1:
            return self._make_expression_block(
                expr=rhs_expr,
                name="gain",
                block_type=BlockType.GAIN,
                in_vars=signal_vars,
                prefix="gain",
                preceding_blocks=blocks,
            )

        block_type = BlockType.PRODUCT if len(signal_vars) > 0 else BlockType.NOTYPE
        return self._make_expression_block(
            expr=rhs_expr,
            name="product" if denominator_expr is None else "divide",
            block_type=BlockType.DIVIDE if denominator_expr is not None and len(signal_vars) > 0 else block_type,
            in_vars=signal_vars,
            prefix="prod" if denominator_expr is None else "div",
            preceding_blocks=blocks,
        )

    def _lower_power(self, expr: sym.BinOp) -> Tuple[sym.Var, List[Block]]:
        left_expr, left_var, left_blocks = self._lower_operand(expr.left)
        right_expr, right_var, right_blocks = self._lower_operand(expr.right)
        return self._make_expression_block(
            expr=left_expr ** right_expr,
            name="power",
            block_type=BlockType.POWER,
            in_vars=[var for var in [left_var, right_var] if var is not None],
            prefix="pow",
            preceding_blocks=left_blocks + right_blocks,
        )

    # ------------------------------------------------------------------
    # Output remapping
    # ------------------------------------------------------------------

    def _remap_last_output(self, blocks: List[Block], current_output: sym.Var, target_output: sym.Var) -> sym.Var:
        if not blocks:
            return current_output
        last = blocks[-1]
        if current_output is not target_output:
            last.update_equations(current_output, target_output)
            last.update_variables(current_output, target_output)
            for i, v in enumerate(last.algebraic_vars):
                if v.non_mutable_uid == current_output.non_mutable_uid:
                    last.algebraic_vars[i] = target_output
            for i, v in enumerate(last.out_vars):
                if v.non_mutable_uid == current_output.non_mutable_uid:
                    last.out_vars[i] = target_output
        return target_output

    def _make_pass_through(self, target_var: sym.Var, source_var: sym.Var) -> Block:
        blk = Block(
            algebraic_vars=[target_var],
            algebraic_eqs=[target_var - source_var],
            in_vars=[source_var],
            out_vars=[target_var],
            name="passthrough",
        )
        self.block2blocktype[blk.uid] = BlockType.NOTYPE
        return blk

    def _make_direct_definition_block(self, target_var: sym.Var, rhs: sym.Expr) -> Block:
        if isinstance(rhs, sym.Var):
            self._ensure_connectable_var(rhs)
            return self._make_pass_through(target_var, rhs)
        elif isinstance(rhs, sym.Const):
            blk = Block(
                algebraic_vars=[target_var],
                algebraic_eqs=[target_var - rhs],
                out_vars=[target_var],
                name="const",
                is_decomposable=False,
            )
            self.block2blocktype[blk.uid] = BlockType.CONST
            return blk
        else:
            blk = Block(
                algebraic_vars=[target_var],
                algebraic_eqs=[target_var - rhs],
                out_vars=[target_var],
                name="expr",
                is_decomposable=False,
            )
            self.block2blocktype[blk.uid] = BlockType.NOTYPE
            return blk

    def _make_expression_block(
        self,
        expr: sym.Expr,
        name: str,
        block_type: BlockType,
        in_vars: List[sym.Var] | None = None,
        prefix: str | None = None,
        preceding_blocks: List[Block] | None = None,
    ) -> Tuple[sym.Var, List[Block]]:
        out_var = self._new_signal_var(prefix or name or "x")
        blk = Block(
            algebraic_vars=[out_var],
            algebraic_eqs=[out_var - expr],
            in_vars=list(in_vars) if in_vars is not None else [],
            out_vars=[out_var],
            name=name,
            is_decomposable=False,
        )
        self.block2blocktype[blk.uid] = block_type
        blocks = list(preceding_blocks) if preceding_blocks is not None else list()
        blocks.append(blk)
        return out_var, blocks

    def _flatten_sum_terms(self, expr: sym.Expr, sign: int = 1) -> List[Tuple[sym.Expr, int]]:
        if isinstance(expr, sym.BinOp) and expr.op == "+":
            return self._flatten_sum_terms(expr.left, sign) + self._flatten_sum_terms(expr.right, sign)
        elif isinstance(expr, sym.BinOp) and expr.op == "-":
            return self._flatten_sum_terms(expr.left, sign) + self._flatten_sum_terms(expr.right, -sign)
        elif isinstance(expr, sym.UnOp) and expr.op == "-":
            return self._flatten_sum_terms(expr.operand, -sign)
        else:
            return [(expr, sign)]

    def _flatten_product_terms(self, expr: sym.Expr) -> Tuple[List[sym.Expr], List[sym.Expr]]:
        if isinstance(expr, sym.BinOp) and expr.op == "*":
            left_num, left_den = self._flatten_product_terms(expr.left)
            right_num, right_den = self._flatten_product_terms(expr.right)
            return left_num + right_num, left_den + right_den
        elif isinstance(expr, sym.BinOp) and expr.op == "/":
            left_num, left_den = self._flatten_product_terms(expr.left)
            right_num, right_den = self._flatten_product_terms(expr.right)
            return left_num + right_den, left_den + right_num
        elif isinstance(expr, sym.UnOp) and expr.op == "-":
            return [sym.Const(-1.0), expr.operand], []
        else:
            return [expr], []

    @staticmethod
    def _combine_factors(factors: List[sym.Expr]) -> sym.Expr:
        if len(factors) == 0:
            return sym.Const(1.0)
        result = factors[0]
        for factor in factors[1:]:
            result = result * factor
        return result

    @staticmethod
    def _rebuild_func(op: str, arg: sym.Expr) -> sym.Expr:
        unary_builders = {
            "sin": sym.sin,
            "cos": sym.cos,
            "tan": sym.tan,
            "exp": sym.exp,
            "log": sym.log,
            "log10": sym.log10,
            "sqrt": sym.sqrt,
            "asin": sym.asin,
            "acos": sym.acos,
            "atan": sym.atan,
            "sinh": sym.sinh,
            "cosh": sym.cosh,
            "tanh": sym.tanh,
            "floor": sym.floor,
            "ceil": sym.ceil,
            "round": sym.round,
            "real": sym.real,
            "imag": sym.imag,
            "conj": sym.conj,
            "angle": sym.angle,
            "abs": sym.abs,
            "heaviside": sym.heaviside,
            "rand": sym.rand,
        }
        if op not in unary_builders:
            raise ValueError(f"Unsupported function: {op}")
        return unary_builders[op](arg)

    @staticmethod
    def _rebuild_func2(name: str, arg1: sym.Expr, arg2: sym.Expr) -> sym.Expr:
        if name == "atan2":
            return sym.atan2(arg1, arg2)
        elif name == "min":
            return sym.min(arg1, arg2)
        elif name == "max":
            return sym.max(arg1, arg2)
        else:
            raise ValueError(f"Unsupported function: {name}")

    @staticmethod
    def _block_type_for_unary_func(op: str) -> BlockType:
        mapping = {
            "sin": BlockType.SIN,
            "cos": BlockType.COS,
            "tan": BlockType.TAN,
            "exp": BlockType.EXP,
            "log": BlockType.LOG,
            "log10": BlockType.LOG10,
            "sqrt": BlockType.SQRT,
            "asin": BlockType.ASIN,
            "acos": BlockType.ACOS,
            "atan": BlockType.ATAN,
            "sinh": BlockType.SINH,
            "cosh": BlockType.COSH,
            "tanh": BlockType.TANH,
            "floor": BlockType.FLOOR,
            "ceil": BlockType.CEIL,
            "round": BlockType.ROUND,
            "real": BlockType.REAL,
            "imag": BlockType.IMAG,
            "conj": BlockType.CONJ,
            "angle": BlockType.ANGLE,
            "abs": BlockType.ABS,
            "heaviside": BlockType.HEAVISIDE,
            "rand": BlockType.RAND,
        }
        return mapping.get(op, BlockType.NOTYPE)

    @staticmethod
    def _block_type_for_binary_func(name: str) -> BlockType:
        mapping = {
            "atan2": BlockType.ATAN2,
            "min": BlockType.MIN,
            "max": BlockType.MAX,
        }
        return mapping.get(name, BlockType.NOTYPE)

