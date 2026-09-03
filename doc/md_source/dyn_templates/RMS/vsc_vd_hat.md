# d-axis current PI controller

**Library:** RMS VSC → Control blocks → d-axis current PI controller  
**Catalogue type:** `VSC_VD_HAT_RMS`  
**Builder:** `build_vsc_vd_hat_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

The d-axis current controller produces the voltage correction consumed by the electrical block. It has an explicit integral state and exactly two inputs; no initialization-only `vd_hat0` port is required.

This is the PI regulator in the **inner d-axis current loop**, not a voltage estimator. Its output is a voltage correction, not the complete converter-voltage command. The [electrical equations](vsc_electrical.md) combine it with the AC-voltage feedforward and cross-axis terms. Together with the electrical dynamics and measured-current feedback, this forms the closed current loop.

The former display name was `vd hat`. The builder name, catalogue identifier and `y_vd_hat` signal name are retained for compatibility with existing scripts and saved models. Here, `hat` is historical notation; it does not imply an observer or estimated voltage. Previously saved blocks retain their stored display names and can be renamed in Block properties.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `i_d` | Actual d-axis current, pu |
| Input | 2 | `i_d_ref_sat` | Limited d-axis current reference, pu |
| Output | 1 | `y_vd_hat` | d-axis converter-voltage correction, pu |

## Equations and dynamic parameters

$$
e_d=i_d-i_{d,ref,sat},\qquad
\dot{\xi}_d=e_d,\qquad
y_{vd,hat}=K_{p,icl}e_d+K_{i,icl}\xi_d.
$$

| Parameter | Default | Meaning |
| --- | --- | --- |
| `Kp_icl` | `0.20` | Proportional gain |
| `Ki_icl` | `5.0` | Integral gain |

Both gains belong to this controller's `event_dict`. The error is **measured current minus reference**, matching the electrical equations' signs. This block does not select another axis or control quantity; use the separate [q-axis current PI controller](vsc_vq_hat.md) entry for the q axis.

## Initialization and connections

The connected electrical equilibrium determines the output correction:

$$
y_{vd,hat0}=v_{d,c0}-v_{d0}+L\omega_0 i_{q0},\qquad
\xi_{d0}=\frac{y_{vd,hat0}-K_{p,icl}e_{d0}}{K_{i,icl}}.
$$

These are the supplied model's equations, not a zero-bias assumption. The complete template binds the output initialization directly. For independent Library blocks, applying/saving the assembled RMS model derives the corresponding binding from the connected electrical equations.

Connect `i_d` from the electrical block, `i_d_ref_sat` from the limiter, and `y_vd_hat` back to electrical input 4. This PI does not include saturation or anti-windup; the reference limiter is a separate component.
