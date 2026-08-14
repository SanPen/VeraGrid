# Current source EMT

Single-phase EMT current source.

### Purpose

This block injects one prescribed single-phase current into an EMT network. Use it when one branch current must be imposed directly instead of being created by an internal converter or machine model.

### Behavior

- Generates one source-current output.
- Uses its configured magnitude or waveform parameters to determine the injected current.
- Leaves the resulting terminal voltage to be determined by the surrounding network.

### Characteristics

- EMT source primitive.
- Single-phase ideal current source.
- Useful for tests, current injection studies, and custom waveform forcing.

## How it works

The block directly prescribes the source current waveform. The connected network then determines what voltage is needed to satisfy that current injection. The block itself does not include internal current-control dynamics or impedance.

## Characteristic equations

$$
i(t) = I(t)
$$

where `I(t)` is the prescribed source waveform defined by the chosen source parameters.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `i` | Imposed source current | A |
| Parameter | `I` | Source magnitude or waveform setting | model-dependent |

## How to use it

- Use it when the EMT network must receive one forced current waveform.
- Use controlled or waveform-specific current-source variants when the injection must react to an external command or follow a particular transient shape.
