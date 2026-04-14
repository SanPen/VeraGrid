# VeraGridEngine Module: src/VeraGridEngine/Simulations/driver_template.py

- Original source path: `src/VeraGridEngine/Simulations/driver_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 4
- Top-level function count: 0
- Representative imports: __future__, time, numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.results_template

## Class: DummySignal

- Bases: none
- Summary: Qt signal placeholder to not to import QT in the engine

### Methods

- `emit(self, val)`
  Summary: No docstring provided.
- `connect(self, val)`
  Summary: :param val:

## Class: DriverToSave

- Bases: none
- Summary: Wrapper to save a driver

### Methods

- No methods detected.

## Class: DriverTemplate

- Bases: none
- Summary: Base driver template

### Methods

- `tic(self, skip_logger)`
  Summary: Register start of time
- `toc(self, skip_logger)`
  Summary: Register end of time
- `get_steps(self)`
  Summary: Get the number of steps in the simulation
- `run(self)`
  Summary: No docstring provided.
- `copy_signals(self, other)`
  Summary: Copy the signals from another driver
- `report_progress(self, val)`
  Summary: Report progress
- `report_progress2(self, current, total)`
  Summary: Report progress
- `report_done(self, txt, val)`
  Summary: Report done
- `report_text(self, val)`
  Summary: Report text
- `cancel(self)`
  Summary: Cancel the simulation
- `is_cancel(self)`
  Summary: Check if cancel was activated
- `isRunning(self)`
  Summary: :return:
- `get_save_data(self)`
  Summary: Get save data representation of this driver

## Class: TimeSeriesDriverTemplate

- Bases: DriverTemplate
- Summary: Time series driver template

### Methods

- `get_steps(self)`
  Summary: Get time steps list of strings
- `get_fuel_emissions_energy_calculations(self, gen_p, gen_cost)`
  Summary: Calculate fuel emissions and energy cost
