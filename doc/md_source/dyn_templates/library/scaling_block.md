# Scaling block

### Purpose

This block scales a signal by one gain factor and optionally one offset, depending on the exact template.

### Behavior

- Receives one signal.
- Multiplies it by one gain.
- May also add one offset in affine variants.

## Characteristic equations

$$
y = kx
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Scaled output signal | model-dependent |
| Parameter | `k` | Multiplicative gain | model-dependent |

## How to use it

- Use this block when a signal needs normalization, conversion, or proportional scaling.
