# Explicit-state RMS converter blocks

This section documents the predefined HVDC GFL VSC model, its independently wireable Library components, and the R-L DC line. These are positive-sequence RMS models; they do not resolve converter switching waveforms.

Each page describes the implementation supplied by VeraGrid, including its port order, parameter ownership, equations and explicit initialization. **Block properties → Block info** opens the corresponding published page. Renaming a native Library block does not change its documentation. A user-edited copy may differ from the predefined equations.

## Model reference

- [Complete GFL VSC HVDC and assembly guide](hvdc_vsc_gfl.md).
- [PLL](vsc_pll.md) and [converter electrical equations](vsc_electrical.md).
- [Vdc / P control](vsc_active_control.md) and [Qac / Vac control](vsc_reactive_control.md).
- [Current limiter](vsc_current_limiter.md), [d-axis current PI controller](vsc_vd_hat.md) and [q-axis current PI controller](vsc_vq_hat.md).
- [DC-link capacitor](vsc_dc_link.md) and [terminal power equations](vsc_terminal_power.md).
- [DC line](dc_line.md).

## Common conventions

- Voltage, current and power signals use the model's per-unit bases; phase angles use radians and simulation time uses seconds. `omega` is per-unit frequency, not rad/s.
- The PLL aligns the **q axis** with the AC voltage: at initialization, `vd = 0` and `vq = Vm`. Consequently, `i_q` controls active power and `i_d` controls reactive power at that operating point.
- `P` and `Q` are internal converter powers. Terminal powers use the branch convention: positive into the VSC at each terminal. Thus `Pt_vsc = -P` and `Qt_vsc = -Q`.
- Display labels can propagate through connections. Port order and the actual variable connection, not the displayed name alone, define the model.

## Parameters and initialization

Dynamic parameters belong to `event_dict`. Their values or initialization expressions are edited in **Block properties → General options → Parameters**. In scripting, use `set_parameter_in_model(var_name=..., new_value=...)` after building the block. Repeated parameter names in different children have separate owners; select the intended block.

Static parameters belong to `parameters` and are linked through `api_obj_mapping`. They may be declared as `Const(None)` because the static device must supply their value during assembly. They must not receive independent numerical fallbacks or be edited as dynamic gains.

Explicit PI controllers use an integral state:

$$
\dot{\xi}=e,\qquad y=K_p e+K_i\xi,\qquad
\xi_0=\frac{y_0-K_p e_0}{K_i}.
$$

The initial output bias `y_0` is essential even when the initial error is zero. Keep `Ki` nonzero for this initialization formula. Power-flow-seeded terminal variables are not assigned duplicate initialization equations.

When assembling the converter from individual blocks, connect all physical and control signals, then apply/save the RMS model. The editor derives the electrical `P/Q` initialization and inner-PI output biases from the connected blocks. It also synchronizes the surviving child mappings to the device root. Merely placing blocks in the scene does not create these connections.

For the complete wiring sequence, see [Complete GFL VSC HVDC](hvdc_vsc_gfl.md). The [two-winding transformer](2w_transformer.md) reference describes the external AC coupling branch; it is separate from the converter's internal filter.
