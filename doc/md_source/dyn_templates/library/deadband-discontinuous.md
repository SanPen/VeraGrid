# Deadband discontinuous

<!-- veragrid-block-introduction:start -->
**Deadband discontinuous** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Deadband discontinuous creates a hard transition at the deadband edge. Use it when you need explicit on/off style deadband behavior instead of a smooth re-entry.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after discontinuous deadband processing | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
