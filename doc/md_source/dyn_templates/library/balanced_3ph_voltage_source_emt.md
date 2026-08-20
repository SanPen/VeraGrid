# Balanced 3-phase voltage source EMT

<!-- veragrid-block-introduction:start -->
**Balanced 3-phase voltage source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

Balanced three-phase EMT voltage source.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `v_A` | Phase-A voltage | V |
| Output | `v_B` | Phase-B voltage | V |
| Output | `v_C` | Phase-C voltage | V |
| Parameter | `V` | Phase magnitude setting | model-dependent |
| Parameter | `f` | Source frequency | Hz |
