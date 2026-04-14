# VeraGridEngine Module: src/VeraGridEngine/Simulations/StateEstimation/state_stimation_driver.py

- Original source path: `src/VeraGridEngine/Simulations/StateEstimation/state_stimation_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: __future__, typing, VeraGridEngine.Simulations.StateEstimation.observability_analysis, VeraGridEngine.Simulations.StateEstimation.pseudo_measurements_augmentation, VeraGridEngine.Simulations.StateEstimation.state_estimation_results, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.StateEstimation.state_estimation, VeraGridEngine.Simulations.StateEstimation.state_estimation_inputs, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.driver_template, VeraGridEngine.enumerations

## Class: StateEstimationOptions

- Bases: none
- Summary: StateEstimationOptions

### Methods

- No methods detected.

## Class: StateEstimationConvergenceReport

- Bases: ConvergenceReport
- Summary: No docstring provided.

### Methods

- `add_se(self, method, converged, error, elapsed, iterations, bad_data_detected, is_observable, bus_contribution, pseudo_measurements, unobservable_buses, measurement_profile)`
  Summary: :param method:
- `is_observable(self)`
  Summary: Get info is the island was observable
- `get_bad_data_detected(self)`
  Summary: Get bad data detection results
- `get_unobservable_buses(self)`
  Summary: :return:
- `get_bus_contribution(self)`
  Summary: :return:
- `get_pseudo_measurements(self)`
  Summary: :return:
- `add_unobservable_buses(self, unobservable_buses)`
  Summary: :param unobservable_buses:
- `add_bus_contribution(self, bus_contribution)`
  Summary: :param bus_contribution:
- `add_pseudo_measurements(self, se_input)`
  Summary: :param se_input:
- `add_measurement_profile(self, meas_profile)`
  Summary: :param meas_profile:
- `get_measurement_profile(self)`
  Summary: :return:

## Class: StateEstimationDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `collect_measurements(circuit)`
  Summary: Form the input from the circuit measurements
- `run(self)`
  Summary: Run state estimation
