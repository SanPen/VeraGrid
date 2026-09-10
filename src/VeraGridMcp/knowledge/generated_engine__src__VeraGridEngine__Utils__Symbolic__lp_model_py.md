# VeraGridEngine Module: src/VeraGridEngine/Utils/Symbolic/lp_model.py

- Original source path: `src/VeraGridEngine/Utils/Symbolic/lp_model.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 8
- Top-level function count: 7
- Representative imports: __future__, dataclasses, numpy, highspy, typing, VeraGridEngine.Utils.Symbolic.symbolic

## Class: _AB

- Bases: Protocol
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: _LeftRight

- Bases: Protocol
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: _LhsRhs

- Bases: Protocol
- Summary: No docstring provided.

### Methods

- No methods detected.

## Function: _binop_children(node)

Return the two operands of *node*.

## Function: _combine(dst, src)

No docstring provided.

## Function: _affine_parts(node, scale)

No docstring provided.

## Class: LinExpr

- Bases: none
- Summary: Linear expression

### Methods

- `from_expr(expr)`
  Summary: No docstring provided.

## Class: Constraint

- Bases: none
- Summary: No docstring provided.

### Methods

- `from_sides(lhs, op, rhs)`
  Summary: No docstring provided.
- `leq(cls, expr, rhs)`
  Summary: No docstring provided.
- `geq(cls, expr, rhs)`
  Summary: No docstring provided.
- `eq(cls, expr, rhs)`
  Summary: No docstring provided.

## Function: _as_constraint(obj)

:param obj:

## Class: Result

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: _LinVarExtension

- Bases: none
- Summary: Internal data that extends Var to have LP limits

### Methods

- No methods detected.

## Function: _to_lin(val)

No docstring provided.

## Class: LPModel

- Bases: none
- Summary: LPModel

### Methods

- `add_var(self, name, low, up, integer, start)`
  Summary: No docstring provided.
- `minimise(self, expr)`
  Summary: No docstring provided.
- `maximise(self, expr)`
  Summary: No docstring provided.
- `solve(self)`
  Summary: No docstring provided.

## Function: diet_problem()

No docstring provided.

## Function: knapsack_demo()

No docstring provided.
