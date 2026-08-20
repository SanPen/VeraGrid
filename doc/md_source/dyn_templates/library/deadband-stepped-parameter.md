# Deadband stepped (parameter)

<!-- veragrid-block-introduction:start -->
**Deadband stepped (parameter)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Deadband stepped (parameter) uses configured bounds and resumes with step-like behavior outside the dead region. Use it when the output should change in a more quantized way at the threshold.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Stepped deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
| Parameter | `y_max` | Upper output or active-region bound | same as `yi` |
| Parameter | `y_min` | Lower output or active-region bound | same as `yi` |
