# PI controller

### Purpose

A PI controller produces a control output from the sum of a proportional term and an integral term applied to an error signal.

### Behavior

- Receives one error signal.
- Produces one control output.
- Removes steady-state error through the integral term.

### Characteristics

- One of the most common control blocks in the library.
- Used in current loops, voltage loops, power loops, and PLL loop filters.

## Characteristic equations

$$
e = x_{ref} - x
$$

$$
u = K_p e + K_i \int e \, dt
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal or error signal | model-dependent |
| Output | `yo` | Controller output | model-dependent |
| Variable | `integrator state` | Internal state that stores the integral of the error | model-dependent |
| Parameter | `Kp` | Proportional gain | model-dependent |
| Parameter | `Ki` | Integral gain | model-dependent/s |

## How to use it

- Use a PI block when steady-state tracking accuracy is needed.
- Add anti-windup or limiting around it when the actuator can saturate.
