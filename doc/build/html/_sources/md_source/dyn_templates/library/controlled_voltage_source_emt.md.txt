# Controlled voltage source EMT

<!-- veragrid-block-introduction:start -->
**Controlled voltage source EMT** imposes or controls an electrical excitation in an EMT network. Depending on the variant, it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent the grid, a controlled converter terminal, or a standardized transient waveform.

## Typical use

- Use it as a network boundary, disturbance source, or controlled electrical terminal.
- Match polarity, phase convention, grounding, and source impedance to the connected topology.
<!-- veragrid-block-introduction:end -->

Single-phase EMT voltage source driven by an input signal.

### Purpose

This block converts one runtime command signal into one imposed single-phase EMT voltage. Use it when an external controller or supervisory logic must directly drive a voltage source.

### Behavior

- Receives one command input.
- Maps that command into one instantaneous voltage output.
- Behaves like one ideal controlled source, with the network determining the resulting current.

### Characteristics

- EMT controlled source primitive.
- Single-phase ideal voltage source.
- Useful as an actuator-like source inside custom converter or source assemblies.

## How it works

The input signal is interpreted as the source command, usually directly or through a simple internal scaling relation. The output voltage is imposed on the connected branch, while the rest of the circuit determines the current drawn from the source.

## Characteristic equations

$$
v(t) = u(t)
$$

or one scaled equivalent depending on the configured source convention.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `u` | Commanded source value | model-dependent |
| Output | `v` | Imposed terminal voltage | V |

## How to use it

- Use it when a controller or another block must directly generate one EMT voltage waveform.
- Add filtering, limits, or impedance externally if the source must behave less ideally.
