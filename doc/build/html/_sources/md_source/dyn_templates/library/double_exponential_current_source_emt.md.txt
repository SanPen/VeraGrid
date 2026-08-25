# Double exponential current source EMT

<!-- veragrid-block-introduction:start -->
**Double exponential current source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

Transient EMT current source using a double-exponential waveform.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `i` | Surge current | A |
| Parameter | `Ipk` | Peak scale | A |
| Parameter | `tau1` | Front time constant | s |
| Parameter | `tau2` | Tail time constant | s |
