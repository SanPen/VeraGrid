# Complete generator

<!-- veragrid-block-introduction:start -->
**Complete generator** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents a complete positive-sequence RMS synchronous generator with its main control blocks already connected.

### Purpose

It is a packaged RMS positive-sequence generator assembled from:

- `GENQEC` machine block,
- exciter block,
- governor block,
- stabilizer block.

### Behavior

- Uses terminal voltage magnitude and angle as external inputs.
- Produces generator active and reactive power as external outputs.
- Internally wires the machine, exciter, governor, and stabilizer blocks together.
- Uses the machine speed as the stabilizer input, the stabilizer output as an exciter auxiliary input, the exciter output as the machine field input, and the governor output as the machine mechanical torque input.

### Characteristics

- Positive-sequence RMS composite generator model.
- Intended for electromechanical and controller-dynamics studies.
- More complete than the simpler `GENROU/GENROW` machine template.
## Block structure

```text
Terminal voltage (Vm, Va)
    -> GENQEC machine
        <- Exciter (Vf)
        <- Governor (Tm)
        -> Stabilizer input (omega)
Stabilizer
    -> Exciter auxiliary input
Machine outputs
    -> P, Q
```

## Characteristic equations

$$
\frac{d\delta}{dt} = (\omega - 1) w_s
$$

$$
\frac{d\omega}{dt} = \frac{T_m - T_e - D(\omega - 1)}{M}
$$

$$
P_g = V_d I_d + V_q I_q
$$

$$
Q_g = V_q I_d - V_d I_q
$$

$$
T_e = \Psi_d I_q - \Psi_q I_d
$$

The complete model behavior is determined by these machine equations together with the exciter, governor, and stabilizer control laws.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude at the generator bus | pu |
| Input | `Va` | Terminal voltage angle at the generator bus | rad |
| Output | `P` | Net active power exported by the composite generator | pu |
| Output | `Q` | Net reactive power exported by the composite generator | pu |
| Variable | `GENQEC machine block` | Internal synchronous-machine submodel that computes the electrical response | submodel |
| Variable | `Exciter block` | Internal excitation controller submodel | submodel |
| Variable | `Governor block` | Internal mechanical-power controller submodel | submodel |
| Variable | `Stabilizer block` | Internal damping controller submodel | submodel |
| Parameter | `Machine parameters` | Parameters belonging to the `GENQEC` machine block | mixed |
| Parameter | `Exciter parameters` | Parameters belonging to the exciter block | mixed |
| Parameter | `Governor parameters` | Parameters belonging to the governor block | mixed |
| Parameter | `Stabilizer parameters` | Parameters belonging to the stabilizer block | mixed |

## How to use it

- Use this template when you want a complete RMS synchronous generator already wired with its main controls.
- Use the individual `GENQEC`, `Exciter`, `Governor`, and `Stabilizer` docs when you need to understand the internal submodels in detail.
