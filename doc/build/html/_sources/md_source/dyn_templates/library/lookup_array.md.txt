# Lookup array

<!-- veragrid-block-introduction:start -->
**Lookup array** evaluates a tabulated characteristic instead of assuming one closed-form equation. Interpolation maps measured or commanded inputs to empirical outputs such as efficiency, saturation, capability, or control schedules while preserving the supplied breakpoints.

## Typical use

- Use it when manufacturer data or a calibrated characteristic is available as points or a matrix.
- Keep breakpoints ordered and decide deliberately whether values outside the table clip or extrapolate.
<!-- veragrid-block-introduction:end -->

### Purpose

This block approximates one nonlinear relation from one one-dimensional stored array.

### Behavior

- Receives one scalar input.
- Interpolates within one stored array.
- Outputs the corresponding approximated value.

### Characteristics

- Useful for tabulated nonlinear functions.
- Available in linear, spline, clipped, unclipped, fixed-size, variable-size, and object-array variants.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent input variable for the lookup | model-dependent |
| Output | `yo` | Interpolated output value | model-dependent |
| Parameter | `array_K` | Stored lookup array in direct-array variants | data object |
| Parameter | `oarray_K` | Stored lookup object in object-array variants | data object |
| Parameter | `vClip` | Clipping control parameter in variants that support clipping | 0/1 or boolean |

## How to use it

- Use this block when a nonlinear relation is easier to define by one table than by one closed-form expression.
