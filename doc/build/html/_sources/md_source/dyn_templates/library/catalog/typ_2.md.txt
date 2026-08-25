# a(x-c1)(x-c2)

This is Basic Block Catalog type `2` (`a(x-c1)(x-c2)`). It evaluates the mathematical function identified by the block name.

<!-- veragrid-block-introduction:start -->
**a(x-c1)(x-c2)** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Math and Functions / Scaling and Products`.
- Inputs: 1.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 3.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - a \cdot (yi - c1) \cdot (yi - c2))
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `a` | Configurable model parameter | model-dependent |
| Parameter | `c1` | Configurable model parameter | model-dependent |
| Parameter | `c2` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
