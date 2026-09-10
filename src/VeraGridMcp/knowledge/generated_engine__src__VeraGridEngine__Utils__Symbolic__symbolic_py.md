# VeraGridEngine Module: src/VeraGridEngine/Utils/Symbolic/symbolic.py

- Original source path: `src/VeraGridEngine/Utils/Symbolic/symbolic.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 10
- Top-level function count: 69
- Representative imports: __future__, json, math, ast, uuid, builtins, numpy, enum, numba, typing, VeraGridEngine.enumerations

## Function: _new_uid()

Generate a fresh UUID‑v4 string.

## Function: _to_expr(val)

returns an expression

## Class: CmpOp

- Bases: Enum
- Summary: comparisons

### Methods

- No methods detected.

## Class: Comparison

- Bases: none
- Summary: Symbolic comparison wrapper.

### Methods

- `to_expression(self)`
  Summary: Convert the comparison into a heaviside-based symbolic expression.

## Class: Expr

- Bases: none
- Summary: Abstract base class for all expression nodes.

### Methods

- `eval(self, **bindings)`
  Summary: Numeric evaluation
- `eval_uid(self, uid_bindings)`
  Summary: :param uid_bindings:
- `diff(self, var, order, dt)`
  Summary: Differentiation (higher‑order)
- `_diff1(self, var, dt)`
  Summary: No docstring provided.
- `simplify(self)`
  Summary: Simplification & substitution (no‑ops by default)
- `subs(self, mapping)`
  Summary: substitute variables
- `to_dict(self)`
  Summary: returns a dictionary
- `to_json(self, **json_kwargs)`
  Summary: No docstring provided.
- `from_dict(data)`
  Summary: No docstring provided.
- `from_json(blob)`
  Summary: No docstring provided.
- `get_vars(self)`
  Summary: Get all variables in this expression.

## Class: Const

- Bases: Expr
- Summary: No docstring provided.

### Methods

- `eval(self, **bindings)`
  Summary: No docstring provided.
- `eval_uid(self, uid_bindings)`
  Summary: No docstring provided.
- `_diff1(self, var, dt)`
  Summary: No docstring provided.
- `subs(self, mapping)`
  Summary: No docstring provided.
- `to_dict(self)`
  Summary: No docstring provided.

## Class: VarType

- Bases: Enum
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Var

- Bases: Expr
- Summary: Any variable

### Methods

- `eval(self, **bindings)`
  Summary: Evaluate this variable
- `eval_uid(self, uid_bindings)`
  Summary: Evaluate using the uid
- `subs(self, mapping)`
  Summary: Substitute this variable
- `parse(data)`
  Summary: Parse the data
- `network_conn(self)`
  Summary: No docstring provided.
- `diff_order(self)`
  Summary: No docstring provided.
- `origin_var(self)`
  Summary: No docstring provided.
- `ref(self)`
  Summary: No docstring provided.
- `_diff1(self, var, dt)`
  Summary: differentiation
- `populate_initial_lag(self, x0, dx0, lag_x, dt)`
  Summary: Populate the numeric lag state for the current derivative order.
- `approximation_expr(self, dt, central)`
  Summary: Computes the n-th backward finite difference approximation of the derivative

## Function: get_expr_factors(expr)

:param expr:

## Function: build_mul(factors)

:param factors:

## Class: BinOp

- Bases: Expr
- Summary: Binary operation expression

### Methods

- `eval(self, **bindings)`
  Summary: Evaluation using names
- `eval_uid(self, uid_bindings)`
  Summary: Evaluate using uuid's
- `_diff1(self, var, dt)`
  Summary: Differentiation of this expression w.r.t var
- `simplify(self)`
  Summary: Simplify expression
- `subs(self, mapping)`
  Summary: Substitution
- `parse(data)`
  Summary: No docstring provided.
- `to_dict(self)`
  Summary: :return:

## Class: UnOp

- Bases: Expr
- Summary: Unary operation expression

### Methods

- `eval(self, **bindings)`
  Summary: :param bindings:
- `eval_uid(self, uid_bindings)`
  Summary: :param uid_bindings:
- `_diff1(self, var, dt)`
  Summary: :param var:
- `simplify(self)`
  Summary: :return:
- `subs(self, mapping)`
  Summary: :param mapping:
- `parse(data)`
  Summary: No docstring provided.
- `to_dict(self)`
  Summary: :return:

## Function: heaviside_num(x)

No docstring provided.

## Function: get_namespace()

Build the evaluation namespace used by generated expressions.

## Function: _evaluate_unary_function(op, value)

Evaluate a unary symbolic function explicitly by operator name.

## Function: _differentiate_unary_function(op, u, du)

Differentiate a unary symbolic function explicitly by operator name.

## Function: _evaluate_binary_function(name, arg1, arg2)

Evaluate a binary symbolic function explicitly by function name.

## Class: Func

- Bases: Expr
- Summary: No docstring provided.

### Methods

- `eval(self, **bindings)`
  Summary: No docstring provided.
- `eval_uid(self, uid_bindings)`
  Summary: No docstring provided.
- `parse(data)`
  Summary: No docstring provided.
- `to_dict(self)`
  Summary: :return:
- `_diff1(self, var, dt)`
  Summary: No docstring provided.
- `subs(self, mapping)`
  Summary: No docstring provided.

## Function: _symbolic_abs(x)

Create a symbolic absolute-value expression.

## Function: abs_diff(u, du)

No docstring provided.

## Function: real(x)

No docstring provided.

## Function: imag(x)

No docstring provided.

## Function: conj(x)

No docstring provided.

## Function: angle(x)

No docstring provided.

## Function: sin(x)

No docstring provided.

## Function: sin_diff(u, du)

No docstring provided.

## Function: cos(x)

No docstring provided.

## Function: cos_diff(u, du)

No docstring provided.

## Function: sec(x)

No docstring provided.

## Function: tan(x)

No docstring provided.

## Function: tan_diff(u, du)

No docstring provided.

## Function: exp(x)

No docstring provided.

## Function: exp_diff(u, du)

No docstring provided.

## Function: log(x)

No docstring provided.

## Function: log_diff(u, du)

No docstring provided.

## Function: sqrt(x)

No docstring provided.

## Function: sqrt_diff(u, du)

No docstring provided.

## Function: asin(x)

No docstring provided.

## Function: asin_diff(u, du)

No docstring provided.

## Function: acos(x)

No docstring provided.

## Function: acos_diff(u, du)

No docstring provided.

## Function: atan(x)

No docstring provided.

## Function: atan_diff(u, du)

No docstring provided.

## Function: sinh(x)

No docstring provided.

## Function: cosh(x)

No docstring provided.

## Function: sinh_diff(u, du)

No docstring provided.

## Function: cosh_diff(u, du)

No docstring provided.

## Function: heaviside(x)

No docstring provided.

## Function: heaviside_diff(u, du)

No docstring provided.

## Function: _symbolic_max(x, y)

Build a symbolic maximum expression.

## Function: _symbolic_min(x, y)

Build a symbolic minimum expression.

## Function: abs(x)

Public symbolic absolute-value helper kept for API compatibility.

## Function: max(x, y)

Public symbolic maximum helper kept for API compatibility.

## Function: min(x, y)

Public symbolic minimum helper kept for API compatibility.

## Function: atan2(x, y)

No docstring provided.

## Function: hard_sat(x, x_min, x_max)

Apply a symbolic hard saturation to an expression.

## Function: f_exc(In)

No docstring provided.

## Function: piecewise(time_var, t_events, new_values, default_value)

Symbolic piecewise function.

## Class: Func2

- Bases: Expr
- Summary: Symbolic binary function node.

### Methods

- `eval(self, **bindings)`
  Summary: No docstring provided.
- `eval_uid(self, uid_bindings)`
  Summary: No docstring provided.
- `_diff1(self, var, dt)`
  Summary: differentiation
- `simplify(self)`
  Summary: simplification
- `subs(self, mapping)`
  Summary: substitude

## Function: _expr_to_dict(expr)

Serialise any `Expr` tree into a plain Python dictionary that’s

## Function: _dict_to_expr(data)

De-Serialize expression from dictionary

## Function: diff(expr, var, order)

Return ∂^order(expr)/∂var^order.

## Function: eval_uid(expr, uid_bindings)

Evaluate *expr* with a mapping from node UID → numeric value.

## Function: _collect_vars(expr, out)

Collect variables in a deterministic order

## Function: _all_vars(expressions)

Collect all variables in a list of expressions

## Function: _precedence(expr)

Return operator precedence for expression emission.

## Function: expression2numba(expr, compiler_names_dict, parent_prec)

Emit a precedence-aware, Numba-friendly Python expression.

## Function: _emit_event_params_eq(expr, uid_map_t)

Emit an event-parameter expression as pure Python source.

## Function: _emit_one(expr, uid_map_vars, uid_map_event_params, uid_map_params)

Emit a pure-Python (Numba-friendly) expression string

## Function: find_vars_order(expressions, ordering, var_dict)

Return the variable list that positional JIT functions will expect.

## Function: get_expression_vars(expr, vars_found)

Get the list of variables from any expression

## Function: _get_binop_symbol(op_node)

Translate a Python AST binary operator into a symbolic operator token.

## Function: _get_unop_symbol(op_node)

Translate a Python AST unary operator into a symbolic operator token.

## Function: _call_symbolic_parser_function(function_name, arg_expr)

Invoke a supported unary symbolic parser function by name.

## Function: _get_symbolic_parser_function_names_internal()

Return the list of public unary functions accepted by the parser.

## Function: _ast_to_symbolic(node, symbol_namespace)

Convert a restricted Python AST into a symbolic expression tree.

## Function: string_to_symbolic(expression_text, symbol_namespace)

Parse a textual symbolic expression into a symbolic tree using a safe AST walk.

## Function: get_symbolic_parser_function_names()

Return the public function names accepted by :func:`string_to_symbolic`.

## Function: symbolic_to_string(expr)

Convert a symbolic expression into a string (parsable by parse_expr).
