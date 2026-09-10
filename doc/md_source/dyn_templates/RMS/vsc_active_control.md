# Vdc / P control

**Library:** RMS VSC → Control blocks → Vdc / P control  
**Catalogue type:** `VSC_ACTIVE_CONTROL_RMS`  
**Builder:** `build_vsc_active_control_rms()`; configurable definition: `VscActiveControlRmsTemplate`.

## Selectable control modes

Select `control1` in **Block properties → General options → Generated structure**, then apply the changes. The same Library entry supports all three modes.

| `control1` | First input | Reference parameter | Error | Default gains |
| --- | --- | --- | --- | --- |
| `Vm_dc` (default) | `Vdc_state` from the capacitor | `Vdc_ref` | `Vdc_state - Vdc_ref` | `Kp_vdc = 0.20`, `Ki_vdc = 1.0` |
| `Pdc` | DC-terminal `Pf_vsc` | `P_ref` | `P_ref - Pf_vsc` | `Kp_pol = 0.02`, `Ki_pol = 0.10` |
| `Pac` | AC-terminal `Pt_vsc` | `P_ref` | `P_ref + Pt_vsc` | `Kp_pol = 0.02`, `Ki_pol = 0.10` |

`Pdc` measures power entering the converter at the DC terminal. `Pac` measures power entering at the AC terminal; therefore a positive DC-to-AC transfer target corresponds to `P_ref = -Pt_vsc`. The different error expressions preserve the same positive transfer-reference convention.

## Interface

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vdc_state`, `Pf_vsc` or `Pt_vsc` | Selected feedback, pu |
| Input | 2 | `i_q` | Actual q-axis current, used to initialize the PI output |
| Output | 1 | `i_q_ref` | Unrestricted q-axis current reference, pu |

The second input is required even though it does not enter the runtime control error. Connect the actual current from [Converter electrical equations](vsc_electrical.md), not the current reference.

## Equations and parameters

$$
\dot{\xi}=e,\qquad i_{q,ref}=K_p e+K_i\xi.
$$

The gains and reference listed above belong to `event_dict`. At the power-flow operating point the reference initializes to `Vdc_state` in `Vm_dc` mode, `Pf_vsc` in `Pdc` mode, and `-Pt_vsc` in `Pac` mode. It does not continuously track the feedback after initialization. A dynamic event can subsequently change it.

For example, changing `Vdc_ref` perturbs DC-voltage regulation, while changing `P_ref` perturbs the selected terminal-power target. These are dynamic-model references, distinct from the static VSC's power-flow control configuration.

## Initialization and connections

The initial output is `i_q_ref0 = i_q0`, and:

$$
\xi_0=\frac{i_{q0}-K_p e_0}{K_i}.
$$

With the default reference initialization, `e0 = 0`. The nonzero current bias must still be retained.

Feed the output to the second input of the [current limiter](vsc_current_limiter.md). After changing `control1`, check the first-input connection and the active reference/gain names. Voltage-control and power-control modes have different feedback meanings and different error signs; the editor does not select the appropriate measurement on the user's behalf.
