# PI current controller

<!-- veragrid-block-introduction:start -->
**PI current controller** implements a feedback-control relation. Such blocks turn tracking error into an actuator command and may contain proportional, integral, filtering, or dynamic compensation terms. Their gains set closed-loop speed and damping rather than changing the underlying network physics directly.

## Typical use

- Use it inside voltage, current, power, speed, excitation, or governor control loops.
- Coordinate gains, limits, and time constants with the actuator and plant bandwidth.
<!-- veragrid-block-introduction:end -->

### Purpose

A PI current controller regulates current components, typically `d` and `q` current channels in vector-controlled converters.

### Behavior

- Receives measured currents and current references.
- Computes voltage-command-like outputs that drive the inner converter actuation stage.
- Removes steady-state current error through the integral action.

### Characteristics

- Commonly used in grid-following converter inner loops.
- Often implemented as one PI per controlled axis.

## Characteristic equations

$$
e_d = i_{d,ref} - i_d
$$

$$
e_q = i_{q,ref} - i_q
$$

$$
v_{d,cmd} = K_p e_d + K_i \int e_d \, dt
$$

$$
v_{q,cmd} = K_p e_q + K_i \int e_q \, dt
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `i_q` | Measured q-axis current | pu |
| Input | `i_q_ref_sat` | Limited or saturated q-axis current reference | pu |
| Input | `i_d` | Measured d-axis current | pu |
| Input | `i_d_ref_sat` | Limited or saturated d-axis current reference | pu |
| Output | `vq_hat` | q-axis controller output, typically used as a voltage command contribution | pu |
| Output | `vd_hat` | d-axis controller output, typically used as a voltage command contribution | pu |
| Variable | `control_block_iq` | Internal PI subblock regulating the q-axis current | submodel |
| Variable | `control_block_id` | Internal PI subblock regulating the d-axis current | submodel |
| Parameter | `Kp_icl` | Proportional gain of the inner current loop | pu/pu |
| Parameter | `Ki_icl` | Integral gain of the inner current loop | pu/(pu·s) |

## How to use it

- Use this block in converter inner loops where direct current regulation is required.
- Place current limits ahead of this controller when actuator saturation is possible.
