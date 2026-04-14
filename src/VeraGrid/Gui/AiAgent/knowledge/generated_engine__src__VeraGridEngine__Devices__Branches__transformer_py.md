# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/transformer.py

- Original source path: `src/VeraGridEngine/Devices/Branches/transformer.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.controllable_branch_parent, VeraGridEngine.Devices.Branches.transformer_type, VeraGridEngine.Devices.Parents.editable_device

## Class: Transformer2W

- Bases: ControllableBranchParent
- Summary: No docstring provided.

### Methods

- `conn_f(self)`
  Summary: No docstring provided.
- `conn_f(self, val)`
  Summary: No docstring provided.
- `conn_t(self)`
  Summary: No docstring provided.
- `conn_t(self, val)`
  Summary: No docstring provided.
- `vector_group_number(self)`
  Summary: No docstring provided.
- `vector_group_number(self, val)`
  Summary: No docstring provided.
- `phases(self)`
  Summary: No docstring provided.
- `phases(self, val)`
  Summary: No docstring provided.
- `set_hv_and_lv(self, HV, LV)`
  Summary: set the high and low voltage values
- `get_from_to_nominal_voltages(self)`
  Summary: :return:
- `get_virtual_taps(self)`
  Summary: Get the branch virtual taps
- `apply_template(self, obj, Sbase, logger)`
  Summary: Apply a branch template to this object
- `delete_virtual_taps(self)`
  Summary: Set the HV and LV parameters such that any virtual tap is null
- `fix_inconsistencies(self, logger, maximum_difference)`
  Summary: Fix the inconsistencies
- `fill_design_properties(self, Pcu, Pfe, I0, Vsc, Sbase, round_vals)`
  Summary: Fill R, X, G, B from the short circuit study values
- `get_vcc(self)`
  Summary: Get the short circuit voltage in %
- `get_transformer_type(self, Sbase)`
  Summary: Get the equivalent transformer type of this transformer
- `transformer_phases(self, logger)`
  Summary: No docstring provided.
- `transformer_admittance(self, vtap_f, vtap_t, logger)`
  Summary: Get the transformer 3-phase primitives
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
