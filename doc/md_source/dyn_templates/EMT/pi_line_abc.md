# PI line

<!-- veragrid-block-introduction:start -->
**PI line** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

This model represents a three-phase pi-section transmission line for EMT studies.

### Purpose

It is a phase-selective EMT pi-line model with explicit mapped `R`, `L`, and `C` parameter matrices.

### Behavior

- Uses active from-side and to-side terminal voltages as inputs.
- Evolves series-current and shunt-charge-related dynamic variables.
- Computes branch-port currents on both ends.
- Reduces the full NABC parameter matrices to the physically active phase set.

### Characteristics

- EMT branch model based on a pi equivalent.
- Suitable for detailed phase-domain line studies.
- More detailed than the RMS line power-flow-style template.
## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `vf_N` | From-side neutral terminal voltage when the neutral is active | pu |
| Input | `vf_A` | From-side phase-A terminal voltage when phase A is active | pu |
| Input | `vf_B` | From-side phase-B terminal voltage when phase B is active | pu |
| Input | `vf_C` | From-side phase-C terminal voltage when phase C is active | pu |
| Input | `vt_N` | To-side neutral terminal voltage when the neutral is active | pu |
| Input | `vt_A` | To-side phase-A terminal voltage when phase A is active | pu |
| Input | `vt_B` | To-side phase-B terminal voltage when phase B is active | pu |
| Input | `vt_C` | To-side phase-C terminal voltage when phase C is active | pu |
| Output | `if_N` | From-side neutral current when the neutral is active | pu |
| Output | `if_A` | From-side phase-A current when phase A is active | pu |
| Output | `if_B` | From-side phase-B current when phase B is active | pu |
| Output | `if_C` | From-side phase-C current when phase C is active | pu |
| Output | `it_N` | To-side neutral current when the neutral is active | pu |
| Output | `it_A` | To-side phase-A current when phase A is active | pu |
| Output | `it_B` | To-side phase-B current when phase B is active | pu |
| Output | `it_C` | To-side phase-C current when phase C is active | pu |
| Variable | `i_ser_phase` | Series-current state for each active conductor | pu |
| Variable | `q_f_phase` | From-side shunt-charge state for each active conductor | pu·s equivalent state |
| Variable | `q_t_phase` | To-side shunt-charge state for each active conductor | pu·s equivalent state |
| Variable | `i_cap_f_phase` | From-side shunt-capacitor current variable for each active conductor | pu |
| Variable | `i_cap_t_phase` | To-side shunt-capacitor current variable for each active conductor | pu |
| Variable | `if_phase` | From-side branch-port current variable for each active conductor | pu |
| Variable | `it_phase` | To-side branch-port current variable for each active conductor | pu |
| Parameter | `Rnn..Rcc` | Full NABC resistance matrix entries mapped from the line data | pu |
| Parameter | `Linv_nn..Linv_cc` | Full NABC inverse-inductance matrix entries mapped from the line data | 1/(pu·s) |
| Parameter | `Cnn..Ccc` | Full NABC shunt-capacitance matrix entries mapped from the line data | pu·s |

## How to use it

- Use this template for phase-domain EMT line studies when a pi-equivalent representation is sufficient.
- Use Bergeron or JMARTI-style alternatives when propagation-delay behavior is more important.
