# Voltage source EMT

Single-phase EMT voltage source.

### Purpose

This block provides one imposed single-phase voltage waveform to an EMT network. Use it when one branch or subsystem must be driven by a prescribed electrical potential rather than by a solved dynamic source model.

### Behavior

- Generates one voltage output signal.
- Holds or evaluates the source waveform from its configured magnitude or waveform settings.
- Acts as an ideal source, so the network must determine the resulting current elsewhere in the connected circuit.

### Characteristics

- EMT source primitive.
- Single-phase ideal source.
- Useful for tests, source injection, and small custom EMT assemblies.

## How it works

The block directly imposes the voltage assigned to its output channel. It does not solve internal electromechanical or converter dynamics. Any current drawn from the source is determined by the external network equations and connected elements.

## Characteristic equations

$$
v(t) = V(t)
$$

where `V(t)` may be one constant, one ramp, one step, or another prescribed waveform depending on the source variant or parameterization used around the block.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `v` | Imposed terminal voltage | V |
| Parameter | `V` | Source magnitude or waveform setting | model-dependent |

## How to use it

- Use it when you need one ideal single-phase voltage excitation in an EMT network.
- Use one of the balanced, controlled, step, ramp, or arbitrary waveform source variants when the waveform must follow a more specific pattern.
