# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_formulation_template.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_formulation_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, pandas, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options

## Class: PfFormulationTemplate

- Bases: none
- Summary: Base Power Flow Formulation class

### Methods

- `converged(self)`
  Summary: Converged?
- `error(self)`
  Summary: Converged?
- `f(self)`
  Summary: Converged?
- `Va(self)`
  Summary: Voltage angles
- `Vm(self)`
  Summary: Voltage modules
- `x2var(self, x)`
  Summary: Convert X to decision variables
- `var2x(self)`
  Summary: Convert the internal decision variables into the vector
- `check_error(self, x)`
  Summary: Check error of the solution without affecting the problem
- `update(self, x, update_controls)`
  Summary: Update the problem
- `size(self)`
  Summary: Size of the jacobian matrix
- `fx(self)`
  Summary: :return:
- `Jacobian(self)`
  Summary: :return:
- `solve_step_from_f(self, f)`
  Summary: :param f: Function residual
- `solve_step(self)`
  Summary: :return:
- `get_x_names(self)`
  Summary: Names matching x
- `get_fx_names(self)`
  Summary: Names matching fx
- `get_jacobian_df(self, J, autodiff)`
  Summary: Get the Jacobian DataFrame
- `get_f_df(self, f)`
  Summary: Get the f(x) DataFrame
- `get_x_df(self, x)`
  Summary: Get the x DataFrame
- `get_solution(self, elapsed, iterations)`
  Summary: :return:
