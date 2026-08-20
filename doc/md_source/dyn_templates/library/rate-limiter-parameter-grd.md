# Rate limiter (parameter) [param: grd]

<!-- veragrid-block-introduction:start -->
**Rate limiter (parameter) [param: grd]** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Rate limiter variant uses one symmetric configured ramp limit. Use it when the same rate cap should apply in both directions.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `grd` | Symmetric allowed rate of change | output units/s |
