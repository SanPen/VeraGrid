# Hard saturation

<!-- veragrid-block-introduction:start -->
**Hard saturation** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

## Purpose

Clamps an input expression between two evaluated limits and writes the result to a retained mode.

## Configuration

- **Output mode**: retained saturated result.
- **Input expression**: requested value.
- **Minimum** and **Maximum**: symbolic bounds.

## Runtime behavior

All three expressions are evaluated at each accepted update. If the bounds are reversed, the implementation normalizes their order before clamping. The operation is procedural and therefore does not add an algebraic residual.
