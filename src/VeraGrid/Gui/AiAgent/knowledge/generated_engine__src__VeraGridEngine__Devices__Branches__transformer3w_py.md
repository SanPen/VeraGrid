# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/transformer3w.py

- Original source path: `src/VeraGridEngine/Devices/Branches/transformer3w.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: typing, numpy, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.Devices.Parents.physical_device, VeraGridEngine.Devices.Branches.winding, VeraGridEngine.Devices.Branches.transformer_type,  VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.editable_device

## Function: delta_to_star(z12, z23, z31)

Perform the delta->star transformation

## Function: star_to_delta(z1, z2, z3)

Perform the star->delta transformation

## Class: Transformer3W

- Bases: PhysicalDevice
- Summary: No docstring provided.

### Methods

- `winding1(self)`
  Summary: Winding 1 getter
- `winding1(self, val)`
  Summary: No docstring provided.
- `winding2(self)`
  Summary: Winding 2 getter
- `winding2(self, val)`
  Summary: No docstring provided.
- `winding3(self)`
  Summary: Winding 3 getter
- `winding3(self, val)`
  Summary: No docstring provided.
- `active_prof(self)`
  Summary: Cost profile
- `active_prof(self, val)`
  Summary: No docstring provided.
- `get_active_at(self, t)`
  Summary: :param t:
- `all_connected(self)`
  Summary: Check that all three windings are connected to something
- `bus1(self)`
  Summary: Bus 1
- `bus1(self, obj)`
  Summary: No docstring provided.
- `bus2(self)`
  Summary: Bus 2
- `bus2(self, obj)`
  Summary: No docstring provided.
- `bus3(self)`
  Summary: Bus 3
- `bus3(self, obj)`
  Summary: No docstring provided.
- `V1(self)`
  Summary: Nominal voltage 1 in kV
- `V1(self, val)`
  Summary: No docstring provided.
- `V2(self)`
  Summary: Nominal voltage 2 in kV
- `V2(self, val)`
  Summary: No docstring provided.
- `V3(self)`
  Summary: Nominal voltage 3 in kV
- `V3(self, val)`
  Summary: No docstring provided.
- `compute_delta_to_star(self)`
  Summary: Perform the delta -> star transformation
- `fill_from_star(self, r1, r2, r3, x1, x2, x3)`
  Summary: Fill from Star values
- `r12(self)`
  Summary: 1->2 measured resistance in p.u.
- `r12(self, val)`
  Summary: No docstring provided.
- `r23(self)`
  Summary: 2->3 measured resistance in p.u.
- `r23(self, val)`
  Summary: No docstring provided.
- `r31(self)`
  Summary: 3->1 measured resistance in p.u.
- `r31(self, val)`
  Summary: No docstring provided.
- `x12(self)`
  Summary: 1->2 measured reactance in p.u.
- `x12(self, val)`
  Summary: No docstring provided.
- `x23(self)`
  Summary: 2->3 measured reactance in p.u.
- `x23(self, val)`
  Summary: No docstring provided.
- `x31(self)`
  Summary: 3->1 measured reactance in p.u.
- `x31(self, val)`
  Summary: No docstring provided.
- `rate1(self)`
  Summary: 1 measured rate in MVA
- `rate1(self, val)`
  Summary: No docstring provided.
- `rate2(self)`
  Summary: 2 measured rate in MVA
- `rate2(self, val)`
  Summary: No docstring provided.
- `rate3(self)`
  Summary: 3->1 measured rate in MVA
- `rate3(self, val)`
  Summary: No docstring provided.
- `Pcu12(self)`
  Summary: :return:
- `Pcu12(self, value)`
  Summary: No docstring provided.
- `Pcu23(self)`
  Summary: :return:
- `Pcu23(self, value)`
  Summary: No docstring provided.
- `Pcu31(self)`
  Summary: :return:
- `Pcu31(self, value)`
  Summary: No docstring provided.
- `Vsc12(self)`
  Summary: :return:
- `Vsc12(self, value)`
  Summary: No docstring provided.
- `Vsc23(self)`
  Summary: :return:
- `Vsc23(self, value)`
  Summary: No docstring provided.
- `Vsc31(self)`
  Summary: :return:
- `Vsc31(self, value)`
  Summary: No docstring provided.
- `Pfe(self)`
  Summary: :return:
- `Pfe(self, value)`
  Summary: No docstring provided.
- `I0(self)`
  Summary: :return:
- `I0(self, value)`
  Summary: No docstring provided.
- `get_winding(self, i)`
  Summary: Get winding from an integer
- `_recalc_from_definition(self, Sbase)`
  Summary: Recompute from the definition stored data
- `fill_from_design_values(self, V1, V2, V3, Sn1, Sn2, Sn3, Pcu12, Pcu23, Pcu31, Vsc12, Vsc23, Vsc31, Pfe, I0, Sbase)`
  Summary: Fill winding per unit impedances from the short circuit study values
- `active(self)`
  Summary: Get ``active``.
- `active(self, val)`
  Summary: Set ``active``.
- `x(self)`
  Summary: Get ``x``.
- `x(self, val)`
  Summary: Set ``x``.
- `y(self)`
  Summary: Get ``y``.
- `y(self, val)`
  Summary: Set ``y``.
