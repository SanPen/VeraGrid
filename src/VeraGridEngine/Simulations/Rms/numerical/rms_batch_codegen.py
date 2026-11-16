# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Emit scalar RMS DAG operations once before compiling each bounded batch."""

import hashlib
from typing import Any

from VeraGridEngine.Utils.Symbolic.jit_compiler_rms_numba_comp import (
    EagerKernelKind, RmsEagerEquationCompiler, RmsResidualVisitor, RmsAdVisitor,
    _compile_to_file, _is_zero,
)
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Expr, Func, Func2, UnOp


class BatchResidualVisitor(RmsResidualVisitor):
    """Reuse already emitted children while preserving existing RMS operators."""

    __slots__ = ("materialized",)

    def __init__(self, compiler: RmsEagerEquationCompiler) -> None:
        """Bind the original global scalar inputs.

        :param compiler: Global variable, derivative and parameter slot owner.
        :return: None.
        """
        super().__init__(compiler.var_map, compiler.param_map, compiler.strategy, compiler.diff_vars_objs)
        self.materialized: dict[int, str] = dict()

    def visit(self, node: Expr, precedence: int = 0) -> str:
        """Resolve a prepared temporary before recursing into an expression.

        :param node: Existing expression node.
        :param precedence: Parent operation precedence.
        :return: Temporary name or unchanged scalar code.
        """
        prepared: str | None = self.materialized.get(id(node), None)
        if prepared is not None:
            return prepared
        else:
            return super().visit(node, precedence)


class BatchAdVisitor(RmsAdVisitor):
    """Reuse child values and tangents without expanding limiter derivatives."""

    __slots__ = ("materialized",)

    def __init__(self, compiler: RmsEagerEquationCompiler) -> None:
        """Bind unchanged RMS derivative values and their Backward Euler tangents.

        :param compiler: Global input slot owner.
        :return: None.
        """
        super().__init__(compiler.var_map, compiler.param_map, compiler.strategy,
                         compiler.diff_vars_objs, None,
                         independent_derivatives=compiler.independent_derivatives)
        self.materialized: dict[int, tuple[str, str]] = dict()

    def visit(self, node: Expr, precedence: int = 0) -> tuple[str, str]:
        """Resolve both prepared child quantities before applying the existing rule.

        :param node: Existing expression node.
        :param precedence: Parent operation precedence.
        :return: Value and directional derivative code.
        """
        prepared: tuple[str, str] | None = self.materialized.get(id(node), None)
        if prepared is not None:
            return prepared
        else:
            return super().visit(node, precedence)


def compile_batch_pair(compiler: RmsEagerEquationCompiler, equations: list[Expr],
                        offset: int) -> tuple[Any, Any, Any, Any]:
    """Generate linear-size value/JVP source using postorder DAG temporaries.

    :param compiler: Original global slot bindings and eager kernel signatures.
    :param equations: Contiguous batch-local equation list.
    :param offset: Global residual row of the first equation.
    :return: Python value kernel/signature and Python AD kernel/signature.
    """
    ordered: list[Expr] = list()
    seen: set[int] = set()
    pending: list[tuple[Expr, bool]] = list((equation, False) for equation in reversed(equations))
    while pending:
        node: Expr
        ready: bool
        node, ready = pending.pop()
        if ready:
            ordered.append(node)
        elif id(node) not in seen:
            seen.add(id(node))
            pending.append((node, True))
            if isinstance(node, BinOp):
                pending.append((node.right, False))
                pending.append((node.left, False))
            elif isinstance(node, UnOp):
                pending.append((node.operand, False))
            elif isinstance(node, Func2):
                pending.append((node.arg2, False))
                pending.append((node.arg1, False))
            elif isinstance(node, Func):
                pending.append((node.arg, False))
            else:
                pass
        else:
            pass

    residual: BatchResidualVisitor = BatchResidualVisitor(compiler)
    ad: BatchAdVisitor = BatchAdVisitor(compiler)
    value_lines: list[str] = list(("def batch_value(states, params, history, d_history, h, data_out, history2):",))
    ad_lines: list[str] = list(("def batch_ad(states, seeds, params, history, d_history, h, data_out, history2):",))
    shared_values: dict[str, str] = dict()
    shared_ad: dict[tuple[str, str], tuple[str, str]] = dict()
    index: int
    for index, node in enumerate(ordered):
        value_code: str = residual.visit(node)
        ad_value: str
        ad_dot: str
        ad_value, ad_dot = ad.visit(node)
        if isinstance(node, (BinOp, UnOp, Func, Func2)):
            # Shallow operation keys merge identical bound operations, never
            # symbolic names or reordered operands. Every child is already bound.
            value_name: str | None = shared_values.get(value_code, None)
            if value_name is None:
                value_name = f"_value_{index}"
                value_lines.append(f"    {value_name} = {value_code}")
                shared_values[value_code] = value_name
            else:
                pass
            residual.materialized[id(node)] = value_name
            key: tuple[str, str] = (ad_value, ad_dot)
            pair: tuple[str, str] | None = shared_ad.get(key, None)
            if pair is None:
                ad_name: str = f"_ad_value_{index}"
                dot_name: str = "0.0" if _is_zero(ad_dot) else f"_ad_dot_{index}"
                ad_lines.append(f"    {ad_name} = {ad_value}")
                if dot_name != "0.0":
                    ad_lines.append(f"    {dot_name} = {ad_dot}")
                else:
                    pass
                pair = (ad_name, dot_name)
                shared_ad[key] = pair
            else:
                pass
            ad.materialized[id(node)] = pair
        else:
            pass
    for index, node in enumerate(equations):
        value_lines.append(f"    data_out[{offset + index}] = {residual.visit(node)}")
        ad_lines.append(f"    data_out[{index}] = {ad.visit(node)[1]}")
    # Stable source identities allow Numba's existing disk cache to be reused.
    value_source: str = "\n".join(value_lines)
    ad_source: str = "\n".join(ad_lines)
    value_name = "rms_batch_value_" + hashlib.sha256(value_source.encode()).hexdigest()[:16]
    ad_name = "rms_batch_ad_" + hashlib.sha256(ad_source.encode()).hexdigest()[:16]
    value_source = value_source.replace("def batch_value(", f"def {value_name}(", 1)
    ad_source = ad_source.replace("def batch_ad(", f"def {ad_name}(", 1)
    value_function: Any = _compile_to_file(value_source, value_name)
    ad_function: Any = _compile_to_file(ad_source, ad_name)
    value_signature: Any = compiler.generate_signature(
        EagerKernelKind.Residual, len(compiler.variables_objs), len(compiler.parameters_objs), len(equations), True,
    )
    ad_signature: Any = compiler.generate_signature(
        EagerKernelKind.AutomaticDifferentiation, len(compiler.variables_objs), len(compiler.parameters_objs),
        len(equations), True,
    )
    return value_function, value_signature, ad_function, ad_signature
