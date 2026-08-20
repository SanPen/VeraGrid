# Sauer-Pai generator

<!-- veragrid-block-introduction:start -->
**Sauer-Pai generator** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents the Sauer-Pai synchronous machine block used within the EMT complete generator model.

### Purpose

It is the phase-domain synchronous-machine EMT model built by `get_generator_sauer_pai_type_emt_template()`.

### Behavior

- Receives three-phase terminal voltages from the wrapper.
- Receives mechanical torque from the governor and field voltage from the exciter.
- Evolves electromagnetic, mechanical, and zero-sequence states.
- Injects phase currents into the network and exports torque, speed, and exciter feedback channels.

### Characteristics

- EMT abc-domain machine model.
- Includes Park-transform-based dq0 dynamics internally.
- Includes explicit zero-sequence dynamics.
- Includes transient and subtransient magnetic states.
## Characteristic equations

$$
\frac{d\theta_{abs}}{dt} = \omega_b \omega
$$

$$
\frac{d\omega}{dt} = \frac{T_m - T_e - D(\omega - \omega_s)}{2H}
$$

$$
\frac{d\psi_d}{dt} = \omega_b (r_a i_d + \omega \psi_q + v_d)
$$

$$
\frac{d\psi_q}{dt} = \omega_b (r_a i_q - \omega \psi_d + v_q)
$$

$$
\frac{d\psi_0}{dt} = \omega_b (r_a i_0 + v_0)
$$

$$
\frac{de_{qp}}{dt} = \frac{-I_{RPu} + v_f}{T_{d0p}}
$$

$$
0 = \psi_d + x_{dpp} i_d - \gamma_{d1} e_{qp} - (1-\gamma_{d1})\psi_{pp,d}
$$

$$
0 = \psi_q + x_{qpp} i_q + \gamma_{q1} e_{dp} - (1-\gamma_{q1})\psi_{pp,q}
$$

$$
0 = \psi_0 + x_0 i_0
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A terminal voltage | pu |
| Input | `v_B` | Instantaneous phase-B terminal voltage | pu |
| Input | `v_C` | Instantaneous phase-C terminal voltage | pu |
| Input | `Tm` | Mechanical torque input from the governor | pu |
| Input | `v_f` | Field-voltage input from the exciter | pu |
| Output | `i_A` | Phase-A current injected into the EMT network | pu |
| Output | `i_B` | Phase-B current injected into the EMT network | pu |
| Output | `i_C` | Phase-C current injected into the EMT network | pu |
| Output | `omega` | Rotor speed shared with the governor and stabilizer | pu |
| Output | `IRPu` | Exciter feedback quantity exported to the exciter block | pu |
| Output | `Te` | Electromagnetic torque exported to the composite generator chain | pu |
| Variable | `theta_abs` | Absolute electrical rotor angle used by the EMT Park transform | rad |
| Variable | `omega` | Rotor speed state | pu |
| Variable | `psi_d` | d-axis flux state | pu |
| Variable | `psi_q` | q-axis flux state | pu |
| Variable | `psi_0` | zero-sequence flux state | pu |
| Variable | `e_qp` | q-axis transient emf state | pu |
| Variable | `e_dp` | d-axis transient emf state | pu |
| Variable | `psi_pp_d` | d-axis subtransient flux state | pu |
| Variable | `psi_pp_q` | q-axis subtransient flux state | pu |
| Variable | `v_d` | d-axis internal voltage after abc-to-dq0 transformation | pu |
| Variable | `v_q` | q-axis internal voltage after abc-to-dq0 transformation | pu |
| Variable | `v_0` | zero-sequence internal voltage | pu |
| Variable | `i_d` | d-axis current | pu |
| Variable | `i_q` | q-axis current | pu |
| Variable | `i_0` | zero-sequence current | pu |
| Variable | `i_A` | Algebraic phase-A current output variable | pu |
| Variable | `i_B` | Algebraic phase-B current output variable | pu |
| Variable | `i_C` | Algebraic phase-C current output variable | pu |
| Variable | `Te` | Electromagnetic torque variable | pu |
| Variable | `p_e` | Instantaneous three-phase electrical active power | pu |
| Variable | `q_e` | Instantaneous three-phase electrical reactive power | pu |
| Variable | `IRPu` | Exciter feedback quantity derived from the q-axis emf channel | pu |
| Parameter | `ra` | Armature resistance | pu |
| Parameter | `xd` | d-axis synchronous reactance | pu |
| Parameter | `xq` | q-axis synchronous reactance | pu |
| Parameter | `xdp` | d-axis transient reactance | pu |
| Parameter | `xqp` | q-axis transient reactance | pu |
| Parameter | `xdpp` | d-axis subtransient reactance | pu |
| Parameter | `xqpp` | q-axis subtransient reactance | pu |
| Parameter | `xl` | Leakage reactance | pu |
| Parameter | `x0` | zero-sequence reactance | pu |
| Parameter | `Td0p` | d-axis open-circuit transient time constant | s |
| Parameter | `Tq0p` | q-axis open-circuit transient time constant | s |
| Parameter | `Td0pp` | d-axis open-circuit subtransient time constant | s |
| Parameter | `Tq0pp` | q-axis open-circuit subtransient time constant | s |
| Parameter | `gamma_d1` | d-axis magnetic coupling coefficient | pu |
| Parameter | `gamma_q1` | q-axis magnetic coupling coefficient | pu |
| Parameter | `gamma_d2` | d-axis magnetic coupling coefficient used in the Sauer-Pai equations | pu |
| Parameter | `gamma_q2` | q-axis magnetic coupling coefficient used in the Sauer-Pai equations | pu |
| Parameter | `H` | Inertia constant | s |
| Parameter | `D` | Damping coefficient | pu-based model constant |
| Parameter | `omega_b` | Base electrical angular frequency | rad/s |
| Parameter | `omega_s` | Synchronous reference speed used by the swing equation | pu |

## How to use it

- Treat this as the machine core of the packaged EMT `Complete generator` model.
- Use the higher-level `Complete generator` document when you want the full governor-exciter-stabilizer-machine assembly.
