# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/tap_changer.py

- Original source path: `src/VeraGridEngine/Devices/Branches/tap_changer.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, pandas, typing, VeraGridEngine.Utils.NumericalMethods.common, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: TapChanger

- Bases: none
- Summary: Tap changer

### Methods

- `copy(self)`
  Summary: :return:
- `asymmetry_angle(self)`
  Summary: No docstring provided.
- `asymmetry_angle(self, asymmetry_angle)`
  Summary: No docstring provided.
- `dV(self)`
  Summary: No docstring provided.
- `dV(self, dV)`
  Summary: No docstring provided.
- `normal_position(self)`
  Summary: No docstring provided.
- `normal_position(self, normal_position)`
  Summary: No docstring provided.
- `tc_type(self)`
  Summary: No docstring provided.
- `tc_type(self, tc_type)`
  Summary: No docstring provided.
- `total_positions(self)`
  Summary: Tap changer total number of positions
- `total_positions(self, value)`
  Summary: No docstring provided.
- `tap_position(self)`
  Summary: Get the tap position
- `tap_position(self, val)`
  Summary: Set the tap position (zero indexing)
- `neutral_position(self)`
  Summary: Get the neutral position
- `neutral_position(self, val)`
  Summary: Set the neutral position
- `tap_modules_array(self)`
  Summary: Get the tap modules array
- `tap_angles_array(self)`
  Summary: :return:
- `resize(self)`
  Summary: Resize and recalc the tap positions array
- `recalc(self)`
  Summary: Recalculate the phase and modules corresponding to each tap position
- `to_dict(self)`
  Summary: Get a dictionary representation of the tap
- `parse(self, data, logger)`
  Summary: Parse the tap data
- `to_df(self)`
  Summary: Get DaraFrame of the values
- `reset(self)`
  Summary: Resets the tap changer to the neutral position
- `tap_up(self)`
  Summary: Go to the next upper tap position
- `tap_down(self)`
  Summary: Go to the next upper tap position
- `get_tap_phase2(self, tap_position)`
  Summary: Get the tap phase in radians
- `get_tap_module2(self, tap_position)`
  Summary: Get the tap voltage regulation module
- `get_tap_phase(self)`
  Summary: Get the tap phase in radians
- `get_tap_module(self)`
  Summary: Get the tap voltage regulation module
- `set_tap_module(self, tap_module)`
  Summary: Set the tap position closest to the tap module
- `set_tap_phase(self, tap_phase)`
  Summary: Set the tap position closest to the tap phase
- `get_tap_module_min(self)`
  Summary: Min tap module, computed on the fly
- `get_tap_module_max(self)`
  Summary: Max tap module, computed on the fly
- `get_tap_phase_min(self)`
  Summary: Min tap phase, computed on the fly
- `get_tap_phase_max(self)`
  Summary: Maximum tap phase (calculated)
- `init_from_cgmes(self, low, high, normal, neutral, stepVoltageIncrement, step, asymmetry_angle, tc_type)`
  Summary: Import TapChanger object from CGMES
- `get_cgmes_values(self)`
  Summary: Returns with values of a Tap Changer in CGMES
