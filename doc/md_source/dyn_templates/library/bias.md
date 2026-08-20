# Bias

<!-- veragrid-block-introduction:start -->
**Bias** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

### Purpose

This block adds one constant offset to a signal.

### Behavior

- Receives one signal.
- Adds one bias term.
- Outputs the shifted signal.

## Characteristic equations

$$
y = x + b
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Biased output signal | model-dependent |
| Parameter | `b` | Constant offset added to the input | model-dependent |

## How to use it

- Use this block when a signal must be shifted by a constant amount.
