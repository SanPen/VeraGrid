# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/branch_parent.py

- Original source path: `src/VeraGridEngine/Devices/Parents/branch_parent.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Substation.substation, VeraGridEngine.Devices.Substation.voltage_level, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.dynamic_parent, VeraGridEngine.Devices.Aggregation.branch_group,  VeraGridEngine.Devices.Parents.editable_device

## Class: BranchParent

- Bases: DynamicDevice
- Summary: This class serves to represent the basic branch

### Methods

- `bus_from(self)`
  Summary: Bus
- `bus_from(self, val)`
  Summary: No docstring provided.
- `bus_to(self)`
  Summary: Bus
- `bus_to(self, val)`
  Summary: No docstring provided.
- `active_prof(self)`
  Summary: Cost profile
- `active_prof(self, val)`
  Summary: No docstring provided.
- `get_active_at(self, t)`
  Summary: :param t:
- `rate_prof(self)`
  Summary: Cost profile
- `rate_prof(self, val)`
  Summary: No docstring provided.
- `get_rate_at(self, t)`
  Summary: :param t:
- `contingency_factor_prof(self)`
  Summary: Cost profile
- `contingency_factor_prof(self, val)`
  Summary: No docstring provided.
- `get_contingency_factor_at(self, t)`
  Summary: :param t:
- `protection_rating_factor_prof(self)`
  Summary: Cost profile
- `protection_rating_factor_prof(self, val)`
  Summary: No docstring provided.
- `get_protection_rating_factor_at(self, t)`
  Summary: :param t:
- `Cost_prof(self)`
  Summary: Cost profile
- `Cost_prof(self, val)`
  Summary: No docstring provided.
- `get_Cost_at(self, t)`
  Summary: :param t:
- `temp_oper_prof(self)`
  Summary: Cost profile
- `temp_oper_prof(self, val)`
  Summary: No docstring provided.
- `get_temp_oper_at(self, t)`
  Summary: :param t:
- `rate(self)`
  Summary: Rate (MVA)
- `rate(self, val)`
  Summary: No docstring provided.
- `contingency_factor(self)`
  Summary: Rate (MVA)
- `contingency_factor(self, val)`
  Summary: No docstring provided.
- `protection_rating_factor(self)`
  Summary: Rate (MVA)
- `protection_rating_factor(self, val)`
  Summary: No docstring provided.
- `get_max_bus_nominal_voltage(self)`
  Summary: GEt the maximum nominal voltage
- `get_min_bus_nominal_voltage(self)`
  Summary: Get the minimum nominal voltage
- `get_sorted_buses_voltages(self)`
  Summary: Get the sorted bus voltages
- `get_buses_sorted_by_voltage(self)`
  Summary: Get the sorted buses
- `get_virtual_taps(self)`
  Summary: Get the branch virtual taps
- `get_coordinates(self)`
  Summary: Get the line defining coordinates
- `convertible_to_vsc(self)`
  Summary: Is this line convertible to VSC?
- `Vf(self)`
  Summary: Get the voltage "from" (kV)
- `Vt(self)`
  Summary: Get the voltage "to" (kV)
- `should_this_be_a_transformer(self, branch_connection_voltage_tolerance, logger)`
  Summary: Check if this line should be a transformer
- `get_substation_from(self)`
  Summary: Try to get the substation at the From side
- `get_substation_to(self)`
  Summary: Try to get the substation at the To side
- `get_voltage_level_from(self)`
  Summary: Try to get the voltage level at the From side
- `get_voltage_level_to(self)`
  Summary: Try to get the voltage level at the To side
- `get_from_and_to_objects(self)`
  Summary: Get the from and to connection objects of the branch
- `get_weight(self)`
  Summary: Get a weight of this line for graph purposes
- `get_bus_pos(self, bus)`
  Summary: Get the bus specified position
- `reassign_bus(self, old_bus, new_bus)`
  Summary: Re-assign a bus
- `active(self)`
  Summary: Get ``active``.
- `active(self, val)`
  Summary: Set ``active``.
- `reducible(self)`
  Summary: Get ``reducible``.
- `reducible(self, val)`
  Summary: Set ``reducible``.
- `monitor_loading(self)`
  Summary: Get ``monitor_loading``.
- `monitor_loading(self, val)`
  Summary: Set ``monitor_loading``.
- `mttf(self)`
  Summary: Get ``mttf``.
- `mttf(self, val)`
  Summary: Set ``mttf``.
- `mttr(self)`
  Summary: Get ``mttr``.
- `mttr(self, val)`
  Summary: Set ``mttr``.
- `Cost(self)`
  Summary: Get ``Cost``.
- `Cost(self, val)`
  Summary: Set ``Cost``.
- `capex(self)`
  Summary: Get ``capex``.
- `capex(self, val)`
  Summary: Set ``capex``.
- `opex(self)`
  Summary: Get ``opex``.
- `opex(self, val)`
  Summary: Set ``opex``.
- `bus_from_pos(self)`
  Summary: Get ``bus_from_pos``.
- `bus_from_pos(self, val)`
  Summary: Set ``bus_from_pos``.
- `bus_to_pos(self)`
  Summary: Get ``bus_to_pos``.
- `bus_to_pos(self, val)`
  Summary: Set ``bus_to_pos``.
- `temp_base(self)`
  Summary: Get ``temp_base``.
- `temp_base(self, val)`
  Summary: Set ``temp_base``.
- `temp_oper(self)`
  Summary: Get ``temp_oper``.
- `temp_oper(self, val)`
  Summary: Set ``temp_oper``.
- `alpha(self)`
  Summary: Get ``alpha``.
- `alpha(self, val)`
  Summary: Set ``alpha``.
