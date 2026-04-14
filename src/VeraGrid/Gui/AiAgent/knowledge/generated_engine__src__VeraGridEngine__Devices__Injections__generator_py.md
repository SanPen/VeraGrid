# VeraGridEngine Module: src/VeraGridEngine/Devices/Injections/generator.py

- Original source path: `src/VeraGridEngine/Devices/Injections/generator.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, pandas, typing, matplotlib, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Associations.association, VeraGridEngine.Devices.Injections.generator_q_curve,  VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Parents.injection_parent

## Class: Generator

- Bases: InjectionParent
- Summary: No docstring provided.

### Methods

- `Pf_prof(self)`
  Summary: Cost profile
- `Pf_prof(self, val)`
  Summary: No docstring provided.
- `get_Pf_at(self, t)`
  Summary: :param t:
- `get_Q_at(self, t)`
  Summary: :param t:
- `Vset_prof(self)`
  Summary: Cost profile
- `Vset_prof(self, val)`
  Summary: No docstring provided.
- `get_Vset_at(self, t)`
  Summary: :param t:
- `Qmin_prof(self)`
  Summary: Qmin profile
- `Qmin_prof(self, val)`
  Summary: No docstring provided.
- `get_Qmin_at(self, t)`
  Summary: :param t:
- `Qmax_prof(self)`
  Summary: Qmax profile
- `Qmax_prof(self, val)`
  Summary: No docstring provided.
- `get_Qmax_at(self, t)`
  Summary: :param t:
- `Cost2_prof(self)`
  Summary: Cost profile
- `Cost2_prof(self, val)`
  Summary: No docstring provided.
- `get_Cost2_at(self, t)`
  Summary: :param t:
- `Cost0_prof(self)`
  Summary: Cost profile
- `Cost0_prof(self, val)`
  Summary: No docstring provided.
- `get_Cost0_at(self, t)`
  Summary: :param t:
- `enabled_dispatch_prof(self)`
  Summary: Cost profile
- `enabled_dispatch_prof(self, val)`
  Summary: No docstring provided.
- `get_enabled_dispatch_at(self, t)`
  Summary: :param t:
- `must_run_prof(self)`
  Summary: Cost profile
- `must_run_prof(self, val)`
  Summary: No docstring provided.
- `get_must_run_at(self, t)`
  Summary: :param t:
- `plot_profiles(self, time, show_fig)`
  Summary: Plot the time series results of this object
- `fix_inconsistencies(self, logger, min_vset, max_vset)`
  Summary: Correct the voltage set points
- `Qmax(self)`
  Summary: Return the reactive power upper limit
- `Qmax(self, val)`
  Summary: No docstring provided.
- `Qmin(self)`
  Summary: Return the reactive power lower limit
- `Qmin(self, val)`
  Summary: No docstring provided.
- `Snom(self)`
  Summary: Return the reactive power lower limit
- `Snom(self, val)`
  Summary: Set the generator nominal power
- `is_controlled(self)`
  Summary: Get ``is_controlled``.
- `is_controlled(self, val)`
  Summary: Set ``is_controlled``.
- `Pf(self)`
  Summary: Get ``Pf``.
- `Pf(self, val)`
  Summary: Set ``Pf``.
- `Vset(self)`
  Summary: Get ``Vset``.
- `Vset(self, val)`
  Summary: Set ``Vset``.
- `use_reactive_power_curve(self)`
  Summary: Get ``use_reactive_power_curve``.
- `use_reactive_power_curve(self, val)`
  Summary: Set ``use_reactive_power_curve``.
- `R1(self)`
  Summary: Get ``R1``.
- `R1(self, val)`
  Summary: Set ``R1``.
- `X1(self)`
  Summary: Get ``X1``.
- `X1(self, val)`
  Summary: Set ``X1``.
- `R0(self)`
  Summary: Get ``R0``.
- `R0(self, val)`
  Summary: Set ``R0``.
- `X0(self)`
  Summary: Get ``X0``.
- `X0(self, val)`
  Summary: Set ``X0``.
- `R2(self)`
  Summary: Get ``R2``.
- `R2(self, val)`
  Summary: Set ``R2``.
- `X2(self)`
  Summary: Get ``X2``.
- `X2(self, val)`
  Summary: Set ``X2``.
- `Cost2(self)`
  Summary: Get ``Cost2``.
- `Cost2(self, val)`
  Summary: Set ``Cost2``.
- `Cost0(self)`
  Summary: Get ``Cost0``.
- `Cost0(self, val)`
  Summary: Set ``Cost0``.
- `startup_cost(self)`
  Summary: Get ``StartupCost``.
- `startup_cost(self, val)`
  Summary: Set ``StartupCost``.
- `shutdown_cost(self)`
  Summary: Get ``ShutdownCost``.
- `shutdown_cost(self, val)`
  Summary: Set ``ShutdownCost``.
- `min_time_up(self)`
  Summary: Get ``MinTimeUp``.
- `min_time_up(self, val)`
  Summary: Set ``MinTimeUp``.
- `min_time_down(self)`
  Summary: Get ``MinTimeDown``.
- `min_time_down(self, val)`
  Summary: Set ``MinTimeDown``.
- `ramp_up(self)`
  Summary: Get ``RampUp``.
- `ramp_up(self, val)`
  Summary: Set ``RampUp``.
- `ramp_down(self)`
  Summary: Get ``RampDown``.
- `ramp_down(self, val)`
  Summary: Set ``RampDown``.
- `enabled_dispatch(self)`
  Summary: Get ``enabled_dispatch``.
- `enabled_dispatch(self, val)`
  Summary: Set ``enabled_dispatch``.
- `must_run(self)`
  Summary: Get ``must_run``.
- `must_run(self, val)`
  Summary: Set ``must_run``.
