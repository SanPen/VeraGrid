# DC current source EMT

<!-- veragrid-block-introduction:start -->
**DC current source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

Fixed DC EMT current source. It reads the connected DC-bus voltage for its
network interface and imposes a configured injected current independently of
that voltage.

## Characteristic equation

$$
i_{dc} = I_{src}
$$

Positive `I_src` injects current into the connected DC bus according to the
template convention.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_dc` | Connected DC-bus voltage | V |
| Output | `i_dc` | Current injected into the DC bus | A |
| Parameter | `I_src` | Fixed current command | A |

## How to use it

- Use this block for an ideal current injection or a simple DC-side test source.
- Use the controlled variant when another block must provide the current command.
- Do not use it as a detailed battery or converter replacement when DC dynamics matter.
