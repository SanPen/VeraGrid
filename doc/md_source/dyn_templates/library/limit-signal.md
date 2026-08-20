# Limit (signal) [signal: y_max/y_min]

<!-- veragrid-block-introduction:start -->
**Limit (signal) [signal: y_max/y_min]** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Limit variant reads both bounds as signals without extra tolerance parameters. Use it when another part of the model computes the active operating window.

$$
yo = \min(\max(yi, y_{min}), y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Input | `y_max` | Runtime upper bound | same as `yi` |
| Input | `y_min` | Runtime lower bound | same as `yi` |
| Output | `yo` | Limited output | same as `yi` |
