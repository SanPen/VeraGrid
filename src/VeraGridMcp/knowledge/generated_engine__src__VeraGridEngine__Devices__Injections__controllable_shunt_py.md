# VeraGridEngine Module: src/VeraGridEngine/Devices/Injections/controllable_shunt.py

- Original source path: `src/VeraGridEngine/Devices/Injections/controllable_shunt.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.shunt_parent,  VeraGridEngine.Devices.Substation.bus, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.basic_structures

## Class: ControllableShunt

- Bases: ShuntParent
- Summary: Controllable Shunt

### Methods

- `step(self)`
  Summary: Step
- `step(self, value)`
  Summary: No docstring provided.
- `g_steps(self)`
  Summary: G steps
- `g_steps(self, value)`
  Summary: No docstring provided.
- `active_steps(self)`
  Summary: G steps
- `active_steps(self, value)`
  Summary: No docstring provided.
- `set_blocks(self, n_list, b_list)`
  Summary: Initialize the steps from block data
- `get_block_points(self)`
  Summary: Get B points for CGMES export.
- `get_cumulative_b(self)`
  Summary: Get the cumulative B values
- `get_cumulative_g(self)`
  Summary: Get the cumulative G values
- `b_steps(self)`
  Summary: B steps
- `b_steps(self, value)`
  Summary: No docstring provided.
- `Vset_prof(self)`
  Summary: Cost profile
- `Vset_prof(self, val)`
  Summary: No docstring provided.
- `get_Vset_at(self, t)`
  Summary: :param t:
- `step_prof(self)`
  Summary: Cost profile
- `step_prof(self, val)`
  Summary: No docstring provided.
- `get_step_at(self, t)`
  Summary: :param t:
- `get_linear_g_steps(self)`
  Summary: :return:
- `get_linear_b_steps(self)`
  Summary: :return:
- `Gmax(self)`
  Summary: Get ``Gmax``.
- `Gmax(self, val)`
  Summary: Set ``Gmax``.
- `Gmin(self)`
  Summary: Get ``Gmin``.
- `Gmin(self, val)`
  Summary: Set ``Gmin``.
- `Bmax(self)`
  Summary: Get ``Bmax``.
- `Bmax(self, val)`
  Summary: Set ``Bmax``.
- `Bmin(self)`
  Summary: Get ``Bmin``.
- `Bmin(self, val)`
  Summary: Set ``Bmin``.
- `Vmin(self)`
  Summary: Get ``Vmin``.
- `Vmin(self, val)`
  Summary: Set ``Vmin``.
- `Vset(self)`
  Summary: Get ``Vset``.
- `Vset(self, val)`
  Summary: Set ``Vset``.
- `Vmax(self)`
  Summary: Get ``Vmax``.
- `Vmax(self, val)`
  Summary: Set ``Vmax``.
