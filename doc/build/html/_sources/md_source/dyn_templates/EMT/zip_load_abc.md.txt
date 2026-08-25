# ZIP load

<!-- veragrid-block-introduction:start -->
**ZIP load** describes how electrical demand responds to terminal voltage. Its constant-impedance, constant-current, and constant-power components produce different fault and recovery behavior, so their proportions materially change the simulated response.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

This model represents a phase-selective EMT ZIP load with per-phase voltage filtering and polynomial voltage dependence.

It is not restricted to ABC. Any non-empty subset of phases `A`, `B`, and `C` can be enabled. Star connections can use ground, an external neutral, or a floating internal star point; delta connections create branches between enabled phase pairs. Only active conductors create ports, states, equations, and mappings.

### Purpose

It is a phase-selective EMT ZIP load with per-phase SOGI filtering and polynomial voltage dependence.

### Behavior

- Uses the active phase voltages as external inputs.
- Filters each active phase voltage with internal SOGI states.
- Computes per-phase active and reactive load behavior from ZIP coefficients.
- Produces per-phase current injections accordingly.

### Characteristics

- Dynamic phase-domain load model.
- Supports impedance/current/power blending through ZIP coefficients.
- More realistic than a fixed load when voltage dependence matters.

### Characteristic equations

For each active branch, let $r_X=V_X/V_0$ be the filtered voltage magnitude normalized by its reference. The ZIP laws are

$$
P_X=P_{0,X}(a_1r_X^2+a_2r_X+a_3),
$$

$$
Q_X=Q_{0,X}(a_4r_X^2+a_5r_X+a_6).
$$

The quadratic terms represent constant impedance, the linear terms constant current, and the constant terms constant power. The current injection is reconstructed from the filtered in-phase and quadrature voltage components with a regularized denominator.

For a pure component, the corresponding coefficient triplet normally sums to one. Mixed coefficients should be checked at $r_X=1$ so the model reproduces the nominal operating-point power.
## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Phase-A terminal voltage when phase A is active | pu |
| Input | `v_B` | Phase-B terminal voltage when phase B is active | pu |
| Input | `v_C` | Phase-C terminal voltage when phase C is active | pu |
| Output | `i_A` | Phase-A current injection when phase A is active | pu |
| Output | `i_B` | Phase-B current injection when phase B is active | pu |
| Output | `i_C` | Phase-C current injection when phase C is active | pu |
| Variable | `u_phase` | In-phase SOGI state for each active phase | pu |
| Variable | `q_phase` | Quadrature SOGI state for each active phase | pu |
| Variable | `Vphase2` | Squared filtered voltage magnitude variable for each active phase | pu^2 |
| Variable | `Vmphase` | Filtered voltage magnitude variable for each active phase | pu |
| Variable | `rphase` | Normalized voltage ratio used by the ZIP polynomial for each active phase | pu |
| Variable | `P_phase` | Per-phase active load power variable | pu |
| Variable | `Q_phase` | Per-phase reactive load power variable | pu |
| Variable | `i_phase` | Per-phase output current variable | pu |
| Parameter | `V0` | Nominal voltage magnitude used by the ZIP law | pu |
| Parameter | `a1` | Constant-impedance active-power coefficient | pu |
| Parameter | `a2` | Constant-current active-power coefficient | pu |
| Parameter | `a3` | Constant-power active-power coefficient | pu |
| Parameter | `a4` | Constant-impedance reactive-power coefficient | pu |
| Parameter | `a5` | Constant-current reactive-power coefficient | pu |
| Parameter | `a6` | Constant-power reactive-power coefficient | pu |
| Parameter | `k_sogi` | SOGI filter gain | pu |
| Parameter | `eps` | Small numerical regularization constant | pu |
| Parameter | `omega` | Angular frequency used by the SOGI filter | rad/s |
| Parameter | `P0_phase` | Nominal per-phase active power setpoint | pu |
| Parameter | `Q0_phase` | Nominal per-phase reactive power setpoint | pu |

The `phase` placeholder means each enabled star branch or active delta phase pair. The explicit A/B/C rows appear only when those conductors are selected; neutral ports appear only for a neutral-star configuration.

## How to use it

- Use this template when you need an EMT load whose power changes with terminal voltage.
- It is especially useful when ZIP composition matters more than machine-type load dynamics.
- Verify the initialized total power and injection sign after choosing phases and connection.
- Retain a positive `eps` and inspect deep-fault behavior: regularization prevents singular current but does not define missing physical load-disconnection behavior.
