# VeraGridEngine Module: src/VeraGridEngine/Simulations/StateEstimation/pseudo_measurements_augmentation.py

- Original source path: `src/VeraGridEngine/Simulations/StateEstimation/pseudo_measurements_augmentation.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 3
- Representative imports: numpy, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.Devices.measurement, VeraGridEngine.enumerations

## Class: PseudoMeasurement

- Bases: MeasurementTemplate
- Summary: No docstring provided.

### Methods

- `get_value_pu(self, Sbase)`
  Summary: No docstring provided.
- `get_standard_deviation_pu(self, Sbase)`
  Summary: No docstring provided.

## Function: build_neighbors(Cf, Ct)

Build neighbor list per bus from connectivity matrices.

## Function: compute_power_injection(bus, V, Ybus, neighbors)

Compute AC active and reactive power injection for a bus using neighbors.

## Function: add_pseudo_measurements(se_input, unobservable_buses, V, Ybus, neighbors, bus_dict, sigma_pseudo, Sbase, logger)

Extend se_input with pseudo-measurements for unobservable buses.
