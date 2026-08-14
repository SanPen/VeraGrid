# RMS value

### Purpose

An RMS-value block computes the root-mean-square magnitude of a signal over one effective period or window.

### Behavior

- Receives one signal, typically oscillatory.
- Produces a non-negative magnitude estimate representing its RMS value.

### Characteristics

- Useful for monitoring voltage, current, or other waveform magnitudes.
- Available in absolute and per-unit oriented variants.

## Characteristic equations

$$
x_{rms} = \sqrt{\frac{1}{T}\int_{t-T}^{t} x^2(\tau) \, d\tau}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal whose RMS magnitude is to be computed | model-dependent |
| Output | `yo` | RMS magnitude output | model-dependent |
| Parameter | `T` | Effective RMS window or period used by the implementation | s |

## How to use it

- Use it when a waveform must be summarized by a slowly varying magnitude.
- Make sure the RMS window is appropriate for the signal frequency.
