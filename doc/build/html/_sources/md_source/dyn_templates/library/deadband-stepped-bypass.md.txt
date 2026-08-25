# Deadband stepped (bypass)

<!-- veragrid-block-introduction:start -->
**Deadband stepped (bypass)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Deadband stepped (bypass) suppresses small variations and then resumes with stepped behavior once the input leaves the dead zone. Use it when threshold crossings should create a clearer discrete response.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Stepped deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
