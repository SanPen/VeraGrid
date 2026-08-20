# Exponential load (ABC)

<!-- veragrid-block-introduction:start -->
**Exponential load (ABC)** describes how electrical demand responds to terminal voltage, frequency, or internal states. Static impedance/current/power components and dynamic load states produce different fault and recovery behavior, so the selected formulation materially changes system damping and voltage stability.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

This model represents a three-phase EMT load with exponential voltage-dependent behavior.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A terminal voltage when phase A is active in the load | pu |
| Input | `v_B` | Instantaneous phase-B terminal voltage when phase B is active in the load | pu |
| Input | `v_C` | Instantaneous phase-C terminal voltage when phase C is active in the load | pu |
| Output | `i_A` | Phase-A current drawn by the exponential load and injected into the EMT network with load sign convention | pu |
| Output | `i_B` | Phase-B current drawn by the exponential load and injected into the EMT network with load sign convention | pu |
| Output | `i_C` | Phase-C current drawn by the exponential load and injected into the EMT network with load sign convention | pu |
| Variable | `u_A` | In-phase SOGI state used to estimate the filtered phase-A voltage component | pu |
| Variable | `u_B` | In-phase SOGI state used to estimate the filtered phase-B voltage component | pu |
| Variable | `u_C` | In-phase SOGI state used to estimate the filtered phase-C voltage component | pu |
| Variable | `q_A` | Quadrature SOGI state used to estimate the filtered phase-A voltage component | pu |
| Variable | `q_B` | Quadrature SOGI state used to estimate the filtered phase-B voltage component | pu |
| Variable | `q_C` | Quadrature SOGI state used to estimate the filtered phase-C voltage component | pu |
| Variable | `V_A` | Filtered magnitude of the phase-A voltage used in the exponential power law | pu |
| Variable | `V_B` | Filtered magnitude of the phase-B voltage used in the exponential power law | pu |
| Variable | `V_C` | Filtered magnitude of the phase-C voltage used in the exponential power law | pu |
| Variable | `P_A` | Active power absorbed on phase A after applying the voltage exponent | pu |
| Variable | `P_B` | Active power absorbed on phase B after applying the voltage exponent | pu |
| Variable | `P_C` | Active power absorbed on phase C after applying the voltage exponent | pu |
| Variable | `Q_A` | Reactive power absorbed on phase A after applying the voltage exponent | pu |
| Variable | `Q_B` | Reactive power absorbed on phase B after applying the voltage exponent | pu |
| Variable | `Q_C` | Reactive power absorbed on phase C after applying the voltage exponent | pu |
| Variable | `i_A` | Algebraic phase-A current computed from the phase-A power and voltage | pu |
| Variable | `i_B` | Algebraic phase-B current computed from the phase-B power and voltage | pu |
| Variable | `i_C` | Algebraic phase-C current computed from the phase-C power and voltage | pu |
| Parameter | `V0` | Reference voltage magnitude used in the exponential active- and reactive-power laws | pu |
| Parameter | `a` | Exponent that makes active power vary with voltage magnitude | dimensionless |
| Parameter | `b` | Exponent that makes reactive power vary with voltage magnitude | dimensionless |
| Parameter | `k_sogi` | SOGI gain that sets the filter tracking aggressiveness | dimensionless |
| Parameter | `eps` | Small regularization term used to avoid singular behavior near zero voltage | pu |
| Parameter | `omega` | Angular frequency used by the SOGI filter states | rad/s |
| Parameter | `P0_A` | Nominal phase-A active power at the reference voltage `V0` | pu |
| Parameter | `P0_B` | Nominal phase-B active power at the reference voltage `V0` | pu |
| Parameter | `P0_C` | Nominal phase-C active power at the reference voltage `V0` | pu |
| Parameter | `Q0_A` | Nominal phase-A reactive power at the reference voltage `V0` | pu |
| Parameter | `Q0_B` | Nominal phase-B reactive power at the reference voltage `V0` | pu |
| Parameter | `Q0_C` | Nominal phase-C reactive power at the reference voltage `V0` | pu |
