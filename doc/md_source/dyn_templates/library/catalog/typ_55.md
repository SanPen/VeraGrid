# C [param: C; form A]

This is Basic Block Catalog type `55` (`C`). It evaluates the mathematical function identified by the block name.

<!-- veragrid-block-introduction:start -->
**C [param: C; form A]** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Math and Functions / Constants and Scaling`.
- Inputs: 0.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 1.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - C)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `C` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
