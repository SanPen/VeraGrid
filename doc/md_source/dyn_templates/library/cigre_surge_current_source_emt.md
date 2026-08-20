# CIGRE surge current source EMT

<!-- veragrid-block-introduction:start -->
**CIGRE surge current source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

CIGRE-standard surge current source for EMT studies.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `i` | Surge current | A |
| Parameter | `Ipk` | Peak current scale | A |
| Parameter | `shape` | Surge-shape configuration | model-dependent |
