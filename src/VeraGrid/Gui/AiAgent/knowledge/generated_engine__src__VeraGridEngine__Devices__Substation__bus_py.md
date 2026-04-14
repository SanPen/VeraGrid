# VeraGridEngine Module: src/VeraGridEngine/Devices/Substation/bus.py

- Original source path: `src/VeraGridEngine/Devices/Substation/bus.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, pandas, matplotlib, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.dynamic_parent, VeraGridEngine.Devices.Aggregation, VeraGridEngine.Devices.Substation.substation, VeraGridEngine.Devices.Substation.busbar, VeraGridEngine.Devices.Substation.voltage_level,  VeraGridEngine.Devices.Parents.editable_device

## Class: Bus

- Bases: DynamicDevice
- Summary: No docstring provided.

### Methods

- `active_prof(self)`
  Summary: Cost profile
- `active_prof(self, val)`
  Summary: No docstring provided.
- `get_active_at(self, t)`
  Summary: :param t:
- `Vmin_prof(self)`
  Summary: Pmin profile
- `Vmin_prof(self, val)`
  Summary: No docstring provided.
- `get_Vmin_at(self, t)`
  Summary: :param t:
- `Vmax_prof(self)`
  Summary: Pmin profile
- `Vmax_prof(self, val)`
  Summary: No docstring provided.
- `get_Vmax_at(self, t)`
  Summary: :param t:
- `voltage_level(self)`
  Summary: voltage_level getter
- `voltage_level(self, val)`
  Summary: voltage_level getter
- `determine_bus_type(self)`
  Summary: Infer the bus type from the devices attached to it
- `get_voltage_guess(self, use_stored_guess)`
  Summary: Determine the voltage initial guess
- `plot_profiles(self, time_profile, ax_load, ax_voltage, time_series_driver, my_index)`
  Summary: plot the profiles of this bus
- `get_fault_impedance(self)`
  Summary: Get the fault impedance
- `get_coordinates(self)`
  Summary: Get tuple of the bus coordinates (longitude, latitude)
- `try_to_find_coordinates(self)`
  Summary: Try to find the bus coordinates
- `internal(self)`
  Summary: Is the bus internal?
- `internal(self, val)`
  Summary: No docstring provided.
- `bus_bar(self)`
  Summary: Get the BusBar
- `bus_bar(self, val)`
  Summary: No docstring provided.
- `active(self)`
  Summary: Get ``active``.
- `active(self, val)`
  Summary: Set ``active``.
- `is_slack(self)`
  Summary: Get ``is_slack``.
- `is_slack(self, val)`
  Summary: Set ``is_slack``.
- `is_dc(self)`
  Summary: Get ``is_dc``.
- `is_dc(self, val)`
  Summary: Set ``is_dc``.
- `Vnom(self)`
  Summary: Get ``Vnom``.
- `Vnom(self, val)`
  Summary: Set ``Vnom``.
- `Vm0(self)`
  Summary: Get ``Vm0``.
- `Vm0(self, val)`
  Summary: Set ``Vm0``.
- `Va0(self)`
  Summary: Get ``Va0``.
- `Va0(self, val)`
  Summary: Set ``Va0``.
- `Vmin(self)`
  Summary: Get ``Vmin``.
- `Vmin(self, val)`
  Summary: Set ``Vmin``.
- `Vmax(self)`
  Summary: Get ``Vmax``.
- `Vmax(self, val)`
  Summary: Set ``Vmax``.
- `Vm_cost(self)`
  Summary: Get ``Vm_cost``.
- `Vm_cost(self, val)`
  Summary: Set ``Vm_cost``.
- `angle_min(self)`
  Summary: Get ``angle_min``.
- `angle_min(self, val)`
  Summary: Set ``angle_min``.
- `angle_max(self)`
  Summary: Get ``angle_max``.
- `angle_max(self, val)`
  Summary: Set ``angle_max``.
- `angle_cost(self)`
  Summary: Get ``angle_cost``.
- `angle_cost(self, val)`
  Summary: Set ``angle_cost``.
- `r_fault(self)`
  Summary: Get ``r_fault``.
- `r_fault(self, val)`
  Summary: Set ``r_fault``.
- `x_fault(self)`
  Summary: Get ``x_fault``.
- `x_fault(self, val)`
  Summary: Set ``x_fault``.
- `x(self)`
  Summary: Get ``x``.
- `x(self, val)`
  Summary: Set ``x``.
- `y(self)`
  Summary: Get ``y``.
- `y(self, val)`
  Summary: Set ``y``.
- `h(self)`
  Summary: Get ``h``.
- `h(self, val)`
  Summary: Set ``h``.
- `w(self)`
  Summary: Get ``w``.
- `w(self, val)`
  Summary: Set ``w``.
- `longitude(self)`
  Summary: Get ``longitude``.
- `longitude(self, val)`
  Summary: Set ``longitude``.
- `latitude(self)`
  Summary: Get ``latitude``.
- `latitude(self, val)`
  Summary: Set ``latitude``.
- `is_grounded(self)`
  Summary: Get ``is_grounded``.
- `is_grounded(self, val)`
  Summary: Set ``is_grounded``.
