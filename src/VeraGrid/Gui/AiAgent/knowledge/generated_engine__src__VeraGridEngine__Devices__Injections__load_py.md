# VeraGridEngine Module: src/VeraGridEngine/Devices/Injections/load.py

- Original source path: `src/VeraGridEngine/Devices/Injections/load.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, pandas, matplotlib, VeraGridEngine.Templates.Rms.load_rms_template, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.load_parent,  VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Devices.Parents.editable_device

## Class: Load

- Bases: LoadParent
- Summary: Load

### Methods

- `Ir_prof(self)`
  Summary: Cost profile
- `Ir_prof(self, val)`
  Summary: No docstring provided.
- `get_Ir_at(self, t)`
  Summary: :param t:
- `Ir1_prof(self)`
  Summary: Cost profile
- `Ir1_prof(self, val)`
  Summary: No docstring provided.
- `get_Ir1_at(self, t)`
  Summary: :param t:
- `Ir2_prof(self)`
  Summary: Cost profile
- `Ir2_prof(self, val)`
  Summary: No docstring provided.
- `get_Ir2_at(self, t)`
  Summary: :param t:
- `Ir3_prof(self)`
  Summary: Cost profile
- `Ir3_prof(self, val)`
  Summary: No docstring provided.
- `get_Ir3_at(self, t)`
  Summary: :param t:
- `Ii_prof(self)`
  Summary: Cost profile
- `Ii_prof(self, val)`
  Summary: No docstring provided.
- `get_Ii_at(self, t)`
  Summary: :param t:
- `Ii1_prof(self)`
  Summary: Cost profile
- `Ii1_prof(self, val)`
  Summary: No docstring provided.
- `get_Ii1_at(self, t)`
  Summary: :param t:
- `Ii2_prof(self)`
  Summary: Cost profile
- `Ii2_prof(self, val)`
  Summary: No docstring provided.
- `get_Ii2_at(self, t)`
  Summary: :param t:
- `Ii3_prof(self)`
  Summary: Cost profile
- `Ii3_prof(self, val)`
  Summary: No docstring provided.
- `get_Ii3_at(self, t)`
  Summary: :param t:
- `G_prof(self)`
  Summary: Cost profile
- `G_prof(self, val)`
  Summary: No docstring provided.
- `get_G_at(self, t)`
  Summary: :param t:
- `G1_prof(self)`
  Summary: Cost profile
- `G1_prof(self, val)`
  Summary: No docstring provided.
- `get_G1_at(self, t)`
  Summary: :param t:
- `G2_prof(self)`
  Summary: Cost profile
- `G2_prof(self, val)`
  Summary: No docstring provided.
- `get_G2_at(self, t)`
  Summary: :param t:
- `G3_prof(self)`
  Summary: Cost profile
- `G3_prof(self, val)`
  Summary: No docstring provided.
- `get_G3_at(self, t)`
  Summary: :param t:
- `B_prof(self)`
  Summary: Cost profile
- `B_prof(self, val)`
  Summary: No docstring provided.
- `get_B_at(self, t)`
  Summary: :param t:
- `B1_prof(self)`
  Summary: Cost profile
- `B1_prof(self, val)`
  Summary: No docstring provided.
- `get_B1_at(self, t)`
  Summary: :param t:
- `B2_prof(self)`
  Summary: Cost profile
- `B2_prof(self, val)`
  Summary: No docstring provided.
- `get_B2_at(self, t)`
  Summary: :param t:
- `B3_prof(self)`
  Summary: Cost profile
- `B3_prof(self, val)`
  Summary: No docstring provided.
- `get_B3_at(self, t)`
  Summary: :param t:
- `get_I_at(self, t)`
  Summary: :param t:
- `get_I1_at(self, t)`
  Summary: :param t:
- `get_I2_at(self, t)`
  Summary: :param t:
- `get_I3_at(self, t)`
  Summary: :param t:
- `get_Y_at(self, t)`
  Summary: :param t:
- `get_Y1_at(self, t)`
  Summary: :param t:
- `get_Y2_at(self, t)`
  Summary: :param t:
- `get_Y3_at(self, t)`
  Summary: :param t:
- `get_Y_conj_at(self, t)`
  Summary: :param t:
- `get_Y1_conj_at(self, t)`
  Summary: :param t:
- `get_Y2_conj_at(self, t)`
  Summary: :param t:
- `get_Y3_conj_at(self, t)`
  Summary: :param t:
- `n_customers(self)`
  Summary: Return the number of customers
- `n_customers(self, val)`
  Summary: Set the number of customers
- `contract_power(self)`
  Summary: Return the contracted power
- `contract_power(self, val)`
  Summary: Set the contracted power
- `n_customers_prof(self)`
  Summary: Cost profile
- `n_customers_prof(self, val)`
  Summary: No docstring provided.
- `assign_input_vars_and_params(self)`
  Summary: No docstring provided.
- `plot_profiles(self, time, show_fig)`
  Summary: Plot the time series results of this object
- `initialize_rms(self, rms_event)`
  Summary: :param rms_event:
- `Ir(self)`
  Summary: Get ``Ir``.
- `Ir(self, val)`
  Summary: Set ``Ir``.
- `Ir1(self)`
  Summary: Get ``Ir1``.
- `Ir1(self, val)`
  Summary: Set ``Ir1``.
- `Ir2(self)`
  Summary: Get ``Ir2``.
- `Ir2(self, val)`
  Summary: Set ``Ir2``.
- `Ir3(self)`
  Summary: Get ``Ir3``.
- `Ir3(self, val)`
  Summary: Set ``Ir3``.
- `Ii(self)`
  Summary: Get ``Ii``.
- `Ii(self, val)`
  Summary: Set ``Ii``.
- `Ii1(self)`
  Summary: Get ``Ii1``.
- `Ii1(self, val)`
  Summary: Set ``Ii1``.
- `Ii2(self)`
  Summary: Get ``Ii2``.
- `Ii2(self, val)`
  Summary: Set ``Ii2``.
- `Ii3(self)`
  Summary: Get ``Ii3``.
- `Ii3(self, val)`
  Summary: Set ``Ii3``.
- `G(self)`
  Summary: Get ``G``.
- `G(self, val)`
  Summary: Set ``G``.
- `G1(self)`
  Summary: Get ``G1``.
- `G1(self, val)`
  Summary: Set ``G1``.
- `G2(self)`
  Summary: Get ``G2``.
- `G2(self, val)`
  Summary: Set ``G2``.
- `G3(self)`
  Summary: Get ``G3``.
- `G3(self, val)`
  Summary: Set ``G3``.
- `B(self)`
  Summary: Get ``B``.
- `B(self, val)`
  Summary: Set ``B``.
- `B1(self)`
  Summary: Get ``B1``.
- `B1(self, val)`
  Summary: Set ``B1``.
- `B2(self)`
  Summary: Get ``B2``.
- `B2(self, val)`
  Summary: Set ``B2``.
- `B3(self)`
  Summary: Get ``B3``.
- `B3(self, val)`
  Summary: Set ``B3``.
