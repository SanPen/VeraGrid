# PLL explicit PI

**Library:** RMS VSC → Control blocks → PLL explicit PI  
**Catalogue type:** `VSC_PLL_RMS`  
**Builder:** `build_vsc_pll_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

The synchronous-reference-frame PLL estimates the AC voltage angle and frequency and supplies the voltage components used by the [electrical model](vsc_electrical.md). It contains the `PLL coordinates` and `PLL_integrator` children.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vm` | AC terminal voltage magnitude, pu |
| Input | 2 | `Va` | AC terminal voltage angle, rad |
| Output | 1 | `vd` | d-axis voltage, pu |
| Output | 2 | `vq` | q-axis voltage, pu |
| Output | 3 | `omega` | Estimated frequency, pu |

`theta` is an internal state, not an output port. Physical inputs carry the `Vmt` and `Vat` power-flow mappings.

## Equations

$$
e_{PLL}=V_m\sin(V_a-\theta),\qquad
v_d=V_m\sin(V_a-\theta),\qquad
v_q=V_m\cos(V_a-\theta),
$$

$$
\dot{\xi}_{PLL}=e_{PLL},\qquad
\omega=K_{p,PLL}e_{PLL}+K_{i,PLL}\xi_{PLL},\qquad
\dot{\theta}=2\pi f_n(\omega-1).
$$

The nominal frequency is represented by the integrator bias; there is no separate `+1` term in the PI output equation. Do not substitute a d-axis-aligned PLL without adapting the converter equations and controls.

## Dynamic parameters

| Parameter | Default | Meaning |
| --- | --- | --- |
| `fn` | `50.0` Hz | Nominal frequency used for angle dynamics |
| `Kp_pll` | `0.001` | Proportional gain |
| `Ki_pll` | `0.1` | Integral gain |

These parameters belong to the `PLL coordinates` child's `event_dict`. Set `fn` consistently with the network frequency; it is not automatically linked to `fBase` by this component.

## Initialization and wiring

Initialization sets `theta = Va`, `vd = 0`, `vq = Vm`, and `omega = 1`. The PI state is initialized from its output bias, giving `xi_PLL = 1 / Ki_pll` at zero error.

Connect `Vm/Va` to the VSC's AC terminal inputs, then connect all three outputs to the corresponding inputs of [Converter electrical equations](vsc_electrical.md). In `Vm_ac` control mode, also connect `vq` to the [Qac / Vac control](vsc_reactive_control.md). This PLL has no selectable power-control mode.
