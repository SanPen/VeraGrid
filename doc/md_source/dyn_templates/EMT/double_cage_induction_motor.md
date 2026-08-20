# Double cage induction motor

<!-- veragrid-block-introduction:start -->
**Double cage induction motor** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents a double-cage induction motor in phase-domain EMT form.

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
