# Rate limiter base

<!-- veragrid-block-introduction:start -->
**Rate limiter base** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Rate limiter base scales the rate limit from a configured base value. Use it when the permitted ramp should track a base quantity.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `base` | Base scaling value | model-dependent |
| Parameter | `grd_up` | Allowed upward rate of change relative to the base | per second or model-dependent |
