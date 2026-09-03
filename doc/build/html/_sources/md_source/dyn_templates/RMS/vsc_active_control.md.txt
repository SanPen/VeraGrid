# Vdc / P control

**Library:** RMS VSC → Control blocks → Vdc / P control  
**Catalogue type:** `VSC_ACTIVE_CONTROL_RMS`  
**Builder:** `build_vsc_active_control_rms()`; configurable definition: `VscActiveControlRmsTemplate`.

## Selectable control modes

Select `control1` in **Block properties → General options → Generated structure**, then apply the changes. The same Library entry supports all three modes.

| `control1` | First input | Reference parameter | Error | Default gains |
| --- | --- | --- | --- | --- |
| `Vm_dc` (default) | `Vdc_state` from the capacitor | `Vdc_ref` | `Vdc_state - Vdc_ref` | `Kp_vdc = 0.20`, `Ki_vdc = 1.0` |
| `Pdc` | Internal electrical `P` | `P_ref` | `P_ref - P` | `Kp_pol = 0.02`, `Ki_pol = 0.10` |
| `Pac` | Internal electrical `P` | `P_ref` | `P_ref - P` | `Kp_pol = 0.02`, `Ki_pol = 0.10` |

**Implementation scope:** `Pdc` and `Pac` currently use the same internal electrical power signal and the same PI law in the complete converter. The `Pdc` option does not introduce an independent DC-terminal-power measurement. Do not connect `Pf_vsc` merely because the selected option is named `Pdc`; doing so differs from the supplied complete model. Internal `P` has the opposite sign to `Pt_vsc`.

## Interface

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vdc_state` or `P` | Selected feedback, pu |
| Input | 2 | `i_q` | Actual q-axis current, used to initialize the PI output |
| Output | 1 | `i_q_ref` | Unrestricted q-axis current reference, pu |

The second input is required even though it does not enter the runtime control error. Connect the actual current from [Converter electrical equations](vsc_electrical.md), not the current reference.

## Equations and parameters

$$
\dot{\xi}=e,\qquad i_{q,ref}=K_p e+K_i\xi.
$$

The gains and reference listed above belong to `event_dict`. The reference is initialized from the connected feedback at the power-flow operating point; it is not an arbitrary fixed default and it does not continuously track the feedback after initialization. A dynamic event can subsequently change it.

For example, changing `Vdc_ref` perturbs DC-voltage regulation, while changing `P_ref` perturbs the internal active-power target. These are dynamic-model references, distinct from the static VSC's power-flow control configuration.

## Initialization and connections

The initial output is `i_q_ref0 = i_q0`, and:

$$
\xi_0=\frac{i_{q0}-K_p e_0}{K_i}.
$$

With the default reference initialization, `e0 = 0`. The nonzero current bias must still be retained.

Feed the output to the second input of the [current limiter](vsc_current_limiter.md). After changing `control1`, check the first-input connection and the active reference/gain names. Voltage-control and power-control modes have different feedback meanings and different error signs; the editor does not select the appropriate measurement on the user's behalf.
