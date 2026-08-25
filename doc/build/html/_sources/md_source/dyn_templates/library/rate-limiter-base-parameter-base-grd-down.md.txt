# Rate limiter base (parameter) [param: base/grd_down]

<!-- veragrid-block-introduction:start -->
**Rate limiter base (parameter) [param: base/grd_down]** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Rate limiter base variant uses fixed base and downward ramp settings. Use it when the falling rate must be constrained relative to a configured base.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `base` | Base scaling value | model-dependent |
| Parameter | `grd_down` | Allowed downward rate of change relative to the base | per second or model-dependent |
