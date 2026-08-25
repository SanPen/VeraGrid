# SQRT(C1/C2)

This is Basic Block Catalog type `62` (`SQRT(C1/C2)`). It evaluates the mathematical function identified by the block name.

<!-- veragrid-block-introduction:start -->
**SQRT(C1/C2)** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Math and Functions / Constants and Scaling`.
- Inputs: 0.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 2.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - SQRT(C1/C2)_{yo0})
$$

$$
SQRT(C1/C2)_{yo0}(t_0) = \sqrt{\frac{C1}{C2}}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `C1` | Configurable model parameter | model-dependent |
| Parameter | `C2` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
