# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/shunt_parent.py

- Original source path: `src/VeraGridEngine/Devices/Parents/shunt_parent.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, pandas, matplotlib, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations,  VeraGridEngine.Devices.Parents.injection_parent, VeraGridEngine.Devices.admittance_matrix, VeraGridEngine.Devices.Parents.editable_device

## Class: ShuntParent

- Bases: InjectionParent
- Summary: Template for objects that behave like shunts

### Methods

- `G_prof(self)`
  Summary: Cost profile
- `G_prof(self, val)`
  Summary: No docstring provided.
- `get_G_at(self, t)`
  Summary: :param t:
- `Ga_prof(self)`
  Summary: Cost profile
- `Ga_prof(self, val)`
  Summary: No docstring provided.
- `get_Ga_at(self, t)`
  Summary: :param t:
- `Gb_prof(self)`
  Summary: Cost profile
- `Gb_prof(self, val)`
  Summary: No docstring provided.
- `get_Gb_at(self, t)`
  Summary: :param t:
- `Gc_prof(self)`
  Summary: Cost profile
- `Gc_prof(self, val)`
  Summary: No docstring provided.
- `get_Gc_at(self, t)`
  Summary: :param t:
- `B_prof(self)`
  Summary: Cost profile
- `B_prof(self, val)`
  Summary: No docstring provided.
- `get_B_at(self, t)`
  Summary: :param t:
- `Ba_prof(self)`
  Summary: Cost profile
- `Ba_prof(self, val)`
  Summary: No docstring provided.
- `get_Ba_at(self, t)`
  Summary: :param t:
- `Bb_prof(self)`
  Summary: Cost profile
- `Bb_prof(self, val)`
  Summary: No docstring provided.
- `get_Bb_at(self, t)`
  Summary: :param t:
- `Bc_prof(self)`
  Summary: Cost profile
- `Bc_prof(self, val)`
  Summary: No docstring provided.
- `get_Bc_at(self, t)`
  Summary: :param t:
- `G0_prof(self)`
  Summary: Cost profile
- `G0_prof(self, val)`
  Summary: No docstring provided.
- `get_G0_at(self, t)`
  Summary: :param t:
- `B0_prof(self)`
  Summary: Cost profile
- `B0_prof(self, val)`
  Summary: No docstring provided.
- `get_B0_at(self, t)`
  Summary: :param t:
- `ysh(self)`
  Summary: Shunt admittance matrix (4x4)
- `ysh(self, val)`
  Summary: No docstring provided.
- `get_Y_at(self, t)`
  Summary: :param t:
- `get_Ya_at(self, t)`
  Summary: :param t:
- `get_Yb_at(self, t)`
  Summary: :param t:
- `get_Yc_at(self, t)`
  Summary: :param t:
- `plot_profiles(self, time, show_fig)`
  Summary: Plot the time series results of this object
- `fill_3_phase_from_sequence(self)`
  Summary: Fill the admittance
- `G(self)`
  Summary: Get ``G``.
- `G(self, val)`
  Summary: Set ``G``.
- `G0(self)`
  Summary: Get ``G0``.
- `G0(self, val)`
  Summary: Set ``G0``.
- `Ga(self)`
  Summary: Get ``Ga``.
- `Ga(self, val)`
  Summary: Set ``Ga``.
- `Gb(self)`
  Summary: Get ``Gb``.
- `Gb(self, val)`
  Summary: Set ``Gb``.
- `Gc(self)`
  Summary: Get ``Gc``.
- `Gc(self, val)`
  Summary: Set ``Gc``.
- `B(self)`
  Summary: Get ``B``.
- `B(self, val)`
  Summary: Set ``B``.
- `B0(self)`
  Summary: Get ``B0``.
- `B0(self, val)`
  Summary: Set ``B0``.
- `Ba(self)`
  Summary: Get ``Ba``.
- `Ba(self, val)`
  Summary: Set ``Ba``.
- `Bb(self)`
  Summary: Get ``Bb``.
- `Bb(self, val)`
  Summary: Set ``Bb``.
- `Bc(self)`
  Summary: Get ``Bc``.
- `Bc(self, val)`
  Summary: Set ``Bc``.
