# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Module: JIT Equation Compiler & Numerical Discretization Engine
===============================================================

Abstract
--------
This module implements a symbolic-to-numeric translation engine designed to generate
optimized executable kernels for Differential-Algebraic Equation (DAE) systems.
It operates by traversing the symbolic Abstract Syntax Tree (AST) of the model and
injecting discrete time-stepping schemes (e.g., Implicit Trapezoidal, BDF2) directly
into the residual evaluation code.

Architectural Rationale
-----------------------
The decoupling of the compilation logic from the `DiffBlockSolver` enforces a strict
separation of concerns between the network topology management (Solver) and the
numerical discretization strategy (Compiler). This abstraction allows for the
interchangeability of integration methods—facilitating the switch between A-stable
and L-stable schemes—without altering the solver's core iterative algorithms.

Performance Optimization

------------------------
By fusing the physical model equations with the numerical integration formulas into
a single JIT-compiled kernel, this module eliminates the interpreter overhead and
intermediate memory allocations typical of vectorized Numpy operations. This results
in a monolithic residual evaluation function optimized for the high-frequency
computation requirements of Electromagnetic Transient (EMT) simulations.
"""

# Import libraries for utils
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Tuple, Set
import os
import importlib.util
import hashlib
import scipy.sparse as sp

#RMS
from VeraGridEngine.Utils.Symbolic.symbolic import expression2numba
from VeraGridEngine.enumerations import DynamicIntegrationMethod
#Totally integrated
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, BinOp, UnOp, Func, Var, Const


def _is_zero(s: str) -> bool:
    return s in ["0.0", "0", "0.00", "(-0.0)"]

def _is_one(s: str) -> bool:
    return s in ["1.0", "1", "1.00"]

def _compile_to_file(full_source: str, func_name: str) -> Callable:
    """
    Writes source code to a file in __pycache_jit__ and imports it.
    This allows Numba's cache=True to work.
    """
    import sys

    header = "import numpy as np\nimport math\nfrom VeraGridEngine.Utils.Symbolic.symbolic import heaviside_num as _heaviside\n\n"
    full_content = header + full_source

    root_dir = os.getcwd()
    cache_dir = os.path.join(root_dir, "__pycache_jit__")
    os.makedirs(cache_dir, exist_ok=True)

    if cache_dir not in sys.path:
        sys.path.append(cache_dir)

    content_hash = hashlib.md5(full_content.encode('utf-8')).hexdigest()[:16]
    mod_name = f"{func_name}_{content_hash}"
    filename = f"{mod_name}.py"
    filepath = os.path.join(cache_dir, filename)

    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write(full_content)

    if mod_name in sys.modules:
        return sys.modules[mod_name].__dict__[func_name]

    spec = importlib.util.spec_from_file_location(mod_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)

    return module.__dict__[func_name]

# ==============================================================================
# 1. Discretization strategy (Numerical Methods)
# ==============================================================================
class DiscretizationMethod(ABC):
    """Abstract base class for discretization strategies."""

    @abstractmethod
    def discretize(self, state_idx: int, h_var: str = 'h') -> str:
        pass

    @abstractmethod
    def discretize_dot(self, state_idx: int, h_var: str = 'h', seeds_var: str = 'seeds') -> str:
        pass


class TrapezoidalMethod(DiscretizationMethod):
    def discretize(self, state_idx: int, h_var: str = 'h') -> str:
        return f"((2.0/{h_var}) * (states[{state_idx}] - history[{state_idx}]) - d_history[{state_idx}])"

    def discretize_dot(self, state_idx: int, h_var: str = 'h', seeds_var: str = 'seeds') -> str:
        return f"((2.0/{h_var}) * ({seeds_var}[{state_idx}]))"


class BackwardEulerMethod(DiscretizationMethod):
    def discretize(self, state_idx: int, h_var: str = 'h') -> str:
        return f"((states[{state_idx}] - history[{state_idx}]) / {h_var})"

    def discretize_dot(self, state_idx: int, h_var: str = 'h', seeds_var: str = 'seeds') -> str:
        return f"(({seeds_var}[{state_idx}]) / {h_var})"


class BDF2Method(DiscretizationMethod):
    def discretize(self, state_idx: int, h_var: str = 'h') -> str:
        return f"((1.5*states[{state_idx}] - 2.0*history[{state_idx}] + 0.5*history2[{state_idx}]) / {h_var})"

    def discretize_dot(self, state_idx: int, h_var: str = 'h', seeds_var: str = 'seeds') -> str:
        return f"((1.5*{seeds_var}[{state_idx}]) / {h_var})"

class ContinuousMethod(DiscretizationMethod):
    """Strategy for continuous systems (RMS Small Signal). Does not discretize."""
    def discretize(self, state_idx: int, h_var: str = 'h') -> str:
        return f"dx[{state_idx}]"

    def discretize_dot(self, state_idx: int, h_var: str = 'h', seeds_var: str = 'seeds') -> str:
        return "0.0"

# ==============================================================================
# 2. CSE (Common Subexpression Elimination) Analyzer (large systems)
# ==============================================================================
class SubexpressionAnalyzer:
    """
    Find and catalog subexpressions that appear multiple times.
    OPTIMIZED: Uses memoization for complexity calc and string generation.
    """
    __slots__ = ['threshold', 'expr_counts', 'expr_objects', 'expr_complexity', 'memo_complexity', 'memo_canonical',
                 'visited_traversal']

    def __init__(self, threshold: int = 2)-> None:
        self.threshold: int = threshold
        self.expr_counts: Dict[str, int] = dict()
        self.expr_objects: Dict[str, Expr] = dict()
        self.expr_complexity: Dict[str, int] = dict()

        # Caches
        self.memo_complexity: Dict[int, int] = dict()
        self.memo_canonical: Dict[int, str] = dict()
        self.visited_traversal: Set[int] = set()

    def analyze(self, equations: List[Expr]) -> Dict[str, str]:
        # Reset caches
        self.expr_counts.clear()
        self.expr_objects.clear()
        self.expr_complexity.clear()
        self.memo_complexity.clear()
        self.memo_canonical.clear()

        self.visited_traversal.clear()

        for eq in equations:
            self._count_subexpressions(eq)

        candidates: List[Tuple[int, str]] = list()
        for expr_hash, count in self.expr_counts.items():
            if count >= self.threshold:
                complexity = self.expr_complexity[expr_hash]
                benefit = count * complexity
                candidates.append((benefit, expr_hash))

        candidates.sort(reverse=True)
        temp_vars: Dict[str, str] = dict()
        for i, (_, expr_hash) in enumerate(candidates):
            temp_vars[expr_hash] = f"_t{i}"
        return temp_vars

    def _count_subexpressions(self, node: Expr)->None:
        if isinstance(node, (Const, Var)):
            return

        complexity = self._calculate_complexity(node)

        if complexity > 1:
            expr_hash = self.hash_expr(node)
            self.expr_counts[expr_hash] = self.expr_counts.get(expr_hash, 0) + 1
            self.expr_objects[expr_hash] = node
            self.expr_complexity[expr_hash] = complexity
        else:
            pass

        if id(node) in self.visited_traversal:
            return
        self.visited_traversal.add(id(node))

        if isinstance(node, BinOp):
            self._count_subexpressions(node.left)
            self._count_subexpressions(node.right)
        elif isinstance(node, UnOp):
            self._count_subexpressions(node.operand)
        elif isinstance(node, Func):
            self._count_subexpressions(node.arg)

    def _calculate_complexity(self, node: Expr) -> int:
        if id(node) in self.memo_complexity:
            return self.memo_complexity[id(node)]

        res: int
        if isinstance(node, (Const, Var)):
            res = 0
        elif isinstance(node, BinOp):
            op_cost = 2 if node.op in ['*', '/', '**'] else 1
            res = op_cost + self._calculate_complexity(node.left) + \
                  self._calculate_complexity(node.right)
        elif isinstance(node, UnOp):
            res = 1 + self._calculate_complexity(node.operand)
        elif isinstance(node, Func):
            res = 5 + self._calculate_complexity(node.arg)
        else:
            res = 1

        self.memo_complexity[id(node)] = res
        return res

    def hash_expr(self, node: Expr) -> str:
        canonical = self._expr_to_canonical_string(node)
        return hashlib.md5(canonical.encode()).hexdigest()[:12]

    def _expr_to_canonical_string(self, node: Expr) -> str:
        if id(node) in self.memo_canonical:
            return self.memo_canonical[id(node)]

        res: str
        if isinstance(node, Const):
            res = f"C{node.value}"
        elif isinstance(node, Var):
            if node.base_var is not None:
                res = f"D{node.base_var.name}"
            else:
                res = f"V{node.name}"
        elif isinstance(node, BinOp):
            left = self._expr_to_canonical_string(node.left)
            right = self._expr_to_canonical_string(node.right)
            if node.op in ['+', '*']:
                if left > right:
                    left, right = right, left
                else:
                    pass
            else:
                pass
            res = f"({left}{node.op}{right})"
        elif isinstance(node, UnOp):
            operand = self._expr_to_canonical_string(node.operand)
            res = f"{node.op}{operand}"
        elif isinstance(node, Func):
            res = f"{node.op}({self._expr_to_canonical_string(node.arg)})"
        else:
            res = str(node)

        self.memo_canonical[id(node)] = res
        return res


# ==============================================================================
# 3. Conversion to string based on visitor pattern (sequentiality)
# ==============================================================================

class SymbolicToPythonVisitor:
    __slots__ = ['var_map', 'param_map', 'method', 'cse_map', 'analyzer', 'in_cse_def', '_str_cache']

    OP_PRECEDENCE = {'+': 10, '-': 10, '*': 20, '/': 20, '**': 30}

    def __init__(self, var_map: Dict[int, int], param_map: Dict[int, int], method: DiscretizationMethod):
        self.var_map = var_map
        self.param_map = param_map or dict()
        self.method = method
        self.cse_map: Dict[str, str] = dict()
        self.analyzer = None
        self.in_cse_def = False
        self._str_cache: Dict[Tuple[int, int], str] = dict()

    def _prec(self, node) -> int:
        """Return precedence of a node. Non-operators get 'infinite' precedence."""
        # BinOp nodes define precedence; everything else we treat as atomic.
        if isinstance(node, BinOp):
            return self.OP_PRECEDENCE.get(node.op, 0)
        return 10 ** 9

    def _maybe_parenthesize(self, code: str, child_node, parent_op: str, parent_prec: int, side: str) -> str:
        """
        Decide whether to wrap child expression in parentheses.

        Rules:
          - If child's precedence < parent's precedence => need parentheses.
          - If child's precedence == parent's precedence:
              * For non-associative ops (-, /): right child must be parenthesized.
              * For exponent (**), which is right-associative: left child must be parenthesized when equal precedence.
              * For associative ops (+, *): no parentheses needed.
        """
        child_prec = self._prec(child_node)

        # Lower precedence always needs parentheses
        if child_prec < parent_prec:
            return f"({code})"

        # Equal precedence: depends on operator and side
        if child_prec == parent_prec:
            if parent_op in ('-', '/'):
                # a - (b - c) and a / (b / c) must keep parentheses on right
                if side == 'right':
                    return f"({code})"
            if parent_op == '**':
                # (a ** b) ** c must keep parentheses on left (since ** is right-associative)
                if side == 'left':
                    return f"({code})"
            # + and * are associative enough here -> no parentheses
        return code

    def visit(self, node: Expr, precedence: int = 0) -> str:
        """
        Dispatches node processing using explicit type matching to avoid reflection.

        :param node: The symbolic expression node to visit.
        :type node: Expr
        :param precedence: Operator precedence level.
        :type precedence: int
        :return: Python code string representation of the node.
        :rtype: str
        """
        # 1. CSE (Common Subexpression Elimination) Check
        if self.analyzer is not None and self.cse_map is not None and not self.in_cse_def:
            if not isinstance(node, (Var, Const)):
                h: str = self.analyzer.hash_expr(node)
                if h in self.cse_map:
                    return self.cse_map[h]
                else:
                    pass
            else:
                pass
        else:
            pass

        # 2. Cache Check
        cache_key: Tuple[int, int] = (id(node), precedence)
        if cache_key in self._str_cache:
            return self._str_cache[cache_key]
        else:
            pass

        result: str = ""

        match node:
            case BinOp():
                result = self.visit_binop(node, precedence)
            case UnOp():
                result = self.visit_unop(node, precedence)
            case Const():
                result = self.visit_const(node, precedence)
            case Var():
                result = self.visit_var(node, precedence)
            case Func():
                result = self.visit_func(node, precedence)
            case _:
                result = self.generic_visit(node, precedence)

        # 5. Store and Return
        self._str_cache[cache_key] = result
        return result

    def generic_visit(self, node: Expr, _: int) -> str:
        raise NotImplementedError(f"Node not supported: {type(node)}")

    # def visit_binop(self, node: BinOp, prec: int) -> str:
    #     curr_prec = self.OP_PRECEDENCE.get(node.op, 0)
    #     l = self.visit(node.left, curr_prec)
    #     r = self.visit(node.right, curr_prec)
    #     code = f"{l} {node.op} {r}"
    #     return f"({code})" if curr_prec < prec else code

    def visit_binop(self, node: 'BinOp', prec: int) -> str:
        """
        Emit Python code for a binary operation with correct parentheses.

        Important:
        - We do NOT just compare prec numerically in a naive way; we also handle
          associativity for '-', '/', and '**' to avoid sign/structure bugs.
        """
        op = node.op
        curr_prec = self.OP_PRECEDENCE.get(op, 0)

        # Visit children using current operator precedence as the "context"
        l_code = self.visit(node.left, curr_prec)
        r_code = self.visit(node.right, curr_prec)

        # Parenthesize children if needed (precedence + associativity)
        l_code = self._maybe_parenthesize(l_code, node.left, op, curr_prec, side='left')
        r_code = self._maybe_parenthesize(r_code, node.right, op, curr_prec, side='right')

        code = f"{l_code} {op} {r_code}"

        # If parent context has higher precedence, wrap the whole expression
        return f"({code})" if curr_prec < prec else code

    def visit_unop(self, node: UnOp, _) -> str:
        return f"{node.op}{self.visit(node.operand, 100)}"

    def visit_const(self, node: Const, _) -> str:
        return str(node.value)

    def visit_var(self, node: Var, prec: int) -> str:
        if node.uid in self.var_map:
            return f"states[{self.var_map[node.uid]}]"
        else:
            pass

        if node.uid in self.param_map:
            return f"params[{self.param_map[node.uid]}]"
        else:
            pass

        if node.base_var is not None:
            return self.visit_diffvar(node, prec)
        else:
            pass

        if node.name == 'h':
            return 'h'

        raise ValueError(f"Variable '{node.name}' (UID: {node.uid}) Not mapped in compiler.")

    def visit_diffvar(self, node: Var, prec: int) -> str:
        # If base_var is also a DiffVar, recursively discretize it
        if node.base_var.base_var is not None:
            # Recursively get discretized base (e.g., dx from x)
            base_discretized = self.visit_diffvar(node.base_var, prec)
            # Apply discretization to the discretized base using d_history
            # For Backward Euler: d2x = (dx - dx_history) / h
            # Use base_var's origin since base_var is itself a DiffVar
            base_idx = self.var_map[node.base_var.origin_var.uid]
            term = f"(({base_discretized} - d_history[{base_idx}]) / h)"
        else:
            # Base is a regular state variable
            base_uid = node.base_var.uid
            if base_uid not in self.var_map:
                raise ValueError(f"Base var '{node.base_var.name}' (UID: {base_uid})"
                                 f" for DiffVar does not exist in states.")
            term = self.method.discretize(self.var_map[base_uid])
        return f"({term})" if prec > 10 else term

    def visit_func(self, node: Func, _) -> str:
        arg = self.visit(node.arg, 0)

        op = node.op
        if op == 'heaviside':
            return f"_heaviside({arg})"
        if op == 'abs':
            return f"np.abs({arg})"

        return f"np.{op}({arg})"

# =============================================================================================
# 4. Solution for large-scale algebraic frameworks, based on differential automatic composition
# =============================================================================================

class ADVisitor(SymbolicToPythonVisitor):
    __slots__ = ['seeds_var', 'active_indices']

    def __init__(self, var_map: Dict[int, int], param_map: Dict[int, int],
                 method: DiscretizationMethod, seeds_var: str = 'seeds',
                 active_indices: set | None = None):
        super().__init__(var_map, param_map, method)
        self.seeds_var = seeds_var
        self.active_indices = active_indices
        self._str_cache: Dict[Tuple[int, int], Tuple[str, str]] = dict()

    def generic_visit(self, node: Expr, _: int) -> Tuple[str, str]:
        raise NotImplementedError(f"Node not supported in AD: {type(node)}")

    def visit(self, node: Expr, precedence: int = 0) -> Tuple[str, str]:
        """
        Dispatches node processing for Automatic Differentiation using explicit type matching.
        """
        # 1. CSE Check
        if self.analyzer is not None and self.cse_map is not None and not self.in_cse_def:
            if not isinstance(node, (Var, Const)):
                h_hash: str = self.analyzer.hash_expr(node)
                if h_hash in self.cse_map:
                    return self.cse_map[h_hash], f"{self.cse_map[h_hash]}_d"
                else:
                    pass
            else:
                pass
        else:
            pass

        # 2. Cache Check (Critical for AD speed)
        cache_key: Tuple[int, int] = (id(node), precedence)
        if cache_key in self._str_cache:
            return self._str_cache[cache_key]
        else:
            pass

        res: Tuple[str, str] = ("", "")

        match node:
            case BinOp():
                res = self.visit_binop(node, precedence)
            case UnOp():
                res = self.visit_unop(node, precedence)
            case Const():
                res = self.visit_const(node, precedence)
            case Var():
                res = self.visit_var(node, precedence)
            case Func():
                res = self.visit_func(node, precedence)
            case _:
                # Fallback for generic or unsupported nodes
                res = self.generic_visit(node, precedence)

        # 5. Store and Return
        self._str_cache[cache_key] = res
        return res

    def visit_const(self, node: Const, _: int) -> Tuple[str, str]:
        return str(node.value), "0.0"

    def visit_var(self, node: Var, _) -> Tuple[str, str]:
        # 1. Standard mapping for states
        if node.uid in self.var_map:
            i: int = self.var_map[node.uid]
            val: str = f"states[{i}]"

            # Seed value for the specific column being differentiated
            if self.active_indices is not None:
                seed_val: str = "1.0" if i in self.active_indices else "0.0"
            else:
                seed_val: str = f"{self.seeds_var}[{i}]"
            return val, seed_val
        else:
            pass

        # 2. Parameter mapping (Parameters have a seed of 0.0)
        if node.uid in self.param_map:
            return f"params[{self.param_map[node.uid]}]", "0.0"
        else:
            pass

        if node.base_var is not None:
            return self.visit_diffvar(node, 100)
        else:
            pass

        raise ValueError(f"Var '{node.name}' (UID: {node.uid}) Not mapped in ADVisitor.")

    def visit_diffvar(self, node: Var, prec: int) -> Tuple[str, str]:
        # If base_var is also a DiffVar, recursively discretize it
        if node.base_var.base_var is not None:
            # Recursively get discretized base (value, dot)
            base_val, base_dot = self.visit_diffvar(node.base_var, prec)
            # Use base_var's origin since base_var is itself a DiffVar
            base_idx = self.var_map[node.base_var.origin_var.uid]
            
            if isinstance(self.method, BackwardEulerMethod):
                # d2x = (dx - dx_history) / h
                val = f"(({base_val} - d_history[{base_idx}]) / h)"
                dot = "0.0" if base_dot == "0.0" else f"({base_dot}/h)"
            elif isinstance(self.method, TrapezoidalMethod):
                # d2x = (2/h)*(dx - dx_history) - d2x_history
                val = f"((2.0/h)*({base_val} - d_history[{base_idx}]) - d2_history[{base_idx}])"
                dot = "0.0" if base_dot == "0.0" else f"(2.0*{base_dot}/h)"
            elif isinstance(self.method, BDF2Method):
                # Not implemented for nested diff vars with BDF2
                raise NotImplementedError("Nested DiffVar not supported with BDF2")
            else:
                raise NotImplementedError
        else:
            # Base is a regular state variable
            base_uid = node.base_var.uid
            i = self.var_map[base_uid]
            if self.active_indices is not None:
                seed = "1.0" if i in self.active_indices else "0.0"
            else:
                seed = f"{self.seeds_var}[{i}]"

            if isinstance(self.method, BackwardEulerMethod):
                val = f"((states[{i}] - history[{i}]) / h)"
                dot = "0.0" if seed == "0.0" else ("(1.0/h)" if seed == "1.0" else f"({seed}/h)")
            elif isinstance(self.method, TrapezoidalMethod):
                val = f"((2.0/h)*(states[{i}] - history[{i}]) - d_history[{i}])"
                dot = "0.0" if seed == "0.0" else ("(2.0/h)" if seed == "1.0" else f"(2.0*{seed}/h)")
            elif isinstance(self.method, BDF2Method):
                val = f"((1.5*states[{i}] - 2.0*history[{i}] + 0.5*history2[{i}]) / h)"
                dot = "0.0" if seed == "0.0" else ("(1.5/h)" if seed == "1.0" else f"(1.5*{seed}/h)")
            else:
                raise NotImplementedError
        
        return (f"({val})", f"({dot})") if prec > 10 else (val, dot)

    def visit_binop(self, node: BinOp, prec: int) -> Tuple[str, str]:
        curr_prec = self.OP_PRECEDENCE.get(node.op, 0)
        lv, ld = self.visit(node.left, curr_prec)
        rv, rd = self.visit(node.right, curr_prec)
        op = node.op

        v = ""
        if op == '+':
            v = rv if _is_zero(lv) else (lv if _is_zero(rv) else f"{lv} + {rv}")
        elif op == '-':
            v = lv if _is_zero(rv) else (f"-{rv}" if _is_zero(lv) else f"{lv} - {rv}")
        elif op == '*':
            v = "0.0" if (_is_zero(lv) or _is_zero(rv)) else (
                rv if _is_one(lv) else (lv if _is_one(rv) else f"{lv} * {rv}"))
        elif op == '/':
            v = "0.0" if _is_zero(lv) else (lv if _is_one(rv) else f"{lv} / {rv}")
        elif op == '**':
            v = "1.0" if _is_zero(rv) else (lv if _is_one(rv) else (
                f"({lv})**({node.right.value})" if isinstance(node.right, Const) else f"({lv})**({rv})"))

        d = "0.0"
        if op == '+':
            d = rd if _is_zero(ld) else (ld if _is_zero(rd) else f"({ld} + {rd})")
        elif op == '-':
            d = f"(-{rd})" if _is_zero(ld) else (ld if _is_zero(rd) else f"({ld} - {rd})")
        elif op == '*':
            t1 = "0.0"
            if not _is_zero(ld): t1 = rv if _is_one(ld) else (ld if _is_one(rv) else f"({ld})*({rv})")
            t2 = "0.0"
            if not _is_zero(rd): t2 = lv if _is_one(rd) else (rd if _is_one(lv) else f"({lv})*({rd})")
            d = t2 if t1 == "0.0" else (t1 if t2 == "0.0" else f"({t1} + {t2})")
        elif op == '/':
            if _is_zero(ld) and _is_zero(rd):
                d = "0.0"
            elif _is_zero(rd):
                d = ld if _is_one(rv) else f"({ld}) / ({rv})"
            else:
                d = f"(({ld})*({rv}) - ({lv})*({rd})) / (({rv})*({rv}))"
        elif op == '**':
            if not (_is_zero(ld) and _is_zero(rd)):
                if isinstance(node.right, Const):
                    val = float(node.right.value)
                    if val == 1.0:
                        d = ld
                    elif val == 2.0:
                        d = f"2.0*({lv})*({ld})"
                    else:
                        d = f"({val})*(({lv})**({val - 1}))*({ld})"
                else:
                    d = f"(({v}) * ( ({rd})*np.log({lv}) + ({rv})*({ld})/({lv}) ))"

        return (f"({v})", f"({d})") if curr_prec < prec else (v, d)

    def visit_unop(self, node: UnOp, _: int) -> Tuple[str, str]:
        ov, od = self.visit(node.operand, 100)
        if _is_zero(od):
            s = f"{node.op}({ov})"
            if node.op == '+': s = ov
            return s, "0.0"
        if node.op == '+': return f"(+({ov}))", f"(+({od}))"
        if node.op == '-': return f"(-({ov}))", f"(-({od}))"
        raise NotImplementedError

    def visit_func(self, node: Func, _: int) -> Tuple[str, str]:
        av, ad = self.visit(node.arg, 0)
        if _is_zero(ad):
            if node.op == 'heaviside': return f"_heaviside({av})", "0.0"
            if node.op == 'abs': return f"np.abs({av})", "0.0"
            return f"np.{node.op}({av})", "0.0"

        if node.op == 'heaviside': return f"_heaviside({av})", "0.0"
        if node.op == 'abs': return f"np.abs({av})", f"(np.sign({av})*({ad}))"
        if node.op == 'sin': return f"np.sin({av})", f"(np.cos({av})*({ad}))"
        if node.op == 'cos': return f"np.cos({av})", f"(-np.sin({av})*({ad}))"
        if node.op == 'exp': return f"np.exp({av})", f"({f'np.exp({av})'})*({ad})"
        if node.op == 'log': return f"np.log({av})", f"({ad})/({av})"
        if node.op == 'sqrt': return f"np.sqrt({av})", f"0.5*({ad})/({f'np.sqrt({av})'})"
        raise NotImplementedError

# ==============================================================================
# 5. Compiler (sym-num)(discretized)
# ==============================================================================

class EquationCompiler:
    """Main interface for compiling symbolic equations into executable functions."""

    __slots__ = ['variables_objs', 'parameters_objs', 'strategy', 'var_map', 'param_map', 'visitor']

    METHODS = {
        DynamicIntegrationMethod.DaeTrapezoidal: TrapezoidalMethod(),
        DynamicIntegrationMethod.DaeBackEuler: BackwardEulerMethod(),
        DynamicIntegrationMethod.DaeBDF2: BDF2Method(),
        DynamicIntegrationMethod.DaeContinuous: ContinuousMethod()
    }

    def __init__(self,
                 variables: List[Var],
                 parameters: List[Var] = None,
                 method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal):
        self.variables_objs = variables
        self.parameters_objs = parameters if parameters is not None else list()

        if method not in self.METHODS:
            raise ValueError(f"Method '{method}' Unknown. Options: {list(self.METHODS.keys())}")

        self.strategy = self.METHODS[method]

        self.var_map = {v.uid: i for i, v in enumerate(self.variables_objs)}
        self.param_map = {p.uid: i for i, p in enumerate(self.parameters_objs)}

        self.visitor = SymbolicToPythonVisitor(self.var_map, self.param_map, self.strategy)

    def compile(self, equations: List[Expr], func_name: str = "step_fn", use_cse: bool = True,
                offset: int = 0, inplace: bool = False) -> Callable:

        lines: List[str] = list()
        # Header depends on mode
        if inplace:
            lines.append(f"def {func_name}(states, params, history, d_history, h, residuals, history2=None):")
        else:
            lines.append(f"def {func_name}(states, params, history, d_history, h, history2=None):")

        # --- CSE Block ---
        if use_cse:
            analyzer = SubexpressionAnalyzer()
            cse_map = analyzer.analyze(equations)
            self.visitor.analyzer = analyzer
            self.visitor.cse_map = cse_map
            self.visitor._str_cache = dict()

            if cse_map:
                sorted_cse = sorted(cse_map.items(), key=lambda x: int(x[1][2:]))
                for expr_hash, var_name in sorted_cse:
                    expr_obj = analyzer.expr_objects[expr_hash]
                    self.visitor.in_cse_def = True
                    expr_code = self.visitor.visit(expr_obj)
                    self.visitor.in_cse_def = False
                    lines.append(f"    {var_name} = {expr_code}")
            else:
                pass
        else:
            pass

        # --- Body ---
        if not inplace:
            lines.append(f"    residuals = np.zeros({len(equations)}, dtype=np.float64)")
        else:
            pass

        for i, eq in enumerate(equations):
            code = self.visitor.visit(eq)
            # Apply offset if inplace
            target_idx = i + offset if inplace else i
            lines.append(f"    residuals[{target_idx}] = {code}")

        if not inplace:
            lines.append("    return residuals")
        else:
            pass

        # Clean visitor
        self.visitor.cse_map = dict()
        self.visitor.analyzer = None
        self.visitor._str_cache = dict()

        full_source = "\n".join(lines)

        return _compile_to_file(full_source, func_name)

    def compile_ad_kernel(self, equations: List[Expr], func_name: str = "ad_step", use_cse: bool = True,
                          active_indices: set | None = None) -> Callable:

        adv = ADVisitor(self.var_map, self.param_map, self.strategy, seeds_var='seeds', active_indices=active_indices)

        lines: List[str] = list()
        lines.append(f"def {func_name}(states, seeds, params, history, d_history, h, history2=None):")

        if use_cse:
            analyzer = SubexpressionAnalyzer()
            cse_map = analyzer.analyze(equations)
            adv.analyzer = analyzer
            adv.cse_map = cse_map
            adv._str_cache = dict()

            if cse_map:
                sorted_cse = sorted(cse_map.items(), key=lambda x: int(x[1][2:]))
                for expr_hash, var_name in sorted_cse:
                    expr_obj = analyzer.expr_objects[expr_hash]
                    adv.in_cse_def = True
                    expr_val, expr_dot = adv.visit(expr_obj)
                    adv.in_cse_def = False

                    lines.append(f"    {var_name} = {expr_val}")

                    if expr_dot != "0.0":
                        lines.append(f"    {var_name}_d = {expr_dot}")
                    else:
                        pass
            else:
                pass
        else:
            pass

        n: int = len(equations)  # RULE: Local type hint
        lines.append(f"    jvp = np.zeros({n}, dtype=np.float64)")

        for i, eq in enumerate(equations):
            val, dot = adv.visit(eq)
            if dot != "0.0":
                lines.append(f"    jvp[{i}] = {dot}")
            else:
                pass

        lines.append("    return jvp")

        adv.cse_map = dict()
        adv.analyzer = None
        adv._str_cache = dict()

        full_source: str = "\n".join(lines)

        return _compile_to_file(full_source, func_name)


# ==============================================================================
# 6. Matrix Vectorized Compiler (HPC Optimized - No Dictionaries)
# ==============================================================================

class MatrixVectorizedVisitor(SymbolicToPythonVisitor):
    """
    HPC-optimized visitor. Instead of performing dictionary lookups (slow),
    it accesses state variable indices directly from a mapping matrix (fast).
    Generates code such as: states[indices[:, 5]]
    """
    __slots__ = ['col_map']

    def __init__(self, var_map, param_map, method, col_map):
        super().__init__(var_map, param_map, method)
        self.col_map = col_map  # Maps variable_name -> column_index (int)

    def visit_var(self, node: Var, _) -> str:
        if node.uid in self.param_map:
            return f"params[{self.param_map[node.uid]}]"
        else:
            pass

        if node.uid in self.var_map:
            col_idx = self.col_map[node.name]
            return f"states[indices[:, {col_idx}]]"
        else:
            pass

        # EMT Support: If the node is a derivative, call visit_diffvar
        if node.base_var is not None:
            return self.visit_diffvar(node, 100)
        else:
            pass

        raise ValueError(f"Var '{node.name}' (UID: {node.uid}) Not mapped in matrix visitor.")

    def visit_diffvar(self, node: Var, prec: int) -> str:
        # If base_var is also a DiffVar, recursively discretize it
        if node.base_var.base_var is not None:
            # Use base_var's origin for history lookup since base_var is a DiffVar
            base_origin_name = node.base_var.origin_var.name
            col_idx = self.col_map[base_origin_name]
            idx_access = f"indices[:, {col_idx}]"
            
            # Recursively get discretized base
            base_discretized = self.visit_diffvar(node.base_var, prec)
            # Apply discretization using d_history
            if isinstance(self.method, BackwardEulerMethod):
                term = f"(({base_discretized} - d_history[{idx_access}]) / h)"
            elif isinstance(self.method, TrapezoidalMethod):
                term = f"((2.0/h)*({base_discretized} - d_history[{idx_access}]) - d2_history[{idx_access}])"
            else:
                raise NotImplementedError(f"Nested DiffVar not supported with {type(self.method)}")
        else:
            # Base is a regular state variable - use standard discretization
            # Get origin variable name for column mapping
            origin_name = node.origin_var.name
            col_idx = self.col_map[origin_name]
            idx_access = f"indices[:, {col_idx}]"
            
            if isinstance(self.method, TrapezoidalMethod):
                term = f"((2.0/h) * (states[{idx_access}] - history[{idx_access}]) - d_history[{idx_access}])"
            elif isinstance(self.method, BackwardEulerMethod):
                term = f"((states[{idx_access}] - history[{idx_access}]) / h)"
            elif isinstance(self.method, BDF2Method):
                term = f"((1.5*states[{idx_access}] - 2.0*history[{idx_access}] + 0.5*history2[{idx_access}]) / h)"
            else:
                raise NotImplementedError(f"Method {type(self.method)} not supported in matrix vectorization.")

        return f"({term})" if prec > 10 else term


class MatrixVectorizedCompiler(EquationCompiler):
    """
    Compiler utilizing the Matrix Vectorized Visitor.
    Generates kernels that accept 'indices' as a 2D int32 array for batch processing.
    """
    __slots__ = []

    def compile_matrix_kernel(self, template_eq: Expr, func_name: str, template_vars: List[Var]) -> Callable:
        # 1. Create a deterministic column map (Var index within the kernel)
        col_map: Dict[str, int] = dict()
        for i, v in enumerate(template_vars):
            name = v.base_var.name if v.base_var is not None else v.name
            col_map[name] = i

        # 2. Generate source code using the Matrix Visitor
        visitor = MatrixVectorizedVisitor(self.var_map, self.param_map, self.strategy, col_map)
        rhs_code = visitor.visit(template_eq)

        # 3. Package into a function (indices is now a 2D int32 array)
        lines: List[str] = list()
        lines.append(f"def {func_name}(states, params, history, d_history, h, indices, history2=None):")
        lines.append(f"    # Vectorized Matrix Kernel (No Dicts)")
        lines.append(f"    residuals = {rhs_code}")
        lines.append(f"    return residuals")
        full_source = "\n".join(lines)

        # 4. Compile to file (enabling Numba's persistent cache)
        return _compile_to_file(full_source, func_name)

# ==============================================================================
# 7. RMS Native Compiler (Continuous Time & Sparse Jacobians)
# ==============================================================================
class RMSCompiler(EquationCompiler):
    """
    O(N) compiler for RMS (Root Mean Square) Continuous-Time Simulations.

    This compiler generates highly optimized Right-Hand Side (RHS) vectors and
    Sparse Jacobian matrices using a structural analysis approach. By leveraging
    the official `expression2numba` translator, it ensures 100% mathematical
    consistency with legacy systems while drastically reducing symbolic evaluation
    and compilation times.
    """
    __slots__ = ['dt_var', 'compiler_names_dict', 'diff_vars', 'v_params']

    def __init__(self,
                 variables: List[Var],
                 diff_vars: List[Var],
                 v_params: List[Var],
                 c_params: List[Var],
                 dt_var: Var,
                 compiler_names_dict: Dict[int, str]):
        """
        Initializes the RMS Compiler with the system's mathematical components.

        Args:
            variables (List[Var]): State and algebraic variables of the system.
            diff_vars (List[Var]): Differential variables (dx/dt).
            v_params (List[Var]): Variable (event-driven) parameters.
            c_params (List[Var]): Constant parameters.
            dt_var (Var): The symbolic variable representing the integration time step.
            compiler_names_dict (Dict[int, str]): Dictionary mapping variable UIDs to
                                                  their executable string representations.
        """
        super().__init__(variables=variables, parameters=c_params, method=DynamicIntegrationMethod.DaeBackEuler)
        self.dt_var = dt_var
        self.compiler_names_dict = compiler_names_dict
        self.diff_vars = diff_vars
        self.v_params = v_params

    def compile_rhs(self, equations: List[Expr], func_name: str) -> Callable:
        """
        Compiles the residual equations (RHS) into a fast, executable JIT function.

        Args:
            equations (List[Expr]): The list of symbolic expressions to evaluate.
            func_name (str): The desired name for the compiled target function.

        Returns:
            Callable: An executable function computing the RHS residuals.
        """
        # Use the exact array names expected by the legacy solver interface: vars, diff, vprms, cprms
        lines: List[str] = list()
        lines.append(f"def {func_name}(vars, diff, vprms, cprms):")
        lines.append(f"    out = np.zeros({len(equations)}, dtype=np.float64)")

        for i, eq in enumerate(equations):
            expr_str = expression2numba(eq, self.compiler_names_dict)
            lines.append(f"    out[{i}] = {expr_str}")

        lines.append("    return out")

        return _compile_to_file("\n".join(lines), func_name)

    def compile_sparse_jacobian(self, eqs: List[Expr], wrt_vars: List[Var], func_name: str) -> Callable:
        """
        Compiles a sparse Jacobian evaluator using an O(N) structural extraction algorithm.

        Args:
            eqs (List[Expr]): The list of symbolic equations (F or G).
            wrt_vars (List[Var]): The variables to differentiate with respect to (x or y).
            func_name (str): The desired name for the compiled target function.

        Returns:
            Callable: A function that populates and returns a scipy.sparse.csc_matrix.
        """
        triplets: List[Tuple[int, int, Expr]] = list()

        # O(N) Algorithmic Extraction:
        # We check ALL variable-equation pairs to correctly handle chain rules
        # through differential variables. This is less efficient than checking only
        # variables that appear in each equation, but it ensures correctness.
        for row, eq in enumerate(eqs):
            for col, var in enumerate(wrt_vars):
                # Differentiate with respect to the physical time variable (dt_var)
                d_expr = eq.diff(var, dt=self.dt_var)

                if not (isinstance(d_expr, Const) and d_expr.value == 0):
                    triplets.append((col, row, d_expr))
                else:
                    pass

        triplets.sort(key=lambda t: (t[0], t[1]))

        # Handle edge case: Empty Jacobian matrix (no dependencies found)
        if not triplets:
            J_empty = sp.csc_matrix((len(eqs), len(wrt_vars)))
            # noinspection PyShadowingBuiltins
            return lambda vars, diff, vprms, cprms, h: J_empty
        else:
            pass

        # Extract sorted coordinates and corresponding symbolic derivatives
        cols_sorted = [t[0] for t in triplets]
        rows_sorted = [t[1] for t in triplets]
        d_exprs = [t[2] for t in triplets]

        # Precompute CSC (Compressed Sparse Column) pointer arrays
        nnz = len(cols_sorted)
        indices = np.fromiter(rows_sorted, dtype=np.int32, count=nnz)
        indptr = np.zeros(len(wrt_vars) + 1, dtype=np.int32)
        for c in cols_sorted:
            indptr[c + 1] += 1
        np.cumsum(indptr, out=indptr)

        # Initialize the sparse matrix template
        J_template = sp.csc_matrix((np.zeros(nnz), indices, indptr), shape=(len(eqs), len(wrt_vars)))

        # The Jacobian receives 'h' in its signature for solver compatibility,
        # even though 'expression2numba' internally resolves 'dt' via vprms[...]
        lines = [f"def {func_name}_filler(vars, diff, vprms, cprms, h, data_out):"]
        for i, expr in enumerate(d_exprs):
            expr_str = expression2numba(expr, self.compiler_names_dict)
            lines.append(f"    data_out[{i}] = {expr_str}")

        filler_fn = _compile_to_file("\n".join(lines), f"{func_name}_filler")

        # Wrapper function to evaluate and return the actual CSC matrix natively
        # noinspection PyShadowingBuiltins
        def jac_evaluator(vars, diff, vprms, cprms, h):
            filler_fn(vars, diff, vprms, cprms, h, J_template.data)
            return J_template

        return jac_evaluator