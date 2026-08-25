# Limit (signal + parameter input)

<!-- veragrid-block-introduction:start -->
**Limit (signal + parameter input)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Limit variant combines runtime limit inputs with stored fallback bounds. Use it when the active limit signals may vary but parameter values still define the configured range.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Input | `yi_max` | Runtime upper-bound input | same as `yi` |
| Input | `yi_min` | Runtime lower-bound input | same as `yi` |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `y_max` | Configured upper limit | same as `yi` |
| Parameter | `y_min` | Configured lower limit | same as `yi` |
