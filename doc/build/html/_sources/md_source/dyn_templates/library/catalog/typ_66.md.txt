# balanced

This is Basic Block Catalog type `66` (`balanced`). It converts signals between the coordinate systems or units identified by the block name.

<!-- veragrid-block-introduction:start -->
**balanced** is a coordinate-transformation block. In three-phase analysis, Clarke and Park transforms separate stationary or rotating components so sinusoidal phase quantities can be controlled as nearly constant d-q signals. The selected scaling determines whether amplitude or instantaneous power is preserved.

## Typical use

- Use it to connect phase-domain electrical quantities with d-q or sequence-domain control laws.
- Keep angle orientation, axis alignment, phase order, and power/amplitude convention consistent.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Transforms / RMS and Sequence`.
- Inputs: 0.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 0.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - 0)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `yo` | Output signal produced by the block | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
