# Balanced 3-phase current source EMT

<!-- veragrid-block-introduction:start -->
**Balanced 3-phase current source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

Balanced three-phase EMT current source.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `i_A` | Phase-A current | A |
| Output | `i_B` | Phase-B current | A |
| Output | `i_C` | Phase-C current | A |
| Parameter | `I` | Phase magnitude setting | model-dependent |
| Parameter | `f` | Source frequency | Hz |
