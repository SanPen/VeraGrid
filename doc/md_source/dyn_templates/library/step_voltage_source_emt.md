# Step voltage source EMT

<!-- veragrid-block-introduction:start -->
**Step voltage source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

EMT voltage source with a step transition.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `v` | Generated voltage | V |
| Parameter | `V0` | Initial level | V |
| Parameter | `V1` | Final level | V |
| Parameter | `t_step` | Step time | s |
