# Controlled DC voltage source EMT

<!-- veragrid-block-introduction:start -->
**Controlled DC voltage source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

DC EMT voltage source driven by an input signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `u` | Commanded DC voltage | V |
| Output | `v_dc` | Imposed DC voltage | V |
