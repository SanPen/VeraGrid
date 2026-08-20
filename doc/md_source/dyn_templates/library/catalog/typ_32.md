# yi1 not equals yi2

This is Basic Block Catalog type `32` (`yi1 not equals yi2`). It implements logical or event-driven signal behaviour.

<!-- veragrid-block-introduction:start -->
**yi1 not equals yi2** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Logic and Events / Comparators`.
- Inputs: 2.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 0.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - (proc_{select\_const\_0} \cdot 0 + (1 - proc_{select\_const\_0}) \cdot 1))
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | Input signal consumed by the block | model-dependent |
| Input | `yi2` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
