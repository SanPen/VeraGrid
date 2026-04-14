# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_basic_formulation.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_basic_formulation.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Topology.admittance_matrices, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.Derivatives.ac_jacobian, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.enumerations

## Class: PfBasicFormulation

- Bases: PfFormulationTemplate
- Summary: No docstring provided.

### Methods

- `x2var(self, x)`
  Summary: Convert X to decision variables
- `var2x(self)`
  Summary: Convert the internal decission variables into the vector
- `update_bus_types(self, pq, pv, pqv, p)`
  Summary: :param pq:
- `size(self)`
  Summary: Size of the jacobian matrix
- `check_error(self, x)`
  Summary: Check error of the solution without affecting the problem
- `update(self, x, update_controls)`
  Summary: Update step
- `fx(self)`
  Summary: :return:
- `Jacobian(self)`
  Summary: :return:
- `get_x_names(self)`
  Summary: Names matching x
- `get_fx_names(self)`
  Summary: Names matching fx
- `get_solution(self, elapsed, iterations)`
  Summary: Get the problem solution
