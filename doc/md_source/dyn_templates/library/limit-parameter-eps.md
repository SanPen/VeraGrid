# Limit (parameter) eps

<!-- veragrid-block-introduction:start -->
**Limit (parameter) eps** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Limit variant uses a stored limit definition together with an epsilon tolerance. Use it when the bound data is packaged as one parameter object or value set.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `eps` | Small tolerance around the limit transition | same as `yi` |
| Parameter | `y_lim` | Stored limit definition | same as `yi` |
