# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import ast
import math
import numpy as np


def find_between(s: str, first: str, last: str) -> str:
    """
    Find sting between two sub-strings
    Args:
        s: Main string
        first: first sub-string
        last: second sub-string
    Example find_between('[Hello]', '[', ']')  -> returns 'Hello'
    Returns:
        String between the first and second sub-strings, if any was found otherwise returns an empty string
    """
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def _get_matlab_constant_value(name: str) -> float:
    """
    Map one MATLAB-like scalar constant to a Python float.

    :param name:
        Constant token to resolve.
    :return:
        Numeric value for the constant.
    :raises ValueError:
        If the constant is not supported.
    """
    normalized_name: str = name.strip().lower()

    if normalized_name == "pi":
        return math.pi
    elif normalized_name == "inf":
        return math.inf
    elif normalized_name == "nan":
        return math.nan
    elif normalized_name == "eps":
        return math.ulp(1.0)
    else:
        raise ValueError(f"Unsupported MATLAB constant: {name}")


def _apply_matlab_unary_operator(operator_node: ast.unaryop, operand_value: float) -> float:
    """
    Apply one unary operator in a MATLAB-like scalar expression.

    :param operator_node:
        Parsed unary operator node.
    :param operand_value:
        Numeric operand value.
    :return:
        Evaluated unary result.
    :raises ValueError:
        If the unary operator is not supported.
    """
    if isinstance(operator_node, ast.UAdd):
        return operand_value
    elif isinstance(operator_node, ast.USub):
        return -operand_value
    else:
        raise ValueError(f"Unsupported MATLAB unary operator: {type(operator_node).__name__}")


def _apply_matlab_binary_operator(operator_node: ast.operator,
                                  left_value: float,
                                  right_value: float) -> float:
    """
    Apply one binary operator in a MATLAB-like scalar expression.

    :param operator_node:
        Parsed binary operator node.
    :param left_value:
        Numeric left operand.
    :param right_value:
        Numeric right operand.
    :return:
        Evaluated binary result.
    :raises ValueError:
        If the binary operator is not supported.
    """
    if isinstance(operator_node, ast.Add):
        return left_value + right_value
    elif isinstance(operator_node, ast.Sub):
        return left_value - right_value
    elif isinstance(operator_node, ast.Mult):
        return left_value * right_value
    elif isinstance(operator_node, ast.Div):
        return left_value / right_value
    elif isinstance(operator_node, ast.Pow):
        return left_value ** right_value
    else:
        raise ValueError(f"Unsupported MATLAB binary operator: {type(operator_node).__name__}")


def _apply_matlab_function(function_name: str, argument_values: list[float]) -> float:
    """
    Evaluate one supported MATLAB-like scalar function.

    :param function_name:
        Function identifier.
    :param argument_values:
        Evaluated scalar arguments.
    :return:
        Numeric function result.
    :raises ValueError:
        If the function is not supported.
    """
    normalized_name: str = function_name.strip().lower()

    if normalized_name == "sqrt":
        return math.sqrt(argument_values[0])
    elif normalized_name == "abs":
        return abs(argument_values[0])
    elif normalized_name == "sin":
        return math.sin(argument_values[0])
    elif normalized_name == "cos":
        return math.cos(argument_values[0])
    elif normalized_name == "tan":
        return math.tan(argument_values[0])
    elif normalized_name == "asin":
        return math.asin(argument_values[0])
    elif normalized_name == "acos":
        return math.acos(argument_values[0])
    elif normalized_name == "atan":
        return math.atan(argument_values[0])
    elif normalized_name == "exp":
        return math.exp(argument_values[0])
    elif normalized_name == "log":
        return math.log(argument_values[0])
    elif normalized_name == "log10":
        return math.log10(argument_values[0])
    elif normalized_name == "sign":
        if argument_values[0] > 0.0:
            return 1.0
        elif argument_values[0] < 0.0:
            return -1.0
        else:
            return 0.0
    elif normalized_name == "min":
        return min(argument_values)
    elif normalized_name == "max":
        return max(argument_values)
    else:
        raise ValueError(f"Unsupported MATLAB function: {function_name}")


