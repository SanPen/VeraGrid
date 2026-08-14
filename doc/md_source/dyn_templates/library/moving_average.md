# Moving average

### Purpose

A moving-average block filters a signal to remove fast variations and keep a smoothed trend.

### Behavior

- Receives one input signal.
- Outputs a filtered version of the signal.
- Reduces noise and fast oscillations.

### Characteristics

- Useful for measurements, supervisory logic, and slow outer control loops.

## Characteristic equations

$$
y(t) = \frac{1}{T_w}\int_{t-T_w}^{t} x(\tau) \, d\tau
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to be averaged | model-dependent |
| Output | `yo` | Smoothed output signal | model-dependent |
| Parameter | `Tw` | Averaging window or effective filter time | s |

## How to use it

- Use it when a raw signal is too noisy or too oscillatory for direct control use.
- Avoid large windows when fast dynamic response is needed.
