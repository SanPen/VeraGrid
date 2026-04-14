# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/vsc.py

- Original source path: `src/VeraGridEngine/Devices/Branches/vsc.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, pandas, numpy, matplotlib, typing,  VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.branch_parent, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Parents.editable_device

## Class: VSC

- Bases: BranchParent
- Summary: No docstring provided.

### Methods

- `bus_from(self)`
  Summary: Get the DC positive bus
- `bus_from(self, value)`
  Summary: No docstring provided.
- `bus_dc_n(self)`
  Summary: Get the DC negative bus
- `bus_dc_n(self, value)`
  Summary: No docstring provided.
- `bus_to(self)`
  Summary: Get the AC bus
- `bus_to(self, value)`
  Summary: No docstring provided.
- `control1(self)`
  Summary: :return:
- `control1(self, value)`
  Summary: No docstring provided.
- `control1_prof(self)`
  Summary: Cost profile
- `control1_prof(self, val)`
  Summary: No docstring provided.
- `get_control1_at(self, t)`
  Summary: :param t:
- `control2(self)`
  Summary: :return:
- `control2(self, value)`
  Summary: No docstring provided.
- `control2_prof(self)`
  Summary: Cost profile
- `control2_prof(self, val)`
  Summary: No docstring provided.
- `get_control2_at(self, t)`
  Summary: :param t:
- `control1_val(self)`
  Summary: :return:
- `control1_val(self, value)`
  Summary: No docstring provided.
- `control1_val_prof(self)`
  Summary: Cost profile
- `control1_val_prof(self, val)`
  Summary: No docstring provided.
- `get_control1_val_at(self, t)`
  Summary: :param t:
- `control2_val(self)`
  Summary: :return:
- `control2_val(self, value)`
  Summary: No docstring provided.
- `control2_val_prof(self)`
  Summary: Cost profile
- `control2_val_prof(self, val)`
  Summary: No docstring provided.
- `get_control2_val_at(self, t)`
  Summary: :param t:
- `control1_dev(self)`
  Summary: :return:
- `control1_dev(self, value)`
  Summary: No docstring provided.
- `control1_dev_prof(self)`
  Summary: Cost profile
- `control1_dev_prof(self, val)`
  Summary: No docstring provided.
- `get_control1_dev_at(self, t)`
  Summary: :param t:
- `control2_dev(self)`
  Summary: :return:
- `control2_dev(self, value)`
  Summary: No docstring provided.
- `control2_dev_prof(self)`
  Summary: Cost profile
- `control2_dev_prof(self, val)`
  Summary: No docstring provided.
- `get_control2_dev_at(self, t)`
  Summary: :param t:
- `get_coordinates(self)`
  Summary: Get the line defining coordinates
- `plot_profiles(self, time_series, my_index, show_fig)`
  Summary: Plot the time series results of this object
- `is_3term(self)`
  Summary: Is this a 3-terminal VSC?
- `alpha1(self)`
  Summary: Get ``alpha1``.
- `alpha1(self, val)`
  Summary: Set ``alpha1``.
- `alpha2(self)`
  Summary: Get ``alpha2``.
- `alpha2(self, val)`
  Summary: Set ``alpha2``.
- `alpha3(self)`
  Summary: Get ``alpha3``.
- `alpha3(self, val)`
  Summary: Set ``alpha3``.
- `kdp(self)`
  Summary: Get ``kdp``.
- `kdp(self, val)`
  Summary: Set ``kdp``.
- `min_ac_voltage(self)`
  Summary: Get ``min_ac_voltage``.
- `min_ac_voltage(self, val)`
  Summary: Set ``min_ac_voltage``.
- `x(self)`
  Summary: Get ``x``.
- `x(self, val)`
  Summary: Set ``x``.
- `y(self)`
  Summary: Get ``y``.
- `y(self, val)`
  Summary: Set ``y``.
