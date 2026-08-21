# Exponential load

<!-- veragrid-block-introduction:start -->
**Exponential load** describes how electrical demand responds to terminal voltage. Its active- and reactive-power exponents produce different fault and recovery behavior, so the selected formulation materially changes system damping and voltage stability.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

This is a phase-selective EMT model. Any non-empty subset of `A`, `B`, and `C` can be enabled, with star or delta connection behavior selected independently. ABC is the default arrangement, not a restriction of the model.

## Model behavior

Each active branch uses a second-order generalized integrator (SOGI) to obtain in-phase and quadrature voltage components. For branch $X$,

$$
\dot u_X=k_{sogi}\omega(v_X-u_X)-\omega q_X,
$$

$$
\dot q_X=\omega u_X.
$$

The filtered magnitude is regularized close to zero voltage:

$$
V_X=\sqrt{u_X^2+q_X^2+\varepsilon}.
$$

Active and reactive demand then follow

$$
P_X=P_{0,X}\left(\frac{V_X}{V_0}\right)^a,
\qquad
Q_X=Q_{0,X}\left(\frac{V_X}{V_0}\right)^b.
$$

The branch current is reconstructed from the filtered voltage components and the requested complex power. Internal safe denominators keep the expression finite during deep voltage depressions.

## Phase and connection configurations

- Star configurations create one load branch for every enabled phase. The reference can be grounded, externally neutral-connected, or a solved floating star point.
- Delta configurations create branches only between enabled phase pairs and require at least two active phases.
- Disabled conductors do not create ports, equations, states, or external mappings.

The generic branch notation in the equations and table applies equally to A, AB, AC, BC, ABC, and the applicable neutral-inclusive star interfaces.

## Exponent selection

An exponent of 0 gives constant power, 1 gives approximately constant current, and 2 gives constant impedance in terms of power-versus-voltage magnitude. Active and reactive demand may use different exponents. Use measured composite-load behavior where available instead of assuming the same exponent for both.

## Initialization and numerical behavior

The SOGI states are initialized from the solved branch voltages and the power setpoints from the operating point. Confirm that `V0`, `P0_X`, and `Q0_X` use the same base and sign convention as the connected device. The `eps` regularization prevents division by zero but does not make a constant-power load physically realistic at zero voltage; inspect fault recovery results when small terminal voltages are expected.

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

Only rows belonging to enabled phases are instantiated. For a delta model, the same quantities are associated with active phase pairs rather than phase-to-neutral branches.

## How to use it

1. Enable the required phases and choose the physical star or delta connection.
2. Map the nominal branch powers and reference voltage from the initialized network.
3. Set `a` and `b` from the intended voltage response.
4. Verify the initial total active and reactive power, including the load/injection sign.
5. Apply a small voltage disturbance before relying on severe-fault results, and confirm that the selected exponents give the expected response.
