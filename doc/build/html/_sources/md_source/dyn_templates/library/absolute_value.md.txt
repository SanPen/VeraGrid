# Absolute value

<!-- veragrid-block-introduction:start -->
**Absolute value** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

The Absolute value block returns the non-negative magnitude of its scalar
input. It is commonly used before limits, comparisons, and magnitude-based
protection logic.

## Characteristic equation

$$
y = |u|
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `u` | Signed input signal | model-dependent |
| Output | `y` | Absolute magnitude | same as `u` |

The operation is algebraic and is non-differentiable only at `u = 0`.
