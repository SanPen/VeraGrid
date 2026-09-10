# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/load_parent.py

- Original source path: `src/VeraGridEngine/Devices/Parents/load_parent.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, pandas, matplotlib, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.basic_structures,  VeraGridEngine.Devices.Parents.injection_parent, VeraGridEngine.Devices.Parents.editable_device

## Class: LoadParent

- Bases: InjectionParent
- Summary: Template for objects that behave like loads

### Methods

- `P_prof(self)`
  Summary: Cost profile
- `P_prof(self, val)`
  Summary: No docstring provided.
- `get_P_at(self, t)`
  Summary: Get power at time t
- `Pa_prof(self)`
  Summary: Cost profile
- `Pa_prof(self, val)`
  Summary: No docstring provided.
- `get_Pa_at(self, t)`
  Summary: :param t:
- `Pb_prof(self)`
  Summary: Cost profile
- `Pb_prof(self, val)`
  Summary: No docstring provided.
- `get_Pb_at(self, t)`
  Summary: :param t:
- `Pc_prof(self)`
  Summary: Cost profile
- `Pc_prof(self, val)`
  Summary: No docstring provided.
- `get_Pc_at(self, t)`
  Summary: :param t:
- `Q_prof(self)`
  Summary: Cost profile
- `Q_prof(self, val)`
  Summary: No docstring provided.
- `get_Q_at(self, t)`
  Summary: :param t:
- `Qa_prof(self)`
  Summary: Cost profile
- `Qa_prof(self, val)`
  Summary: No docstring provided.
- `get_Qa_at(self, t)`
  Summary: :param t:
- `Qb_prof(self)`
  Summary: Cost profile
- `Qb_prof(self, val)`
  Summary: No docstring provided.
- `get_Qb_at(self, t)`
  Summary: :param t:
- `Qc_prof(self)`
  Summary: Cost profile
- `Qc_prof(self, val)`
  Summary: No docstring provided.
- `get_Qc_at(self, t)`
  Summary: :param t:
- `get_S_with_sign(self)`
  Summary: :return:
- `get_Sprof_with_sign(self)`
  Summary: :return:
- `get_S_at(self, t)`
  Summary: :param t:
- `get_Sa_at(self, t)`
  Summary: :param t:
- `get_Sb_at(self, t)`
  Summary: :param t:
- `get_Sc_at(self, t)`
  Summary: :param t:
- `get_Pf_at(self, t)`
  Summary: Get power factor
- `split_sequence_load_in_3_phase(self, share_a, share_b, share_c)`
  Summary: Initializes the 3-phase properties using the positive sequence ones
- `plot_profiles(self, time, show_fig)`
  Summary: Plot the time series results of this object
- `P(self)`
  Summary: Get ``P``.
- `P(self, val)`
  Summary: Set ``P``.
- `Pa(self)`
  Summary: Get ``Pa``.
- `Pa(self, val)`
  Summary: Set ``Pa``.
- `Pb(self)`
  Summary: Get ``Pb``.
- `Pb(self, val)`
  Summary: Set ``Pb``.
- `Pc(self)`
  Summary: Get ``Pc``.
- `Pc(self, val)`
  Summary: Set ``Pc``.
- `Q(self)`
  Summary: Get ``Q``.
- `Q(self, val)`
  Summary: Set ``Q``.
- `Qa(self)`
  Summary: Get ``Qa``.
- `Qa(self, val)`
  Summary: Set ``Qa``.
- `Qb(self)`
  Summary: Get ``Qb``.
- `Qb(self, val)`
  Summary: Set ``Qb``.
- `Qc(self)`
  Summary: Get ``Qc``.
- `Qc(self, val)`
  Summary: Set ``Qc``.
