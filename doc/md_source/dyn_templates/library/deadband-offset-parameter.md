# Deadband offset (parameter)

<!-- veragrid-block-introduction:start -->
**Deadband offset (parameter)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Deadband offset (parameter) suppresses a central region and then resumes with an offset-style output using configured bounds. Use it when the output should not jump directly back to the raw input outside the deadband.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Offset deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
| Parameter | `y_max` | Upper output or active-region bound | same as `yi` |
| Parameter | `y_min` | Lower output or active-region bound | same as `yi` |
