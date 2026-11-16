# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Generate native colored AD sweeps over equivalent RMS model instances."""

import ast
import hashlib
import inspect
from types import FunctionType
import numba as nb
import numpy as np
from numba.core.registry import CPUDispatcher
from numba.core.typing.templates import Signature

from VeraGridEngine.Utils.Symbolic.jit_compiler_rms_numba_comp import (
    RmsEagerEquationCompiler, _compile_to_file,
)
from VeraGridEngine.Utils.Symbolic.sparse_ad_jacobian import greedy_color_columns
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Expr, Func, Func2, UnOp, Var


class CategoryAdArrayBindings(ast.NodeTransformer):
    """Convert scalar residual/AD input slots to per-instance matrix slots."""

    __slots__ = ("_runtime_count",)

    def __init__(self, runtime_count: int) -> None:
        """Record the boundary between variable and constant parameters.

        :param runtime_count: Number of variable parameter rows.
        :return: None.
        """
        self._runtime_count: int = runtime_count

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Rewrite only the known scalar kernel inputs, preserving the expression tree.

        :param node: Original scalar array access.
        :return: Equivalent access for the current color and instance.
        """
        if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
            name: str = node.value.id
            index: int = int(node.slice.value)
            source: str | None = None
            if name == "states":
                source = f"values[{index}, instance]"
            elif name == "d_history":
                source = f"derivatives[{index}, instance]"
            elif name == "params":
                if index < self._runtime_count:
                    source = f"runtime[{index}, instance]"
                else:
                    source = f"constants[{index - self._runtime_count}, instance]"
            elif name == "seeds":
                source = f"seed_matrix[color, {index}]"
            else:
                pass
            if source is not None:
                return ast.copy_location(ast.parse(source, mode="eval").body, node)
            else:
                pass
        else:
            pass
        return self.generic_visit(node)


def build_category_instance_body(python_function: FunctionType, runtime_count: int) -> list[str]:
    """Reuse scalar code generation while retaining its exact expression parentheses.

    :param python_function: Generated scalar residual or directional derivative.
    :param runtime_count: Boundary between variable and constant parameter slots.
    :return: Statements accessing the current instance's input column.
    """
    definition: ast.stmt = ast.parse(inspect.getsource(python_function)).body[0]
    if isinstance(definition, ast.FunctionDef):
        pass
    else:
        raise ValueError("The generated RMS kernel must be a function definition")
    transformer: CategoryAdArrayBindings = CategoryAdArrayBindings(runtime_count)
    body: list[str] = list()
    statement: ast.stmt
    # Transform array bindings rather than rewriting mathematical expressions as text.
    for statement in definition.body:
        transformed: ast.AST = transformer.visit(statement)
        body.append(ast.unparse(ast.fix_missing_locations(transformed)))
    return body


def compile_category_residual(compiler: RmsEagerEquationCompiler,
                              equations: list[Expr], runtime_count: int) -> CPUDispatcher:
    """Compile value evaluation and signed row accumulation for every instance.

    :param compiler: Representative's established scalar slot bindings.
    :param equations: Differential, device and mapped-terminal expressions.
    :param runtime_count: Number of variable parameter rows.
    :return: Native dispatcher with a fixed in-place signature.
    """
    python_residual: FunctionType
    scalar_signature: Signature
    python_residual, scalar_signature = compiler.compile(equations, use_cse=True)
    body: list[str] = build_category_instance_body(python_residual, runtime_count)
    arguments: str = (
        "values, derivatives, runtime, constants, h, pointers, source_rows, "
        "positions, weights, data_out, output"
    )
    lines: list[str] = list((
        f"def category_residual({arguments}):",
        "    instance: int",
        "    entry: int",
        "    for instance in range(values.shape[1]):",
    ))
    source: str
    for source in body:
        lines.extend("        " + line for line in source.splitlines())
    lines.extend((
        "        for entry in range(pointers[instance], pointers[instance + 1]):",
        "            output[positions[entry]] += weights[entry] * data_out[source_rows[entry]]",
    ))
    source = "\n".join(lines)
    digest: str = hashlib.sha256(source.encode()).hexdigest()[:16]
    name: str = f"rms_category_rhs_{digest}"
    source = source.replace("def category_residual(", f"def {name}(", 1)
    python_kernel: FunctionType = _compile_to_file(source, name)
    vector: nb.types.Array = nb.float64[::1]
    matrix: nb.types.Array = nb.float64[:, ::1]
    integers: nb.types.Array = nb.int64[::1]
    signature: Signature = nb.void(matrix, matrix, matrix, matrix, nb.float64,
                              integers, integers, integers, vector, vector, vector)
    # NumPy error semantics allow the existing solver guards to reject invalid candidates.
    native_kernel: CPUDispatcher = nb.njit(signature, cache=True, fastmath=False, error_model="numpy")(python_kernel)
    return native_kernel


class RmsCategoryAdCompiler:
    """Compile a representative's residual and colored AD instance loops."""

    __slots__ = ("rows", "columns", "colors", "seeds", "equation_count", "kernel", "residual_kernel")

    def __init__(self, equations: list[Expr], variables: list[Var],
                 derivatives: list[Var], runtime: list[Var], constants: list[Var]) -> None:
        """Prepare one kernel reused by all members of a structural category.

        :param equations: State, device algebraic and mapped terminal equations.
        :param variables: Local inputs in gather-matrix row order.
        :param derivatives: Local derivative slots.
        :param runtime: Local variable parameter slots.
        :param constants: Local constant parameter slots.
        :return: None.
        """
        variable_positions: dict[int, int] = dict()
        column_rows: list[list[int]] = list(list() for _ in variables)
        index: int
        variable: Var
        for index, variable in enumerate(variables):
            variable_positions[variable.uid] = index
        row: int
        equation: Expr
        # A local pattern includes external inputs and complete derivative base chains.
        for row, equation in enumerate(equations):
            pending: list[Expr] = list((equation,))
            seen: set[int] = set()
            columns: set[int] = set()
            while pending:
                expression: Expr = pending.pop()
                if id(expression) not in seen:
                    seen.add(id(expression))
                    if isinstance(expression, Var):
                        base: Var | None = expression
                        while base is not None:
                            column: int | None = variable_positions.get(base.uid, None)
                            if column is not None:
                                columns.add(column)
                            else:
                                pass
                            base = base.base_var
                    elif isinstance(expression, BinOp):
                        pending.append(expression.left)
                        pending.append(expression.right)
                    elif isinstance(expression, UnOp):
                        pending.append(expression.operand)
                    elif isinstance(expression, Func):
                        pending.append(expression.arg)
                    elif isinstance(expression, Func2):
                        pending.append(expression.arg1)
                        pending.append(expression.arg2)
                    else:
                        pass
                else:
                    pass
            for index in sorted(columns):
                column_rows[index].append(row)

        color_count: int
        self.colors, color_count = greedy_color_columns(column_rows, len(equations))
        nnz: int = sum(len(entries) for entries in column_rows)
        self.rows: np.ndarray = np.empty(nnz, dtype=np.int64)
        self.columns: np.ndarray = np.empty(nnz, dtype=np.int64)
        position: int = 0
        for index, entries in enumerate(column_rows):
            for row in entries:
                self.rows[position] = row
                self.columns[position] = index
                position += 1
        self.seeds: np.ndarray = np.zeros((color_count, len(variables)), dtype=np.float64)
        for index in range(len(variables)):
            self.seeds[self.colors[index], index] = 1.0
        self.equation_count: int = len(equations)

        parameters: list[Var] = list(runtime)
        parameters.extend(constants)
        compiler: RmsEagerEquationCompiler = RmsEagerEquationCompiler(variables, parameters, derivatives)
        python_ad: FunctionType
        scalar_signature: Signature
        python_ad, scalar_signature = compiler.compile_ad_kernel(equations)
        body: list[str] = build_category_instance_body(python_ad, len(runtime))

        # One native call covers every local color and every equivalent instance.
        arguments: str = (
            "values, derivatives, runtime, constants, h, seed_matrix, pointers, "
            "source_rows, block_ids, positions, weights, data_out, j11, j12, j21, j22"
        )
        lines: list[str] = list((
            f"def category_kernel({arguments}):",
            "    for color in range(seed_matrix.shape[0]):",
            "        for instance in range(values.shape[1]):",
        ))
        for source in body:
            lines.extend("            " + line for line in source.splitlines())
        lines.extend((
            "            for entry in range(pointers[color, instance], pointers[color, instance + 1]):",
            "                value = weights[entry] * data_out[source_rows[entry]]",
            "                position = positions[entry]",
            "                block = block_ids[entry]",
            "                if block == 0:",
            "                    j11[position] += value",
            "                elif block == 1:",
            "                    j12[position] += value",
            "                elif block == 2:",
            "                    j21[position] += value",
            "                else:",
            "                    j22[position] += value",
        ))
        source: str = "\n".join(lines)
        digest: str = hashlib.sha256(source.encode()).hexdigest()[:16]
        name: str = f"rms_category_ad_{digest}"
        source = source.replace("def category_kernel(", f"def {name}(", 1)
        python_kernel: FunctionType = _compile_to_file(source, name)
        vector: nb.types.Array = nb.float64[::1]
        matrix: nb.types.Array = nb.float64[:, ::1]
        integers: nb.types.Array = nb.int64[::1]
        signature: Signature = nb.void(
            matrix, matrix, matrix, matrix, nb.float64, matrix, nb.int64[:, ::1],
            integers, nb.int8[::1], integers, vector, vector, vector, vector, vector, vector,
        )
        self.kernel: CPUDispatcher = nb.njit(signature, cache=True, fastmath=False, error_model="numpy")(python_kernel)
        self.residual_kernel: CPUDispatcher = compile_category_residual(compiler, equations, len(runtime))


