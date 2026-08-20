# Deadband offset (bypass)

<!-- veragrid-block-introduction:start -->
**Deadband offset (bypass)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Deadband offset (bypass) holds a dead zone around the center and then passes the signal with offset-style behavior once active. Use it when you need both suppression near zero and continuity outside it.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Offset deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
