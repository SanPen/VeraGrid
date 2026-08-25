# Constant

<!-- veragrid-block-introduction:start -->
**Constant** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

The Constant block publishes a fixed scalar value. It is useful for set-points,
biases, limits, and any signal that must remain unchanged during a simulation.

## Characteristic equation

$$
y = k
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `y` | Constant output signal | model-dependent |
| Parameter | `k` | Configured constant value | same as `y` |

The block has no input and no dynamic state. Changing `k` through General
options rebuilds the symbolic constant used by downstream equations.
