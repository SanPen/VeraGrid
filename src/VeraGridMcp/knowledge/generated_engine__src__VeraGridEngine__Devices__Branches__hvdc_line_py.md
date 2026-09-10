# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/hvdc_line.py

- Original source path: `src/VeraGridEngine/Devices/Branches/hvdc_line.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: pandas, numpy, typing, matplotlib, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.branch_parent, VeraGridEngine.enumerations,  VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Branches.line_locations

## Function: firing_angles_to_reactive_limits(P, alphamin, alphamax)

Convert firing angles to reactive power limits

## Function: getFromAndToPowerAt(Pset, theta_f, theta_t, Vnf, Vnt, v_set_f, v_set_t, Sbase, r1, angle_droop, rate, free, in_pu)

Compute the power and losses

## Class: HvdcLine

- Bases: BranchParent
- Summary: HvdcLine

### Methods

- `active_prof(self)`
  Summary: Cost profile
- `active_prof(self, val)`
  Summary: No docstring provided.
- `get_active_at(self, t)`
  Summary: :param t:
- `rate_prof(self)`
  Summary: Cost profile
- `rate_prof(self, val)`
  Summary: No docstring provided.
- `get_rate_at(self, t)`
  Summary: :param t:
- `contingency_factor_prof(self)`
  Summary: Cost profile
- `contingency_factor_prof(self, val)`
  Summary: No docstring provided.
- `get_contingency_factor_at(self, t)`
  Summary: :param t:
- `Cost_prof(self)`
  Summary: Cost profile
- `Cost_prof(self, val)`
  Summary: No docstring provided.
- `get_Cost_at(self, t)`
  Summary: :param t:
- `Pset_prof(self)`
  Summary: Cost profile
- `Pset_prof(self, val)`
  Summary: No docstring provided.
- `get_Pset_at(self, t)`
  Summary: :param t:
- `angle_droop_prof(self)`
  Summary: Cost profile
- `angle_droop_prof(self, val)`
  Summary: No docstring provided.
- `get_angle_droop_at(self, t)`
  Summary: :param t:
- `Vset_f_prof(self)`
  Summary: Cost profile
- `Vset_f_prof(self, val)`
  Summary: No docstring provided.
- `get_Vset_f_at(self, t)`
  Summary: :param t:
- `Vset_t_prof(self)`
  Summary: Cost profile
- `Vset_t_prof(self, val)`
  Summary: No docstring provided.
- `get_Vset_t_at(self, t)`
  Summary: :param t:
- `locations(self)`
  Summary: Cost profile
- `locations(self, val)`
  Summary: No docstring provided.
- `length(self)`
  Summary: Line length in km
- `length(self, val)`
  Summary: No docstring provided.
- `get_from_and_to_power(self, theta_f, theta_t, Sbase, in_pu)`
  Summary: Get the power set at both ends accounting for meaningful losses
- `get_from_and_to_power_at(self, t, theta_f, theta_t, Sbase, in_pu)`
  Summary: Get the power set at both ends accounting for meaningful losses
- `get_save_data(self)`
  Summary: Return the data that matches the edit_headers
- `get_max_bus_nominal_voltage(self)`
  Summary: No docstring provided.
- `get_min_bus_nominal_voltage(self)`
  Summary: No docstring provided.
- `plot_profiles(self, time_series, my_index, show_fig)`
  Summary: Plot the time series results of this object
- `get_coordinates(self)`
  Summary: Get the branch defining coordinates
- `get_q_limits(self, P)`
  Summary: Get reactive power limits
- `dispatchable(self)`
  Summary: Get ``dispatchable``.
- `dispatchable(self, val)`
  Summary: Set ``dispatchable``.
- `Pset(self)`
  Summary: Get ``Pset``.
- `Pset(self, val)`
  Summary: Set ``Pset``.
- `r(self)`
  Summary: Get ``r``.
- `r(self, val)`
  Summary: Set ``r``.
- `dc_link_voltage(self)`
  Summary: Get ``dc_link_voltage``.
- `dc_link_voltage(self, val)`
  Summary: Set ``dc_link_voltage``.
- `angle_droop(self)`
  Summary: Get ``angle_droop``.
- `angle_droop(self, val)`
  Summary: Set ``angle_droop``.
- `Vset_f(self)`
  Summary: Get ``Vset_f``.
- `Vset_f(self, val)`
  Summary: Set ``Vset_f``.
- `Vset_t(self)`
  Summary: Get ``Vset_t``.
- `Vset_t(self, val)`
  Summary: Set ``Vset_t``.
- `min_firing_angle_f(self)`
  Summary: Get ``min_firing_angle_f``.
- `min_firing_angle_f(self, val)`
  Summary: Set ``min_firing_angle_f``.
- `max_firing_angle_f(self)`
  Summary: Get ``max_firing_angle_f``.
- `max_firing_angle_f(self, val)`
  Summary: Set ``max_firing_angle_f``.
- `min_firing_angle_t(self)`
  Summary: Get ``min_firing_angle_t``.
- `min_firing_angle_t(self, val)`
  Summary: Set ``min_firing_angle_t``.
- `max_firing_angle_t(self)`
  Summary: Get ``max_firing_angle_t``.
- `max_firing_angle_t(self, val)`
  Summary: Set ``max_firing_angle_t``.
