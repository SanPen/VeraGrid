# Converter electrical equations

**Library:** RMS VSC → Devices → Converter electrical equations  
**Catalogue type:** `VSC_ELECTRICAL_RMS`  
**Builder:** `build_vsc_electrical_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

This block owns the explicit converter-current states and the physical AC-terminal powers. The voltages `v_d_c` and `v_q_c` are algebraic variables, not additional output ports.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `vd` | PLL d-axis grid voltage |
| Input | 2 | `vq` | PLL q-axis grid voltage |
| Input | 3 | `omega` | PLL frequency, pu |
| Input | 4 | `y_vd_hat` | d-axis current-PI voltage correction |
| Input | 5 | `y_vq_hat` | q-axis current-PI voltage correction |
| Output | 1 | `i_d` | d-axis current state |
| Output | 2 | `i_q` | q-axis current state |
| Output | 3 | `Pt_vsc` | AC-terminal active power entering the converter |
| Output | 4 | `Qt_vsc` | AC-terminal reactive power entering the converter |

Voltages, currents and powers are in model per-unit quantities. The powers follow the branch convention and are positive into the VSC.

## Equations

The equations below reproduce the implemented dq signs and time scaling:

$$
\dot{i}_d=\frac{v_d-v_{d,c}-Ri_d+\omega Li_q}{L},\qquad
\dot{i}_q=\frac{v_q-v_{q,c}+Ri_q+\omega Li_d}{L},
$$

$$
v_{d,c}=y_{vd,hat}+v_d-L\omega i_q,\qquad
v_{q,c}=y_{vq,hat}+v_q+L\omega i_d,
$$

$$
P_{t,vsc}=-(v_qi_q+v_di_d),\qquad Q_{t,vsc}=-(v_qi_d-v_di_q).
$$

Use these components together with their matching PLL and current controllers. Replacing individual signs with another dq convention changes the model.

## Dynamic parameters

| Parameter | Default | Meaning |
| --- | --- | --- |
| `R` | `0.0` | Internal converter-filter resistance coefficient |
| `L` | `0.05` | Internal converter-filter inductance coefficient; must be positive |

Both parameters are in this block's `event_dict`. They are not the external transformer or DC-line impedance. `L` is used directly in the implemented differential equations; there is no additional nominal-angular-frequency multiplier in those equations. Do not enter an inductance in henries without conversion to the model's normalization.

## Explicit initialization

The power flow initializes `Pt_vsc0` and `Qt_vsc0` directly. With the PLL initialized on the q axis:

$$
i_{q0}=-P_{t,vsc0}/v_{q0},\qquad i_{d0}=-Q_{t,vsc0}/v_{q0},
$$

$$
v_{d,c0}=v_{d0}-Ri_{d0}+\omega_0Li_{q0},\qquad
v_{q,c0}=v_{q0}+Ri_{q0}+\omega_0Li_{d0}.
$$

The current-PI output biases are then derived from the two algebraic voltage equations. They must not be forced to zero. This initialization requires a nonzero AC voltage `vq0` and a consistent power-flow operating point.

## Connections

Connect `vd/vq/omega` from the PLL, `y_vd_hat` from the [d-axis current PI controller](vsc_vd_hat.md), and `y_vq_hat` from the [q-axis current PI controller](vsc_vq_hat.md). These last two signals are voltage corrections, not voltage estimates or complete converter-voltage commands. Feed `Pt_vsc` to the DC-link and to the active controller in `Pac` mode; feed `Qt_vsc` to the reactive controller in `Qac` mode. Feed `i_d/i_q` back to the inner PIs, to their corresponding outer-controller initialization inputs, and to the DC-link loss model. The current limiter also consumes `i_q`.

Apply/save the assembled RMS model to derive its initialization bindings. The standalone electrical component does not by itself represent a complete VSC network interface.
