# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/transformer_type.py

- Original source path: `src/VeraGridEngine/Devices/Branches/transformer_type.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: typing, numpy, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Parents.dynamic_parent, VeraGridEngine.Devices.Branches.tap_changer

## Class: TransformerType

- Bases: DynamicDevice
- Summary: No docstring provided.

### Methods

- `tap_module_min(self)`
  Summary: Min tap module, computed on the fly
- `tap_module_min(self, val)`
  Summary: No docstring provided.
- `tap_module_max(self)`
  Summary: Max tap module, computed on the fly
- `tap_module_max(self, val)`
  Summary: No docstring provided.
- `tap_phase_min(self)`
  Summary: Min tap phase, cputed on the fly
- `tap_phase_min(self, val)`
  Summary: No docstring provided.
- `tap_phase_max(self)`
  Summary: Maximum tap phase (calculated)
- `tap_phase_max(self, val)`
  Summary: No docstring provided.
- `total_positions(self)`
  Summary: Tap changer total number of positions
- `total_positions(self, value)`
  Summary: No docstring provided.
- `neutral_position(self)`
  Summary: Tap changer neutral position
- `neutral_position(self, value)`
  Summary: No docstring provided.
- `dV(self)`
  Summary: Tap changer Voltage increment per step (p.u.)
- `dV(self, value)`
  Summary: No docstring provided.
- `asymmetry_angle(self)`
  Summary: Tap changer assymetry angle (deg)
- `asymmetry_angle(self, value)`
  Summary: No docstring provided.
- `tc_type(self)`
  Summary: Get the tap changer type
- `tc_type(self, value)`
  Summary: No docstring provided.
- `get_impedances(self, VH, VL, Sbase)`
  Summary: Compute the branch parameters of a transformer from the short circuit test
- `get_tap_changer(self)`
  Summary: Get tap changer object
- `HV(self)`
  Summary: Get ``HV``.
- `HV(self, val)`
  Summary: Set ``HV``.
- `LV(self)`
  Summary: Get ``LV``.
- `LV(self, val)`
  Summary: Set ``LV``.
- `Sn(self)`
  Summary: Get ``Sn``.
- `Sn(self, val)`
  Summary: Set ``Sn``.
- `Pcu(self)`
  Summary: Get ``Pcu``.
- `Pcu(self, val)`
  Summary: Set ``Pcu``.
- `Pfe(self)`
  Summary: Get ``Pfe``.
- `Pfe(self, val)`
  Summary: Set ``Pfe``.
- `I0(self)`
  Summary: Get ``I0``.
- `I0(self, val)`
  Summary: Set ``I0``.
- `Vsc(self)`
  Summary: Get ``Vsc``.
- `Vsc(self, val)`
  Summary: Set ``Vsc``.
- `capex(self)`
  Summary: Get ``capex``.
- `capex(self, val)`
  Summary: Set ``capex``.
- `opex(self)`
  Summary: Get ``opex``.
- `opex(self, val)`
  Summary: Set ``opex``.
- `vector_group_number(self)`
  Summary: Get ``vector_group_number``.
- `vector_group_number(self, val)`
  Summary: Set ``vector_group_number``.

## Function: get_impedances(VH_bus, VL_bus, Sn, HV, LV, Pcu, Pfe, I0, Vsc, Sbase, GR_hv1)

Compute the branch parameters of a transformer from the short circuit test

## Function: reverse_transformer_short_circuit_study(R, X, G, B, rate, Sbase)

Get the short circuit study values from the impedance values
