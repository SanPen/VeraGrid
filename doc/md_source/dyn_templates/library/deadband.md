# Deadband

<!-- veragrid-block-introduction:start -->
**Deadband** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Deadband suppresses small input changes around the center region. Use it to prevent noise or tiny errors from triggering downstream action.

$$
yo = 0 \quad \text{inside the deadband region}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after deadband processing | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
