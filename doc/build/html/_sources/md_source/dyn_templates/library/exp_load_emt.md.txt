# Exponential load EMT

<!-- veragrid-block-introduction:start -->
**Exponential load EMT** describes how electrical demand responds to terminal voltage, frequency, or internal states. Static impedance/current/power components and dynamic load states produce different fault and recovery behavior, so the selected formulation materially changes system damping and voltage stability.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

Voltage-dependent EMT exponential load.

## Behavior

The block converts each enabled phase voltage into a current injection whose
active and reactive power vary with voltage magnitude. It is useful when a
constant-power approximation is too rigid but a detailed motor or converter
model is unnecessary. The default editor configuration is three-wire ABC; the
phase selection and star connection can be changed in General options.

For a phase voltage magnitude `V`, the active and reactive demand follow the
generic exponential laws

$$
P = P_0\left(\frac{V}{V_0}\right)^{\alpha_p}
$$

$$
Q = Q_0\left(\frac{V}{V_0}\right)^{\alpha_q}
$$

and the EMT equations derive the corresponding instantaneous phase current.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Phase-A terminal voltage | pu |
| Input | `v_B` | Phase-B terminal voltage | pu |
| Input | `v_C` | Phase-C terminal voltage | pu |
| Output | `i_A` | Phase-A current injection | pu |
| Output | `i_B` | Phase-B current injection | pu |
| Output | `i_C` | Phase-C current injection | pu |
| Parameter | `alpha_p` | Active-power voltage exponent | pu |
| Parameter | `alpha_q` | Reactive-power voltage exponent | pu |

## How to use it

- Match the enabled phases to the connected static network.
- Use the star connection option only when the intended neutral/reference
  topology is available.
- Confirm the power-flow reference values before starting EMT initialization.
