# VeraGridEngine Module: src/VeraGridEngine/Templates/Emt/converter_emt_template.py

- Original source path: `src/VeraGridEngine/Templates/Emt/converter_emt_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 2
- Representative imports: numpy, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.emt_template, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.symbolic

## Function: get_emt_ideal_converter(vf, name, sbase, fbase, P_ref0, Q_ref0, P_loss0, control1, control2, control1_val, control2_val, vdc_kp)

Build an idealized averaged EMT converter model current injection type with DC power balance.

## Function: get_pseudo_emt_converter(vf, name, sbase, fbase, P_ref0, Q_ref0, Vdc_ref0, R_eq, L_eq, C_dc, R_dc, R_dc_term, pll_kp, pll_ki, i_kp, i_ki, vdc_kp, vdc_ki, q_kp, q_ki, i_max, m_max, P_loss0, P_loss_i1, P_loss_i2, tau_meas, aw_gain, vdc_floor, control1, control2, control1_val, control2_val)

Build a pseudo-EMT averaged grid-following VSC model with explicit DC-link
