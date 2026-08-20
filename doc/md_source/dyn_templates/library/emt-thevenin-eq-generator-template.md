# emt thevenin eq generator template

<!-- veragrid-block-introduction:start -->
**emt thevenin eq generator template** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

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
