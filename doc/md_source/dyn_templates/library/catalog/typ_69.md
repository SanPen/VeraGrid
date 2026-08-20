# Gradient limiter (constant)

This is Basic Block Catalog type `69` (`gradlim_const`). It applies the declared limiting or nonlinear relation to its input signals.

<!-- veragrid-block-introduction:start -->
**Gradient limiter (constant)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Limits and Nonlinearities / Limiters`.
- Inputs: 1.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 2.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - proc_{gradlim\_const\_0})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `gradmax` | Configurable model parameter | model-dependent |
| Parameter | `gradmin` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
