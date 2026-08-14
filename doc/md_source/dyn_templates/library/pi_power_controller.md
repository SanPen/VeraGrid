# PI power controller

### Purpose

A PI power controller regulates active power, reactive power, or DC voltage and converts those control objectives into current references.

### Behavior

- Receives measured power or voltage channels plus references.
- Produces `d` and `q` current references for a downstream current controller.
- Can combine active-power, reactive-power, and DC-voltage control objectives.

### Characteristics

- Common in converter outer-loop control hierarchies.
- Slower than the inner current controller.

## Characteristic equations

$$
e_P = P_{ref} - P
$$

$$
e_Q = Q_{ref} - Q
$$

$$
e_{Vdc} = V_{dc,ref} - V_{dc}
$$

$$
i_{d,ref} = K_{p,P} e_P + K_{i,P} \int e_P \, dt \quad \text{or} \quad K_{p,Vdc} e_{Vdc} + K_{i,Vdc} \int e_{Vdc} \, dt
$$

$$
i_{q,ref} = K_{p,Q} e_Q + K_{i,Q} \int e_Q \, dt
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `P` | Measured active power | pu |
| Input | `Q` | Measured reactive power | pu |
| Input | `v_dc` | Measured DC-link voltage | pu |
| Input | `P_ref` | Active-power reference | pu |
| Input | `Q_ref` | Reactive-power reference | pu |
| Input | `Vdc_ref` | DC-voltage reference | pu |
| Output | `i_q_ref` | q-axis current reference produced by the outer loop | pu |
| Output | `i_d_ref` | d-axis current reference produced by the outer loop | pu |
| Parameter | `Kp_pol` | Proportional gain of the active/reactive power outer loop | pu/pu |
| Parameter | `Ki_pol` | Integral gain of the active/reactive power outer loop | pu/(pu·s) |
| Parameter | `Kp_vdc` | Proportional gain of the DC-voltage control loop | pu/pu |
| Parameter | `Ki_vdc` | Integral gain of the DC-voltage control loop | pu/(pu·s) |

## How to use it

- Use this block upstream of a current controller in a converter control hierarchy.
- Make sure the selected reference and sign conventions match the downstream current-control design.
