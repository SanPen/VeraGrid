# R load EMT

<!-- veragrid-block-introduction:start -->
**R load EMT** describes how electrical demand responds to terminal voltage, frequency, or internal states. Static impedance/current/power components and dynamic load states produce different fault and recovery behavior, so the selected formulation materially changes system damping and voltage stability.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

EMT shunt resistive load.

## Behavior

The block creates one resistive shunt branch for every enabled phase. Its
default topology is three-wire ABC. The selected star connection determines
whether each phase voltage is measured against an internal star point or an
available grounded reference.

For each active phase, the constitutive relation is

$$
i = \frac{v}{R}
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
| Parameter | `R` | Per-phase resistance | ohm |

## How to use it

- Keep `R` strictly positive.
- Match the enabled phases and connection type to the static network.
- Use RLC Combo when resistance, inductance, and capacitance must coexist in one shunt.
