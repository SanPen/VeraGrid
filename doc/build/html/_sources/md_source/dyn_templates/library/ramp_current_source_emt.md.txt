# Ramp current source EMT

<!-- veragrid-block-introduction:start -->
**Ramp current source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

EMT current source with a ramp profile.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `i` | Generated current | A |
| Parameter | `slope` | Ramp slope | A/s |
| Parameter | `t_start` | Ramp start time | s |
