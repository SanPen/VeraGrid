# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/injection_parent.py

- Original source path: `src/VeraGridEngine/Devices/Parents/injection_parent.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices.Parents.dynamic_parent, VeraGridEngine.Devices.Associations.association, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Aggregation.facility, VeraGridEngine.Devices.Parents.editable_device

## Class: InjectionParent

- Bases: DynamicDevice
- Summary: Parent class for Injections

### Methods

- `bus(self)`
  Summary: Bus
- `bus(self, val)`
  Summary: No docstring provided.
- `active_prof(self)`
  Summary: Cost profile
- `active_prof(self, val)`
  Summary: No docstring provided.
- `get_active_at(self, t)`
  Summary: :param t:
- `Cost_prof(self)`
  Summary: Cost profile
- `Cost_prof(self, val)`
  Summary: No docstring provided.
- `get_Cost_at(self, t)`
  Summary: :param t:
- `shift_key_prof(self)`
  Summary: Cost profile
- `shift_key_prof(self, val)`
  Summary: No docstring provided.
- `get_shift_key_at(self, t)`
  Summary: :param t:
- `use_kw(self)`
  Summary: :return:
- `use_kw(self, val)`
  Summary: Setter
- `conn(self)`
  Summary: :return:
- `conn(self, val)`
  Summary: No docstring provided.
- `get_S_with_sign(self)`
  Summary: :return:
- `get_Sprof_with_sign(self)`
  Summary: :return:
- `associate_technology(self, tech, val)`
  Summary: Associate a technology with this injection device
- `tech_list(self)`
  Summary: Bus
- `get_bus_pos(self, bus)`
  Summary: Get the bus position
- `try_to_find_coordinates(self)`
  Summary: Get the latitude and
- `color_by_main_technology(self)`
  Summary: Set the color of the dominant technology
- `color_by_main_owner(self)`
  Summary: Set the color of the dominant owner
- `active(self)`
  Summary: Get ``active``.
- `active(self, val)`
  Summary: Set ``active``.
- `mttf(self)`
  Summary: Get ``mttf``.
- `mttf(self, val)`
  Summary: Set ``mttf``.
- `mttr(self)`
  Summary: Get ``mttr``.
- `mttr(self, val)`
  Summary: Set ``mttr``.
- `capex(self)`
  Summary: Get ``capex``.
- `capex(self, val)`
  Summary: Set ``capex``.
- `opex(self)`
  Summary: Get ``opex``.
- `opex(self, val)`
  Summary: Set ``opex``.
- `Cost(self)`
  Summary: Get ``Cost``.
- `Cost(self, val)`
  Summary: Set ``Cost``.
- `scalable(self)`
  Summary: Get ``scalable``.
- `scalable(self, val)`
  Summary: Set ``scalable``.
- `shift_key(self)`
  Summary: Get ``shift_key``.
- `shift_key(self, val)`
  Summary: Set ``shift_key``.
- `longitude(self)`
  Summary: Get ``longitude``.
- `longitude(self, val)`
  Summary: Set ``longitude``.
- `latitude(self)`
  Summary: Get ``latitude``.
- `latitude(self, val)`
  Summary: Set ``latitude``.
- `bus_pos(self)`
  Summary: Get ``bus_pos``.
- `bus_pos(self, val)`
  Summary: Set ``bus_pos``.
