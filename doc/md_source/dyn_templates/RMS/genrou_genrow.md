# GENROU/GENROW

This model represents a positive-sequence RMS synchronous machine using the `GENROU/GENROW` formulation.

### Purpose

It is a compact RMS synchronous generator model with rotor-angle and speed dynamics and dq internal variables.

### Behavior

- Uses terminal voltage magnitude and angle as inputs.
- Computes active and reactive power injection from internal electrical and mechanical variables.
- Evolves rotor angle and rotor speed dynamically.
- Uses a compact torque-control relation through internal gain and reference terms.

### Characteristics

- Positive-sequence RMS synchronous-machine model.
- Lighter than the composite `Complete generator` package.
- Appropriate for classical electromechanical dynamic studies.
## Characteristic equations

$$
\frac{d\delta}{dt} = 2\pi f (\omega - \omega_{ref})
$$

$$
\frac{d\omega}{dt} = \frac{T_m - T_e - D(\omega - \omega_{ref})}{M}
$$

$$
T_e = \psi_d i_q - \psi_q i_d
$$

$$
P_g = v_d i_d + v_q i_q
$$

$$
Q_g = v_q i_d - v_d i_q
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude at the generator bus | pu |
| Input | `Va` | Terminal voltage angle at the generator bus | rad |
| Output | `P_g` | Generator active power exported by the model | pu |
| Output | `Q_g` | Generator reactive power exported by the model | pu |
| Variable | `delta` | Rotor electrical angle state | rad |
| Variable | `omega` | Rotor speed state | pu |
| Variable | `psid` | d-axis flux linkage quantity | pu |
| Variable | `psiq` | q-axis flux linkage quantity | pu |
| Variable | `i_d` | d-axis stator current | pu |
| Variable | `i_q` | q-axis stator current | pu |
| Variable | `v_d` | d-axis terminal voltage | pu |
| Variable | `v_q` | q-axis terminal voltage | pu |
| Variable | `te` | Electromagnetic torque variable | pu |
| Variable | `tm` | Mechanical torque variable | pu |
| Variable | `et` | Auxiliary integral-related internal variable used by the torque-control law | model units |
| Parameter | `R1` | Electrical resistance parameter used by the stator algebraic equations | pu |
| Parameter | `X1` | Electrical reactance parameter used by the stator algebraic equations | pu |
| Parameter | `frequ` | Base electrical frequency | Hz |
| Parameter | `M` | Inertia constant | pu-based model constant |
| Parameter | `D` | Damping coefficient | pu-based model constant |
| Parameter | `omega_ref` | Rotor-speed reference | pu |
| Parameter | `Kp` | Proportional gain used in the internal torque-control relation | model units |
| Parameter | `Ki` | Integral gain used in the internal torque-control relation | model units |
| Parameter | `vf` | Internal field-related event-driven quantity used during initialization and runtime | pu |
| Parameter | `tm0` | Internal base mechanical torque quantity | pu |

## How to use it

- Use it when you want a simpler generator model than `Complete generator`.
- Use the composite generator instead when you also want embedded exciter, governor, and stabilizer blocks already connected.
