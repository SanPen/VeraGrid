# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_basic_formulation_3ph.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_basic_formulation_3ph.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 14
- Representative imports: typing, numba, numpy, scipy.sparse, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.Derivatives.ac_jacobian, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Sparse.csc2

## Function: lookup_from_mask(mask)

This function builds the lookup vector based on the information provided by the mask vector.

## Function: compute_ybus_generator(nc)

Compute the Ybus matrix for a generator in a 3-phase system with neutral.

## Function: compute_ybus(nc)

Compute admittances and masks

## Function: compute_generators(bus_idx, bus_lookup, V, P, PF, is_controlled)

No docstring provided.

## Function: compute_current_loads(bus_idx, bus_lookup, V, Istar, Idelta, Ifloating)

:param bus_idx:

## Function: compute_power_loads(bus_idx, bus_lookup, V, Sstar, Sfloating, Sdelta)

:param bus_idx:

## Function: calc_autodiff_jacobian(func, x, h)

Compute the Jacobian matrix of `func` at `x` using finite differences.

## Function: expand3ph(x)

Expands a numpy array to 3-pase copying the same values

## Function: slice_indices(pq, bus_lookup)

Slice the indices based on the bus_lookup

## Function: expand_indices_3ph(x)

Expands a numpy array to 3-pase copying the same values

## Function: expand_slice_indices_3ph(x, bus_lookup)

Expands and slices a numpy array to 3-phase copying the same values

## Function: expandVoltage3ph(V0)

Expands a numpy array to 3-pase copying the same values

## Function: expand_magnitudes(magnitude, lookup)

Expands the masked magnitude using the lookup saving zeros where the lookup is -1,

## Function: expand_matrix(magnitude, lookup)

Expands a matrix by adding zero rows and columns based on the lookup indices.

## Class: PfBasicFormulation3Ph

- Bases: PfFormulationTemplate
- Summary: No docstring provided.

### Methods

- `x2var(self, x)`
  Summary: Convert X to decision variables
- `var2x(self)`
  Summary: Convert the internal decision variables into the vector
- `update_bus_types(self, pq, pv, pqv, p)`
  Summary: :param pq:
- `size(self)`
  Summary: Size of the jacobian matrix
- `compute_f(self, x)`
  Summary: Compute the function residual
- `check_error(self, x)`
  Summary: Check error of the solution without affecting the problem
- `update(self, x, update_controls)`
  Summary: Update step
- `fx(self)`
  Summary: # Scalc = V · (Y x V - I)^*
- `Jacobian(self, autodiff)`
  Summary: :param autodiff: If True, use autodiff to compute the Jacobian
- `get_x_names(self)`
  Summary: Names matching x
- `get_fx_names(self)`
  Summary: Names matching fx
- `get_solution(self, elapsed, iterations)`
  Summary: Get the problem solution
