# Current limiter

**Library:** RMS VSC → Control blocks → Current limiter  
**Catalogue type:** `VSC_CURRENT_LIMITER_RMS`  
**Builder:** `build_vsc_current_limiter_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

This algebraic block limits the outer controllers' current references before they reach the inner PIs. It uses the q-axis-priority law of the complete HVDC VSC.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `i_d_ref` | Reference from Qac / Vac control |
| Input | 2 | `i_q_ref` | Reference from Vdc / P control |
| Input | 3 | `i_q` | Actual electrical q-axis current |
| Output | 1 | `i_d_ref_sat` | Limited d-axis reference |
| Output | 2 | `i_q_ref_sat` | Limited q-axis reference |

All signals are currents in model per-unit quantities. The third input must be connected; it is not interchangeable with `i_q_ref`.

## Equations

With `sat(x, lower, upper)` denoting hard saturation:

$$
I_{d,lim}=\sqrt{\max\left(I_{max}^2-\max(i_q,i_{q,ref})^2,10^{-5}\right)},
$$

$$
i_{d,ref,sat}=\operatorname{sat}(i_{d,ref},-I_{d,lim},I_{d,lim}),\qquad
i_{q,ref,sat}=\operatorname{sat}(i_{q,ref},-I_{max},I_{max}).
$$

The inner `max` compares **signed** currents before squaring. It is not `max(abs(i_q), abs(i_q_ref))`, nor a radial projection of the reference vector. The small floor keeps the square-root argument positive. Consequently, this implementation must not be interpreted as a universal exact circular-current constraint in all operating quadrants.

## Dynamic parameter

| Parameter | Default | Meaning |
| --- | --- | --- |
| `Imax` | `1.2` pu | q-axis limit and basis of the d-axis current allowance |

`Imax` belongs to `event_dict`; use a positive value. There is no selectable priority option in this block.

## Initialization and limitations

The explicit initialization seeds `i_d_ref_sat = i_d_ref` and `i_q_ref_sat = i_q_ref`. These seeds assume an unsaturated operating point. If the initial references are already outside the limiter, the seeds will not satisfy the limiting equations; review the operating point and `Imax` before interpreting initialization failures.

Connect the outputs to the [d-axis current PI controller](vsc_vd_hat.md) and [q-axis current PI controller](vsc_vq_hat.md), respectively. This block limits references, not the instantaneous physical currents. It does not add anti-windup states to the outer PIs. Hard saturation and `max` also introduce nonsmooth boundaries relevant to small-signal linearization.
