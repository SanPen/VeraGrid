# Lookup matrix

<!-- veragrid-block-introduction:start -->
**Lookup matrix** evaluates a tabulated characteristic instead of assuming one closed-form equation. Interpolation maps measured or commanded inputs to empirical outputs such as efficiency, saturation, capability, or control schedules while preserving the supplied breakpoints.

## Typical use

- Use it when manufacturer data or a calibrated characteristic is available as points or a matrix.
- Keep breakpoints ordered and decide deliberately whether values outside the table clip or extrapolate.
<!-- veragrid-block-introduction:end -->

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
