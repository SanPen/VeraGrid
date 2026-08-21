# Single cage induction motor

<!-- veragrid-block-introduction:start -->
**Single cage induction motor** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents a single-cage induction motor in phase-domain EMT form.

## Scope and model level

This is the Level-2 induction-motor model. It has a three-wire ABC stator interface and transforms terminal quantities internally to stationary $\alpha\beta$ coordinates. It represents stator and rotor electromagnetic transients together with shaft acceleration, while omitting zero-sequence and detailed mechanical train modes.

Use it for ordinary motor starting, stalling, fault recovery, voltage-dip, and aggregate motor-load studies when one rotor cage adequately represents the machine.

## State equations

The state vector contains stator flux, rotor flux, and normalized rotor speed. Representative equations are

$$
\dot\psi_{s,\alpha}=v_\alpha-r_si_{s,\alpha},
\qquad
\dot\psi_{s,\beta}=v_\beta-r_si_{s,\beta},
$$

$$
\dot\psi_{r,\alpha}=-r_ri_{r,\alpha}-\omega_{r,e}\psi_{r,\beta},
\qquad
\dot\psi_{r,\beta}=-r_ri_{r,\beta}+\omega_{r,e}\psi_{r,\alpha}.
$$

Currents are obtained algebraically by inverting the stator/rotor inductance relation. Electromagnetic torque and shaft speed follow

$$
T_e=\frac{3}{2}\omega_{base}
(\psi_{s,\alpha}i_{s,\beta}-\psi_{s,\beta}i_{s,\alpha}),
$$

$$
\dot\omega_r=\frac{T_e-T_m-d(\omega_r-1)}{2h+\varepsilon},
\qquad
s=1-\omega_r.
$$

The mechanical load torque varies quadratically with speed around its nominal value.

## Initialization

The model builds a positive-sequence equivalent circuit from the solved three-phase $P$, $Q$, and voltage. It estimates and bounds the initial slip, then initializes currents, fluxes, rotor speed, electromagnetic torque, and mechanical torque at a compatible operating point. Large initial derivatives or a power mismatch normally indicate inconsistent motor data, bases, or load-flow sign conventions.

## Numerical and physical limits

The model assumes a symmetrical three-phase machine even though the EMT terminal voltages may become unbalanced during the simulation. Resistances, leakage reactances, magnetizing reactance, and inertia must be positive. Severe voltage depressions can drive the motor toward stall; check speed, slip, current, and torque together rather than interpreting terminal power alone.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A terminal voltage applied to the motor stator | pu |
| Input | `v_B` | Instantaneous phase-B terminal voltage applied to the motor stator | pu |
| Input | `v_C` | Instantaneous phase-C terminal voltage applied to the motor stator | pu |
| Output | `i_A` | Phase-A current injected by the motor model into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the motor model into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the motor model into the EMT network | pu |
| Variable | `psi_s_alpha` | Alpha-axis stator flux linkage state | pu |
| Variable | `psi_s_beta` | Beta-axis stator flux linkage state | pu |
| Variable | `psi_r_alpha` | Alpha-axis rotor flux linkage state | pu |
| Variable | `psi_r_beta` | Beta-axis rotor flux linkage state | pu |
| Variable | `omega_r` | Rotor electrical speed state | pu |
| Variable | `i_s_alpha` | Alpha-axis stator current derived from the flux states | pu |
| Variable | `i_s_beta` | Beta-axis stator current derived from the flux states | pu |
| Variable | `i_r_alpha` | Alpha-axis rotor current derived from the rotor flux states | pu |
| Variable | `i_r_beta` | Beta-axis rotor current derived from the rotor flux states | pu |
| Variable | `P_motor` | Instantaneous three-phase active power absorbed by the motor | pu |
| Variable | `Q_motor` | Instantaneous three-phase reactive power absorbed by the motor | pu |
| Variable | `T_e` | Electromagnetic torque produced by the motor | pu |
| Variable | `T_m` | Mechanical load torque opposing the electromagnetic torque | pu |
| Variable | `slip` | Rotor slip relative to synchronous speed | pu |
| Parameter | `r_s` | Stator resistance | pu |
| Parameter | `r_r` | Rotor resistance | pu |
| Parameter | `x_ls` | Stator leakage reactance | pu |
| Parameter | `x_lr` | Rotor leakage reactance | pu |
| Parameter | `x_m` | Magnetizing reactance | pu |
| Parameter | `h` | Inertia constant of the motor shaft system | s |
| Parameter | `d` | Mechanical damping coefficient | pu torque/pu speed |
| Parameter | `omega_base` | Base electrical angular frequency used to scale the state equations | rad/s |
| Parameter | `t_load_nom` | Nominal mechanical load torque used by the internal load model | pu |
| Parameter | `p0_a` | Initial phase-A active-power operating point used for initialization | pu |
| Parameter | `p0_b` | Initial phase-B active-power operating point used for initialization | pu |
| Parameter | `p0_c` | Initial phase-C active-power operating point used for initialization | pu |
| Parameter | `q0_a` | Initial phase-A reactive-power operating point used for initialization | pu |
| Parameter | `q0_b` | Initial phase-B reactive-power operating point used for initialization | pu |
| Parameter | `q0_c` | Initial phase-C reactive-power operating point used for initialization | pu |

## How to use it

1. Connect all three stator phases and map the machine data on a consistent base.
2. Initialize from a converged power flow and verify that total $P$ and $Q$ match the intended motor demand.
3. Inspect initial slip, speed, torque, and phase currents before applying events.
4. Use the double-cage model when startup or deep-slip rotor behavior cannot be fitted with one cage.
5. Perform a time-step convergence check for starts, faults, and near-stall cases.
