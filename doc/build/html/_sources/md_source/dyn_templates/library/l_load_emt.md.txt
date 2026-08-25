# L load EMT

<!-- veragrid-block-introduction:start -->
**L load EMT** describes how electrical demand responds to terminal voltage, frequency, or internal states. Static impedance/current/power components and dynamic load states produce different fault and recovery behavior, so the selected formulation materially changes system damping and voltage stability.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

EMT shunt inductive load.

## Behavior

The block creates one inductive shunt branch for every enabled phase. The
inductor current is a dynamic state, so the model contributes both a state
equation and initialization constraints to the EMT system. The default phase
selection is three-wire ABC.

For each active phase,

$$
\frac{di}{dt} = \frac{v}{L}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Phase-A voltage when enabled | pu |
| Input | `v_B` | Phase-B voltage when enabled | pu |
| Input | `v_C` | Phase-C voltage when enabled | pu |
| Output | `i_A` | Phase-A current injection | pu |
| Output | `i_B` | Phase-B current injection | pu |
| Output | `i_C` | Phase-C current injection | pu |
| Parameter | `L` | Per-phase inductance | H |

## How to use it

- Keep `L` strictly positive and use units consistent with the EMT base.
- Match the enabled phases and star connection to the connected network.
- Inspect initialization if the desired initial inductor current is non-zero.
