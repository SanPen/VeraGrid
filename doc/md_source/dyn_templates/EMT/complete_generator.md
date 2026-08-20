# Complete generator

<!-- veragrid-block-introduction:start -->
**Complete generator** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents a complete EMT synchronous generator with its machine and control blocks already connected.

### Purpose

It is a packaged phase-domain synchronous generator assembled from:

- Sauer-Pai generator block,
- exciter block,
- governor block,
- stabilizer block.

### Behavior

- Uses three-phase terminal voltages as external inputs.
- Produces three-phase current injections as external outputs.
- Internally wires machine, exciter, governor, and stabilizer signals together.
- Uses the governor for mechanical torque, the exciter for field voltage, and the stabilizer as an auxiliary damping signal for the exciter.

### Characteristics

- EMT abc-domain composite generator.
- Suitable for detailed synchronous-machine transient studies.
- More detailed than the RMS `Complete generator`.
## Block structure

```text
Terminal voltages (v_A, v_B, v_C)
    -> Sauer-Pai generator
        <- Exciter (v_f)
        <- Governor (Tm)
        -> Stabilizer input (omega)
Stabilizer
    -> Exciter auxiliary input
Machine outputs
    -> i_A, i_B, i_C
```

## Characteristic equations

$$
\frac{d\theta_{abs}}{dt} = \omega_b \omega
$$

$$
\frac{d\omega}{dt} = \frac{T_m - T_e - D(\omega - \omega_s)}{2H}
$$

$$
T_e = \frac{3}{2}(\psi_d i_q - \psi_q i_d)
$$

$$
p_e = v_A i_A + v_B i_B + v_C i_C
$$

$$
q_e = \frac{1}{\sqrt{3}}\left((v_A-v_B)i_C + (v_B-v_C)i_A + (v_C-v_A)i_B\right)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Terminal phase-A voltage applied to the composite generator | pu |
| Input | `v_B` | Terminal phase-B voltage applied to the composite generator | pu |
| Input | `v_C` | Terminal phase-C voltage applied to the composite generator | pu |
| Output | `i_A` | Phase-A current injected into the EMT network by the composite generator | pu |
| Output | `i_B` | Phase-B current injected into the EMT network by the composite generator | pu |
| Output | `i_C` | Phase-C current injected into the EMT network by the composite generator | pu |
| Variable | `Sauer-Pai generator block` | Internal synchronous-machine submodel | submodel |
| Variable | `Exciter block` | Internal field-voltage controller submodel | submodel |
| Variable | `Governor block` | Internal mechanical-power controller submodel | submodel |
| Variable | `Stabilizer block` | Internal damping controller submodel | submodel |
| Parameter | `omega_base` | Machine base angular frequency exposed through the wrapper mapping | rad/s |
| Parameter | `R1` | Wrapper-exposed resistance-related machine parameter | pu |
| Parameter | `X1` | Wrapper-exposed positive-sequence reactance-related machine parameter | pu |
| Parameter | `X0` | Wrapper-exposed zero-sequence reactance parameter | pu |
| Parameter | `generator_share_p_ref` | Wrapper-exposed shared governor power-reference parameter | pu |

## How to use it

- Use this template when you want a full EMT synchronous generator already wired with its main control blocks.
- Use the separate component documents when you want to understand the machine, exciter, governor, or stabilizer in isolation.
