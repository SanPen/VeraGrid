# Limit lower (parameter)

<!-- veragrid-block-introduction:start -->
**Limit lower (parameter)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Limit lower (parameter) only enforces a minimum value. Use it when the signal must never fall below a configured floor.

$$
yo = \max(yi, y_{min})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Lower-limited output | same as `yi` |
| Parameter | `y_min` | Minimum allowed value | same as `yi` |
