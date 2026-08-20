# Scaling block

<!-- veragrid-block-introduction:start -->
**Scaling block** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

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
