# VeraGridEngine Module: src/VeraGridEngine/Templates/Emt/xfmr_emt_template.py

- Original source path: `src/VeraGridEngine/Templates/Emt/xfmr_emt_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 10
- Representative imports: __future__, typing, math, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Devices.Branches.transformer, VeraGridEngine.Devices.Dynamic.emt_template, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic

## Function: _safe_positive(value, default, floor)

No docstring provided.

## Function: _parse_connection(trafo)

No docstring provided.

## Function: _connection_matrix(winding_type)

No docstring provided.

## Function: _phase_permutation_matrix(clock)

No docstring provided.

## Function: _estimate_core_loss_conductance_pu(trafo)

No docstring provided.

## Function: _estimate_frolich_coefficients(trafo)

No docstring provided.

## Function: _estimate_terminal_capacitance_pu(trafo, omega_base)

No docstring provided.

## Function: _frolich_current(lam, a_coeff, b_coeff, eps)

No docstring provided.

## Function: _mat_vec_expr(mat, vec, c0)

No docstring provided.

## Function: get_xfmr_emt_template(grid, trafo, name, core_topology)

Build an EMT transformer template inspired by ATPDraw's XFMR hybrid model.
