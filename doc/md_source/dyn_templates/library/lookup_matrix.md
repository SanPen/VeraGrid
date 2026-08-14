# Lookup matrix

### Purpose

This block approximates one two-dimensional nonlinear relation from one stored matrix.

### Behavior

- Receives two independent inputs.
- Interpolates on a matrix or surface.
- Outputs one approximated scalar value.

### Characteristics

- Useful for efficiency maps, saturation surfaces, and two-input nonlinear relationships.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First independent input variable | model-dependent |
| Input | `yi2` | Second independent input variable | model-dependent |
| Output | `yo` | Interpolated output value | model-dependent |
| Parameter | `matrix_K` | Stored lookup matrix or surface data | data object |

## How to use it

- Use this block when the modeled relation depends on two inputs and is best described by tabulated data.
