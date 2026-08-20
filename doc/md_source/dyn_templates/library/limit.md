# Limit

<!-- veragrid-block-introduction:start -->
**Limit** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Limit clips an input to a configured upper range with a small tolerance parameter. Use it when you need a simple saturating ceiling behavior from a single input.

$$
yo \le y_{max}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `eps` | Small tolerance used around the limit | same as `yi` |
| Parameter | `y_max` | Upper limit | same as `yi` |
