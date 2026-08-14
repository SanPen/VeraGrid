# Governor

This model represents the RMS governor block used with the complete generator model.

### Purpose

It is the RMS prime-mover and turbine control block built by `get_governor_rms()`.

### Behavior

- Receives generator speed and electrical-torque-related feedback.
- Processes speed error through a governor/turbine chain.
- Applies rate limiting and power limiting.
- Produces the mechanical torque signal sent to the machine block.

### Characteristics

- Explicit-state RMS governor model.
- Includes turbine-stage dynamics.
- Includes saturation and ramp-rate limiting behavior.
## Block structure

```text
omega -> speed error
      -> governor lag/lead stage
      -> ramp / rate limiter
      -> saturation (Pmin/Pmax)
      -> turbine stages
      -> Tm
```

## Characteristic equations

$$
u_1 = \omega - \omega_{ref}
$$

$$
\frac{dy_{gov0}}{dt} = \frac{u_1 - x_1}{T_1}
$$

$$
y_1 = \frac{T_2}{T_1}u_1 + \left(1 - \frac{T_2}{T_1}\right)x_1
$$

$$
y_{2,1} = \mathrm{sat}\left(\frac{P_{m,ref} - K y_1 - y_{2,3}}{T_3}, U_c, U_o\right)
$$

$$
y_{2,3} = \mathrm{sat}(y_{2,2}, P_{min}, P_{max})
$$

$$
T_m = K_1 y_{3,1} + K_2 y_{3,2} + K_3 y_{3,3} + K_4 y_{3,4}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `omega_` | Generator speed feedback coming from the machine block | pu |
| Input | `Te_` | Electrical torque feedback used by the governor initialization and reference logic | pu |
| Output | `Tm` | Mechanical torque command sent to the machine block | pu |
| Variable | `et` | Auxiliary internal variable kept by the block for control compatibility | model units |
| Variable | `Pm_ref` | Internal mechanical-power reference | pu |
| Variable | `y_gov0` | Main governor internal state | pu |
| Variable | `y_gov1_rate` | Rate-limited governor stage variable | pu/s |
| Variable | `y_gov1` | Governor-stage state associated with the saturated command path | pu |
| Variable | `y2_3_gov` | Limited turbine-input signal after saturation | pu |
| Variable | `y_gov2` | Turbine stage 1 state | pu |
| Variable | `y_gov3` | Turbine stage 2 state | pu |
| Variable | `y_gov4` | Turbine stage 3 state | pu |
| Variable | `y_gov5` | Turbine stage 4 state | pu |
| Variable | `x_gov0` | Internal lag state used by the first governor block | pu |
| Parameter | `T1` | Governor time constant | s |
| Parameter | `T2` | Reheater/lead-lag time constant | s |
| Parameter | `T3` | Governor crossover time constant | s |
| Parameter | `T4` | Turbine stage 1 time constant | s |
| Parameter | `T5` | Turbine stage 2 time constant | s |
| Parameter | `T6` | Turbine stage 3 time constant | s |
| Parameter | `T7` | Turbine stage 4 time constant | s |
| Parameter | `K1` | Turbine stage weighting factor 1 | pu |
| Parameter | `K2` | Turbine stage weighting factor 2 | pu |
| Parameter | `K3` | Turbine stage weighting factor 3 | pu |
| Parameter | `K4` | Turbine stage weighting factor 4 | pu |
| Parameter | `K5` | Additional turbine weighting factor reserved by the template | pu |
| Parameter | `K6` | Additional turbine weighting factor reserved by the template | pu |
| Parameter | `K7` | Additional turbine weighting factor reserved by the template | pu |
| Parameter | `K8` | Additional turbine weighting factor reserved by the template | pu |
| Parameter | `K` | Governor gain | pu/pu |
| Parameter | `Pmax` | Maximum allowed mechanical power/torque command | pu |
| Parameter | `Pmin` | Minimum allowed mechanical power/torque command | pu |
| Parameter | `Uc` | Maximum valve-closing rate | pu/s |
| Parameter | `Uo` | Maximum valve-opening rate | pu/s |
| Parameter | `T_aux` | Auxiliary governor parameter reserved by the template | s |
| Parameter | `Kp` | Proportional reference-control gain reserved in the template API | model units |
| Parameter | `Ki` | Integral reference-control gain reserved in the template API | model units |
| Parameter | `omega_ref` | Speed reference | pu |
| Parameter | `p0` | Initial active-power scheduling parameter | pu |
| Parameter | `P0` | Small active-power offset parameter | pu |

## How to use it

- Treat this as the mechanical-power controller of the RMS `Complete generator` package.
- It is not intended to be a standalone network-injecting device.
