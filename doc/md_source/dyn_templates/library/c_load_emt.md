# C load EMT

<!-- veragrid-block-introduction:start -->
**C load EMT** describes how electrical demand responds to terminal voltage, frequency, or internal states. Static impedance/current/power components and dynamic load states produce different fault and recovery behavior, so the selected formulation materially changes system damping and voltage stability.

## Typical use

- Use the formulation that matches the time scale and measured behavior of the represented demand.
- Initialize active and reactive demand from the power flow and verify the voltage-dependence convention.
<!-- veragrid-block-introduction:end -->

EMT shunt capacitive load.

## Behavior

The block creates one capacitive shunt branch for every enabled phase. Current
depends on the phase-voltage derivative, so the template exposes the derivative
quantities required by the EMT formulation. The default phase selection is
three-wire ABC.

For each active phase,

$$
i = C\frac{dv}{dt}
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
| Parameter | `C` | Per-phase capacitance | F |

## How to use it

- Keep `C` non-negative and use units consistent with the EMT base.
- Ensure voltage-derivative variables are available in the enclosing EMT problem.
- Match the phase selection and star connection to the physical shunt topology.
