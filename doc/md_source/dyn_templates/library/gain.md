# Gain

<!-- veragrid-block-introduction:start -->
**Gain** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

The Gain block multiplies one input signal by a configurable scalar. It is the
basic proportional operation used for unit conversion, feedback gains, and
linear signal scaling.

## Characteristic equation

$$
y = k u
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `u` | Signal to scale | model-dependent |
| Output | `y` | Scaled signal | model-dependent |
| Parameter | `k` | Multiplicative gain | `y/u` |

The block is algebraic: it does not add a state or a delay to the signal path.
