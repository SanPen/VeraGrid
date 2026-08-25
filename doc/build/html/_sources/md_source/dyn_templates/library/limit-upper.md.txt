# Limit upper

<!-- veragrid-block-introduction:start -->
**Limit upper** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Limit upper only enforces a maximum value. Use it when the signal must never exceed a configured ceiling.

$$
yo = \min(yi, y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Upper-limited output | same as `yi` |
| Parameter | `y_max` | Maximum allowed value | same as `yi` |
