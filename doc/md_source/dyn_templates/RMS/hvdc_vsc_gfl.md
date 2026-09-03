# Complete GFL VSC HVDC

**Library:** RMS VSC → Devices → Complete GFL VSC hvdc  
**Catalogue type:** `GFL_VSC_HVDC_RMS`  
**Builder:** `build_hvdc_vsc_gfl_rms()`; configurable definition: `HvdcVscGflRmsTemplate`.

## Purpose and network interface

This positive-sequence, grid-following VSC combines the PLL, current dynamics, outer controls, current-reference limiter, inner PIs, DC-link capacitor and terminal-power interface. Its uses include RMS control-response studies and small-signal analysis around a consistent operating point. It is not a switching model or a grid-forming converter.

The static VSC is oriented **from the DC bus to the AC bus**. An external AC transformer, where present, is a separate network device.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vdc` | DC bus voltage, pu |
| Input | 2 | `Vm` | AC bus voltage magnitude, pu; mapping `Vmt` |
| Input | 3 | `Va` | AC bus voltage angle, rad; mapping `Vat` |
| Output | 1 | `Pf_vsc` | DC-terminal active power entering the converter, pu |
| Output | 2 | `Pt_vsc` | AC-terminal active power entering the converter, pu |
| Output | 3 | `Qt_vsc` | AC-terminal reactive power entering the converter, pu |

## Configurable controls

Use **Block properties → General options → Generated structure** to select the controller structure.

| Setting | Options | Default | Feedback selected inside the complete model |
| --- | --- | --- | --- |
| `control1` | `Vm_dc`, `Pdc`, `Pac` | `Vm_dc` | Capacitor `Vdc_state` for `Vm_dc`; internal electrical `P` for both power modes |
| `control2` | `Qac`, `Vm_ac` | `Qac` | Internal electrical `Q` or PLL `vq`, respectively |
| `cdc` | Numerical capacitance setting | `0.40` | Seeds the capacitor's dynamic parameter `Cdc` |

`Pdc` and `Pac` currently share the same internal power-feedback law. `Vm_ac` uses `vq`, which equals the AC magnitude at PLL equilibrium but need not equal it during angle transients. See the [active-control](vsc_active_control.md) and [reactive-control](vsc_reactive_control.md) pages for errors, gains and reference initialization.

These dynamic-model options are distinct from the static VSC's power-flow controls. Dynamic references initially capture their connected feedback unless explicitly changed. Review the operating point and dynamic reference separately when preparing an event.

## Component parameters and states

| Component | Principal dynamic defaults | Explicit states |
| --- | --- | --- |
| [PLL](vsc_pll.md) | `fn = 50`, `Kp_pll = 0.001`, `Ki_pll = 0.1` | Angle and PI integral state |
| [Electrical equations](vsc_electrical.md) | `R = 0`, `L = 0.05` | `i_d`, `i_q` |
| [Vdc / P control](vsc_active_control.md) | Mode-dependent gains and initialized reference | One PI integral state |
| [Qac / Vac control](vsc_reactive_control.md) | Mode-dependent gains and initialized reference | One PI integral state |
| [Current limiter](vsc_current_limiter.md) | `Imax = 1.2` | None |
| [d-axis current PI controller](vsc_vd_hat.md) | `Kp_icl = 0.20`, `Ki_icl = 5.0` | One PI integral state |
| [q-axis current PI controller](vsc_vq_hat.md) | `Kp_icl = 0.20`, `Ki_icl = 5.0` | One PI integral state |
| [DC-link capacitor](vsc_dc_link.md) | `Cdc = 0.40`; losses from static `alpha1/2/3` | `Vdc_state` |
| [Terminal power equations](vsc_terminal_power.md) | DC-side `Qf = 0` | None |

The component equations define an RMS DAE with explicit states. A reduced standard small-signal problem additionally requires that the algebraic subsystem can be eliminated at the selected operating point. No stability or convergence guarantee follows solely from using explicit states.

## Assembling the same model from small blocks

The complete model remains available as one Library item. To build it manually, place the nine components documented above. A Generic Device may group the seven converter-control/electrical components; an extra wrapper is not required for the equations.

| Producer | Consumers |
| --- | --- |
| Root `Vm`, `Va` | PLL inputs 1 and 2 |
| PLL `vd`, `vq`, `omega` | Electrical inputs 1, 2 and 3 |
| Electrical `i_d` | d-axis current PI controller input 1; reactive-control input 2; capacitor input 4 |
| Electrical `i_q` | q-axis current PI controller input 1; active-control input 2; limiter input 3; capacitor input 5 |
| Electrical `P`, `Q` | Terminal-power inputs 3 and 4 |
| Capacitor `Vdc_state` | Terminal-power input 2; active-control input 1 in `Vm_dc` mode |
| Electrical `P` | Active-control input 1 in `Pdc` or `Pac` mode |
| Electrical `Q` / PLL `vq` | Reactive-control input 1 in `Qac` / `Vm_ac` mode |
| Reactive-control `i_d_ref` | Limiter input 1 |
| Active-control `i_q_ref` | Limiter input 2 |
| Limiter `i_d_ref_sat`, `i_q_ref_sat` | d-axis and q-axis current PI controller input 2, respectively |
| d-axis PI `y_vd_hat`, q-axis PI `y_vq_hat` | Electrical inputs 4 and 5 (voltage corrections) |
| Root `Vdc` | Capacitor input 1 and terminal-power input 1 |
| Terminal `Pf_vsc`, `Pt_vsc` | Root outputs 1 and 2, and capacitor inputs 2 and 3 |
| Terminal `Qt_vsc` | Root output 3 |

Signal Pair blocks may replace drawn wires, provided the corresponding sender/receiver signals are explicitly paired. Matching display names alone is not a connection.

## Initialization and verification

Start from a converged power flow. Terminal powers seed internal `P/Q`; the PLL initializes its reference frame; electrical currents and converter voltages determine the inner-PI biases. Outer PI outputs initialize to actual currents. The DC-link state initializes to the DC-bus voltage.

After wiring, apply/save the RMS model to bind the component initialization and synchronize the root mappings. Do not add initialization-only ports or force the PI biases to zero. If components have been replaced, saving the model must remove mappings to deleted variables and retain mappings to the current components.

Before testing disturbances, check the initialization status and residuals. Keep the initial operating point within the limiter assumptions and use the same solver settings when comparing a manually assembled model with the complete template.
