# Gradient limiter

<!-- veragrid-block-introduction:start -->
**Gradient limiter** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

## Purpose

Limits how fast a retained output can move toward a requested source value.

## Configuration

- **Output mode**: retained rate-limited result.
- **Source expression**: requested value.
- **Lower rate** and **Upper rate**: permitted slopes per second.

## Runtime behavior

The first accepted update initializes the held output from the source. Each later update restricts the change using elapsed accepted time. Reversed lower and upper bounds are normalized automatically.
