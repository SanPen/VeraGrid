# q-axis current PI controller

**Library:** RMS VSC → Control blocks → q-axis current PI controller  
**Catalogue type:** `VSC_VQ_HAT_RMS`  
**Builder:** `build_vsc_vq_hat_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

The q-axis current controller produces the voltage correction consumed by the electrical block. Its integral state is explicit. There is no additional `vq_hat0` input or separate initialization-bias output.

This is the PI regulator in the **inner q-axis current loop**, not a voltage estimator. Its output is a voltage correction, not the complete converter-voltage command. The [electrical equations](vsc_electrical.md) combine it with the AC-voltage feedforward and cross-axis terms. Together with the electrical dynamics and measured-current feedback, this forms the closed current loop.

The former display name was `vq hat`. The builder name, catalogue identifier and `y_vq_hat` signal name are retained for compatibility with existing scripts and saved models. Here, `hat` is historical notation; it does not imply an observer or estimated voltage. Previously saved blocks retain their stored display names and can be renamed in Block properties.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `i_q` | Actual q-axis current, pu |
| Input | 2 | `i_q_ref_sat` | Limited q-axis current reference, pu |
| Output | 1 | `y_vq_hat` | q-axis converter-voltage correction, pu |

## Equations and dynamic parameters

$$
e_q=i_q-i_{q,ref,sat},\qquad
\dot{\xi}_q=e_q,\qquad
y_{vq,hat}=K_{p,icl}e_q+K_{i,icl}\xi_q.
$$

| Parameter | Default | Meaning |
| --- | --- | --- |
| `Kp_icl` | `0.20` | Proportional gain |
| `Ki_icl` | `5.0` | Integral gain |

These gains belong to this block's `event_dict`, independently of the identically named gains in the [d-axis current PI controller](vsc_vd_hat.md). The error is measured current minus limited reference. The axis is fixed by the Library entry, not a selectable `control1/control2` option.

## Initialization and connections

The electrical equilibrium provides the correction bias:

$$
y_{vq,hat0}=v_{q,c0}-v_{q0}-L\omega_0i_{d0},\qquad
\xi_{q0}=\frac{y_{vq,hat0}-K_{p,icl}e_{q0}}{K_{i,icl}}.
$$

With the implemented electrical equilibrium, `y_vq_hat0 = R i_q0`. It is zero only when that operating point makes it zero; do not replace the derived initialization with an unconditional zero.

Connect `i_q` from the electrical block, `i_q_ref_sat` from the limiter, and `y_vq_hat` to electrical input 5. Apply/save the assembled model so the editor can derive the initialization binding. No saturation or anti-windup is implemented inside this PI.
