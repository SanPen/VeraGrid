# ZIP load (ABC)

This model represents a phase-selective EMT ZIP load with per-phase voltage filtering and polynomial voltage dependence.

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

## How to use it

- Use this template when you need an EMT load whose power changes with terminal voltage.
- It is especially useful when ZIP composition matters more than machine-type load dynamics.
