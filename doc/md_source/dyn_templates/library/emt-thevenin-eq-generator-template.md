# emt thevenin eq generator template

### Purpose

This reusable library template inserts one compact EMT three-phase Thevenin-equivalent generator.

### Behavior

- Uses three phase voltages as inputs.
- Produces three phase injected currents.
- Represents one source behind impedance with internal emf reconstruction.

### Characteristics

- Runtime template exposed through the dynamic editor `Templates` branch.
- Compact EMT source model.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Phase-A terminal voltage | pu |
| Input | `v_B` | Phase-B terminal voltage | pu |
| Input | `v_C` | Phase-C terminal voltage | pu |
| Output | `i_A` | Phase-A injected current | pu |
| Output | `i_B` | Phase-B injected current | pu |
| Output | `i_C` | Phase-C injected current | pu |
| Variable | `theta` | Internal source angle | rad |
| Parameter | `omega_base` | Base angular frequency | rad/s |
| Parameter | `R_s` | Source resistance | pu |
| Parameter | `X_s` | Source reactance | pu |

## How to use it

- Use this template when one reusable compact EMT generator source is needed in the library.
