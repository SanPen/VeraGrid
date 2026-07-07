# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/controllable_branch_parent.py

- Original source path: `src/VeraGridEngine/Devices/Parents/controllable_branch_parent.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.branch_parent, VeraGridEngine.Devices.Branches.tap_changer, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.profile

## Class: ControllableBranchParent

- Bases: BranchParent
- Summary: No docstring provided.

### Methods

- `tap_module_prof(self)`
  Summary: Cost profile
- `tap_module_prof(self, val)`
  Summary: No docstring provided.
- `get_tap_module_at(self, t)`
  Summary: :param t:
- `tap_phase_prof(self)`
  Summary: Cost profile
- `tap_phase_prof(self, val)`
  Summary: No docstring provided.
- `get_tap_phase_at(self, t)`
  Summary: :param t:
- `vset_prof(self)`
  Summary: vset profile
- `vset_prof(self, val)`
  Summary: No docstring provided.
- `get_vset_at(self, t)`
  Summary: :param t:
- `Pset_prof(self)`
  Summary: vset profile
- `Pset_prof(self, val)`
  Summary: No docstring provided.
- `get_Pset_at(self, t)`
  Summary: :param t:
- `Qset_prof(self)`
  Summary: vset profile
- `Qset_prof(self, val)`
  Summary: No docstring provided.
- `get_Qset_at(self, t)`
  Summary: :param t:
- `tap_module_control_mode_prof(self)`
  Summary: _tap_module_control_mode_prof profile
- `tap_module_control_mode_prof(self, val)`
  Summary: No docstring provided.
- `get_tap_module_control_mode_at(self, t)`
  Summary: :param t:
- `tap_phase_control_mode_prof(self)`
  Summary: tap_phase_control_mode_prof profile
- `tap_phase_control_mode_prof(self, val)`
  Summary: No docstring provided.
- `get_tap_phase_control_mode_at(self, t)`
  Summary: :param t:
- `tap_module_min(self)`
  Summary: :return:
- `tap_module_min(self, val)`
  Summary: No docstring provided.
- `tap_module_max(self)`
  Summary: :return:
- `tap_module_max(self, val)`
  Summary: No docstring provided.
- `tap_phase_min(self)`
  Summary: :return:
- `tap_phase_min(self, val)`
  Summary: No docstring provided.
- `tap_phase_max(self)`
  Summary: :return:
- `tap_phase_max(self, val)`
  Summary: No docstring provided.
- `tap_changer(self)`
  Summary: Cost profile
- `tap_changer(self, val)`
  Summary: No docstring provided.
- `tap_phase_control_mode(self)`
  Summary: Get the tap phase control mode
- `tap_phase_control_mode(self, val)`
  Summary: No docstring provided.
- `tap_module_control_mode(self)`
  Summary: Get the tap module control mode
- `tap_module_control_mode(self, val)`
  Summary: No docstring provided.
- `R_corrected(self)`
  Summary: Returns a temperature corrected resistance based on a formula provided by:
- `change_base(self, Sbase_old, Sbase_new)`
  Summary: Change the impedance base
- `get_weight(self)`
  Summary: Get a weight for the graphs
- `flip(self)`
  Summary: Change the terminals' positions
- `set_tap_controls(self, tap_phase_control_mode, tap_module_control_mode)`
  Summary: Set both tap controls
- `tap_up(self)`
  Summary: Move the tap changer one position up
- `tap_down(self)`
  Summary: Move the tap changer one position up
- `apply_tap_changer(self, tap_changer)`
  Summary: Apply a new tap changer
- `R(self)`
  Summary: Get ``R``.
- `R(self, val)`
  Summary: Set ``R``.
- `X(self)`
  Summary: Get ``X``.
- `X(self, val)`
  Summary: Set ``X``.
- `G(self)`
  Summary: Get ``G``.
- `G(self, val)`
  Summary: Set ``G``.
- `B(self)`
  Summary: Get ``B``.
- `B(self, val)`
  Summary: Set ``B``.
- `R0(self)`
  Summary: Get ``R0``.
- `R0(self, val)`
  Summary: Set ``R0``.
- `X0(self)`
  Summary: Get ``X0``.
- `X0(self, val)`
  Summary: Set ``X0``.
- `G0(self)`
  Summary: Get ``G0``.
- `G0(self, val)`
  Summary: Set ``G0``.
- `B0(self)`
  Summary: Get ``B0``.
- `B0(self, val)`
  Summary: Set ``B0``.
- `R2(self)`
  Summary: Get ``R2``.
- `R2(self, val)`
  Summary: Set ``R2``.
- `X2(self)`
  Summary: Get ``X2``.
- `X2(self, val)`
  Summary: Set ``X2``.
- `G2(self)`
  Summary: Get ``G2``.
- `G2(self, val)`
  Summary: Set ``G2``.
- `B2(self)`
  Summary: Get ``B2``.
- `B2(self, val)`
  Summary: Set ``B2``.
- `tolerance(self)`
  Summary: Get ``tolerance``.
- `tolerance(self, val)`
  Summary: Set ``tolerance``.
- `tap_module(self)`
  Summary: Get ``tap_module``.
- `tap_module(self, val)`
  Summary: Set ``tap_module``.
- `vset(self)`
  Summary: Get ``vset``.
- `vset(self, val)`
  Summary: Set ``vset``.
- `Qset(self)`
  Summary: Get ``Qset``.
- `Qset(self, val)`
  Summary: Set ``Qset``.
- `tap_phase(self)`
  Summary: Get ``tap_phase``.
- `tap_phase(self, val)`
  Summary: Set ``tap_phase``.
- `Pset(self)`
  Summary: Get ``Pset``.
- `Pset(self, val)`
  Summary: Set ``Pset``.
