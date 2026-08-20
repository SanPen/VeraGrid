# Limit (parameter) (using min/max)

<!-- veragrid-block-introduction:start -->
**Limit (parameter) (using min/max)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Limit variant uses a single parameter carrying the limit range. Use it when your model stores the allowed minimum and maximum together.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `y_lim` | Stored min/max limit definition | same as `yi` |
