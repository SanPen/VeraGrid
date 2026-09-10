# VeraGridEngine Module: src/VeraGridEngine/Devices/Injections/external_grid.py

- Original source path: `src/VeraGridEngine/Devices/Injections/external_grid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, pandas, matplotlib, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.load_parent,  VeraGridEngine.Devices.Parents.editable_device

## Class: ExternalGrid

- Bases: LoadParent
- Summary: No docstring provided.

### Methods

- `Vm_prof(self)`
  Summary: Cost profile
- `Vm_prof(self, val)`
  Summary: No docstring provided.
- `get_Vm_at(self, t)`
  Summary: :param t:
- `Va_prof(self)`
  Summary: Cost profile
- `Va_prof(self, val)`
  Summary: No docstring provided.
- `get_Va_at(self, t)`
  Summary: :param t:
- `plot_profiles(self, time, show_fig)`
  Summary: Plot the time series results of this object
- `Vm(self)`
  Summary: Get ``Vm``.
- `Vm(self, val)`
  Summary: Set ``Vm``.
- `Va(self)`
  Summary: Get ``Va``.
- `Va(self, val)`
  Summary: Set ``Va``.