def compile_category_coordinator(kernels: tuple[CPUDispatcher, ...]) -> CPUDispatcher:
    """Generate explicit native calls while retaining each category's own kernel.

    :param kernels: Prepared category residual dispatchers in stable order.
    :return: Numba coordinator; specialized once when its fixed buffers are bound.
    """
    # Each category remains a separately compiled function; no global symbolic expansion occurs.
    lines: list[str] = list(("import numba as nb",))
    index: int
    kernel: CPUDispatcher
    for index, kernel in enumerate(kernels):
        source: str = inspect.getsource(kernel.py_func)
        source = source.replace("def " + kernel.py_func.__name__ + "(", f"def category_{index}(", 1)
        lines.append('@nb.njit(cache=True, fastmath=False, error_model="numpy")')
        lines.append(source)
    lines.extend((
        "def category_coordinator(values, derivatives, previous, h, categories, runtime_global,",
        "                         raw, output, fixed_rows, fixed_columns, fixed_weights, constant_rhs, state_count,",
        "                         refresh_runtime, gather_values, evaluate_values, implicit):",
        '    """Gather persistent category inputs and evaluate the requested equations."""',
        "    if evaluate_values:",
        "        raw[:] = constant_rhs",
        "    else:",
        "        pass",
    ))
    for index in range(len(kernels)):
        # Literal tuple indexing lets Numba resolve every category statically.
        lines.extend((
            f"    data = categories[{index}]",
            "    if gather_values:",
            "        for row in range(data[4].shape[0]):",
            "            for instance in range(data[4].shape[1]):",
            "                data[0][row, instance] = values[data[4][row, instance]]",
            "        for row in range(data[5].shape[0]):",
            "            for instance in range(data[5].shape[1]):",
            "                data[1][row, instance] = derivatives[data[5][row, instance]]",
            "    else:",
            "        pass",
            "    if refresh_runtime:",
            "        for row in range(data[6].shape[0]):",
            "            for instance in range(data[6].shape[1]):",
            "                data[2][row, instance] = runtime_global[data[6][row, instance]]",
            "    else:",
            "        pass",
            "    if evaluate_values:",
            f"        category_{index}(data[0], data[1], data[2], data[3], h,",
            "                         data[7], data[8], data[9], data[10], data[11], raw)",
            "    else:",
            "        pass",
        ))
    lines.extend((
        "    if evaluate_values:",
        "        for entry in range(fixed_rows.size):",
        "            raw[fixed_rows[entry]] += fixed_weights[entry] * values[fixed_columns[entry]]",
        "        if implicit:",
        "            for row in range(state_count):",
        "                output[row] = values[row] - previous[row] - h * raw[row]",
        "            for row in range(state_count, raw.size):",
        "                output[row] = raw[row]",
        "        else:",
        "            pass",
        "    else:",
        "        pass",
    ))
    source = "\n".join(lines)
    digest: str = hashlib.sha256(source.encode()).hexdigest()[:16]
    name: str = f"rms_category_coordinator_{digest}"
    source = source.replace("def category_coordinator(", f"def {name}(", 1)
    function: FunctionType = _compile_to_file(source, name)
    return nb.njit(cache=True, fastmath=False, error_model="numpy")(function)
