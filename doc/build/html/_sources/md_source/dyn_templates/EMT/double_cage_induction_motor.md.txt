# Double cage induction motor

<!-- veragrid-block-introduction:start -->
**Double cage induction motor** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents a double-cage induction motor in phase-domain EMT form.

## Scope and model level

This is the Level-3 induction-motor model. Like the single-cage model, it uses a three-wire ABC stator interface and stationary $\alpha\beta$ electrical coordinates. It adds a second rotor cage so the equivalent rotor impedance changes naturally with slip. This improves the representation of starting torque, inrush current, and deep-bar behavior.

Use Level 3 when both running and high-slip characteristics must be matched. Use the simpler Level-2 model when one cage fits the study data and the extra parameters cannot be identified reliably.

## State equations

The model retains stator flux, two pairs of rotor-cage fluxes, and normalized rotor speed. The stator flux follows

$$
\dot\psi_{s,\alpha}=v_\alpha-r_si_{s,\alpha},
\qquad
\dot\psi_{s,\beta}=v_\beta-r_si_{s,\beta}.
$$

For cage $k\in\{1,2\}$,

$$
\dot\psi_{rk,\alpha}=-r_{rk}i_{rk,\alpha}-\omega_{r,e}\psi_{rk,\beta},
$$

$$
\dot\psi_{rk,\beta}=-r_{rk}i_{rk,\beta}+\omega_{r,e}\psi_{rk,\alpha}.
$$

The coupled inductance matrix determines stator and cage currents from all six flux components. Electromagnetic torque is computed from stator flux and current, and the shaft equation is

$$
\dot\omega_r=\frac{T_e-T_m-d(\omega_r-1)}{2h+\varepsilon},
\qquad s=1-\omega_r.
$$

## Initialization

The initializer forms a positive-sequence double-cage equivalent circuit from solved terminal voltage and power. It estimates a bounded slip, divides rotor current between the two cage impedances, and seeds stator flux, both cage fluxes, speed, and torque consistently. The two cage parameter sets must be physically distinct and use the same per-unit base; otherwise the added model order provides no reliable benefit.

## Numerical and physical limits

This is still a symmetrical three-phase machine model, although unbalanced ABC terminal waveforms are accepted during EMT simulation. The additional rotor time constant can make the system stiffer than the single-cage model. Inspect both cage currents during starting and faults, and use time-step convergence when one cage has very small leakage or resistance.

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
| Variable | `psi_r1_alpha` | Alpha-axis flux linkage of the first rotor cage | pu |
| Variable | `psi_r1_beta` | Beta-axis flux linkage of the first rotor cage | pu |
| Variable | `psi_r2_alpha` | Alpha-axis flux linkage of the second rotor cage | pu |
| Variable | `psi_r2_beta` | Beta-axis flux linkage of the second rotor cage | pu |
| Variable | `omega_r` | Rotor electrical speed state | pu |
| Variable | `i_s_alpha` | Alpha-axis stator current derived from the flux states | pu |
| Variable | `i_s_beta` | Beta-axis stator current derived from the flux states | pu |
| Variable | `i_r1_alpha` | Alpha-axis current in the first rotor cage | pu |
| Variable | `i_r1_beta` | Beta-axis current in the first rotor cage | pu |
| Variable | `i_r2_alpha` | Alpha-axis current in the second rotor cage | pu |
| Variable | `i_r2_beta` | Beta-axis current in the second rotor cage | pu |
| Variable | `P_motor` | Instantaneous three-phase active power absorbed by the motor | pu |
| Variable | `Q_motor` | Instantaneous three-phase reactive power absorbed by the motor | pu |
| Variable | `T_e` | Electromagnetic torque produced by the motor | pu |
| Variable | `T_m` | Mechanical load torque opposing the electromagnetic torque | pu |
| Variable | `slip` | Rotor slip relative to synchronous speed | pu |
| Parameter | `r_s` | Stator resistance | pu |
| Parameter | `r_r1` | Rotor resistance of the first cage | pu |
| Parameter | `x_lr1` | Rotor leakage reactance of the first cage | pu |
| Parameter | `r_r2` | Rotor resistance of the second cage | pu |
| Parameter | `x_lr2` | Rotor leakage reactance of the second cage | pu |
| Parameter | `x_ls` | Stator leakage reactance | pu |
| Parameter | `x_m` | Magnetizing reactance shared by stator and rotor cages | pu |
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

1. Connect all three stator phases and map stator, magnetizing, mechanical, and both cage parameter sets.
2. Initialize from a converged operating point and verify total power, slip, and torque balance.
3. Compare starting current and torque against manufacturer or test data when tuning the two cages.
4. Prefer the single-cage model if only normal-running behavior is known.
5. Monitor speed, slip, both cage currents, and electromagnetic torque during severe voltage events.