def _evaluate_matlab_float_node(node: ast.AST) -> float:
    """
    Evaluate one parsed AST node from a MATLAB-like scalar expression.

    :param node:
        AST node to evaluate.
    :return:
        Numeric node value.
    :raises ValueError:
        If the node is not supported.
    """
    if isinstance(node, ast.Expression):
        return _evaluate_matlab_float_node(node.body)
    elif isinstance(node, ast.Constant):
        constant_value = node.value
        if isinstance(constant_value, int | float):
            return float(constant_value)
        else:
            raise ValueError(f"Unsupported MATLAB constant literal: {constant_value!r}")
    elif isinstance(node, ast.Name):
        return _get_matlab_constant_value(node.id)
    elif isinstance(node, ast.UnaryOp):
        operand_value: float = _evaluate_matlab_float_node(node.operand)
        return _apply_matlab_unary_operator(node.op, operand_value)
    elif isinstance(node, ast.BinOp):
        left_value: float = _evaluate_matlab_float_node(node.left)
        right_value: float = _evaluate_matlab_float_node(node.right)
        return _apply_matlab_binary_operator(node.op, left_value, right_value)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            argument_values: list[float] = list()
            argument_node: ast.AST
            for argument_node in node.args:
                argument_values.append(_evaluate_matlab_float_node(argument_node))

            return _apply_matlab_function(node.func.id, argument_values)
        else:
            raise ValueError("Unsupported MATLAB callable expression")
    else:
        raise ValueError(f"Unsupported MATLAB AST node: {type(node).__name__}")


def parse_matlab_float(value: str) -> float:
    """
    Parse one MATLAB-like scalar token into a Python float.

    :param value:
        Scalar token or scalar expression.
    :return:
        Parsed floating-point value.
    :raises ValueError:
        If the token cannot be parsed as a supported scalar expression.
    """
    stripped_value: str = value.strip()

    try:
        return float(stripped_value)
    except ValueError:
        normalized_value: str = stripped_value.replace("^", "**")
        expression: ast.Expression = ast.parse(normalized_value, mode="eval")
        return _evaluate_matlab_float_node(expression)


def txt2mat(txt: str, line_splitter: str = ';', to_float: bool = True) -> np.ndarray:
    """
    Convert one MATPOWER matrix literal into a NumPy array.

    :param txt:
        Matrix body text without the outer brackets.
    :param line_splitter:
        Row terminator token.
    :param to_float:
        Whether to parse entries as numeric values.
    :return:
        Parsed matrix.
    """
    lines = txt.strip().split('\n')
    # del lines[-1]

    # preprocess lines (delete the comments)
    lines2 = list()
    for i, line in enumerate(lines):
        if line.lstrip()[0] != '%':
            lines2.append(line)
        else:
            # print('skipping', line)
            pass

    # convert the lines to data
    nrows = len(lines2)
    arr = None
    for i, line in enumerate(lines2):

        if ';' in line:
            line2 = line.split(line_splitter)[0]
        else:
            line2 = line

        vec = line2.strip().split()

        # declare the container array based on the first line
        if arr is None:
            ncols = len(vec)
            if to_float:
                arr = np.zeros((nrows, ncols))
            else:
                arr = np.zeros((nrows, ncols), dtype=object)

        # fill-in the data
        for j, val in enumerate(vec):
            if to_float:
                # MATPOWER case files sometimes store scalar expressions instead
                # of literal numbers, so use the MATLAB-like scalar parser.
                arr[i, j] = parse_matlab_float(val)
            else:
                arr[i, j] = val.strip().replace("'", "")

    return np.array(arr)
