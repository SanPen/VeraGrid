# BESS

This model represents an EMT battery energy storage system with converter control and DC-side dynamics.

### Purpose

It is a Level-1 averaged-value grid-following Battery Energy Storage System EMT template.

### Behavior

- Uses three AC phase voltages as external inputs.
- Contains an internal battery block, imported VSC electrical/DC block, PLL, outer loop, inner current loop, and dq0/abc interface block.
- Produces three-phase current injections into the EMT network.
- Internally couples DC storage behavior with converter and AC-side control behavior.

### Characteristics

- Aggregated EMT BESS model.
- More detailed than the RMS battery template.
- Still averaged rather than switching-level.
## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Phase-A AC terminal voltage at the BESS connection point | pu |
| Input | `v_B` | Phase-B AC terminal voltage at the BESS connection point | pu |
| Input | `v_C` | Phase-C AC terminal voltage at the BESS connection point | pu |
| Output | `i_A` | Phase-A current injected into the EMT network by the BESS | pu |
| Output | `i_B` | Phase-B current injected into the EMT network by the BESS | pu |
| Output | `i_C` | Phase-C current injected into the EMT network by the BESS | pu |
| Variable | `battery block` | Internal averaged battery/DC-source submodel | submodel |
| Variable | `vsc block` | Internal averaged converter electrical/DC submodel | submodel |
| Variable | `pll block` | Internal synchronous-reference-frame PLL submodel | submodel |
| Variable | `outer loop block` | Internal BESS outer control loop submodel | submodel |
| Variable | `inner loop block` | Internal converter current-control submodel | submodel |
| Variable | `transformer block` | Internal dq0/abc interface branch block | submodel |
| Parameter | `battery Thevenin parameters` | Internal battery open-circuit-voltage and resistance-related parameters | mixed |
| Parameter | `battery SoC parameters` | State-of-charge, efficiency, and energy-capacity-related parameters | mixed |
| Parameter | `converter parameters` | Imported VSC electrical, DC-link, current-limit, and control parameters | mixed |

## How to use it

- Use this template for EMT studies of converter-based battery energy storage connected to an AC network.
- It is a plant-level averaged model, not a switching cell-level battery/converter model.
