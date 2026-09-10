# Qac / Vac control

**Library:** RMS VSC → Control blocks → Qac / Vac control  
**Catalogue type:** `VSC_REACTIVE_CONTROL_RMS`  
**Builder:** `build_vsc_reactive_control_rms()`; configurable definition: `VscReactiveControlRmsTemplate`.

## Selectable control modes

Select `control2` in **Block properties → General options → Generated structure**, then apply the changes.

| `control2` | First input | Reference parameter | Error | Default gains |
| --- | --- | --- | --- | --- |
| `Qac` (default) | AC-terminal `Qt_vsc` | `Q_ref` | `Q_ref + Qt_vsc` | `Kp_pol = 0.02`, `Ki_pol = 0.10` |
| `Vm_ac` | PLL output `vq` | `Vm_ac_ref` | `Vm_ac_ref - vq` | `Kp_vac = 0.10`, `Ki_vac = 1.0` |

In `Vm_ac` mode the supplied implementation regulates the q-axis voltage `vq`, not a separately measured voltage magnitude. At PLL equilibrium `vq = Vm`; during angle transients, `vq = Vm cos(Va - theta)`. Use the PLL's `vq` output to reproduce the complete converter.

In `Qac` mode, positive `Q_ref` follows the converter-to-grid convention, while `Qt_vsc` is positive from the AC bus into the converter. Therefore the initialized reference is `Q_ref0 = -Qt_vsc0`.

## Interface and equations

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Qt_vsc` or `vq` | Selected reactive-power/voltage feedback, pu |
| Input | 2 | `i_d` | Actual d-axis current for output initialization |
| Output | 1 | `i_d_ref` | Unrestricted d-axis current reference, pu |

$$
\dot{\xi}=e,\qquad i_{d,ref}=K_p e+K_i\xi.
$$

Gains and reference are dynamic parameters in this block's `event_dict`. The default reference expression captures `-Qt_vsc` in `Qac` mode and `vq` in `Vm_ac` mode. It remains the initialized reference until changed, for example by a dynamic event. It is not a live connection that makes the error identically zero.

## Initialization and connections

Initialization uses the actual electrical current:

$$
i_{d,ref0}=i_{d0},\qquad
\xi_0=\frac{i_{d0}-K_p e_0}{K_i}.
$$

Connect input 2 to the electrical block's `i_d` output and send `i_d_ref` to input 1 of the [current limiter](vsc_current_limiter.md). This outer PI has no internal output saturation or anti-windup feedback; current-reference limiting is performed by the separate limiter.

When switching `Qac` to `Vm_ac`, reconnect input 1 from electrical `Qt_vsc` to PLL `vq`, and review the new gains/reference. The complete converter's `control2` option selects this wiring automatically; a manually assembled set of components requires the corresponding manual connection.
