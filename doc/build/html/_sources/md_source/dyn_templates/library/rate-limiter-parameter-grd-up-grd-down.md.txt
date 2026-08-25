# Rate limiter (parameter) [param: grd_up/grd_down]

<!-- veragrid-block-introduction:start -->
**Rate limiter (parameter) [param: grd_up/grd_down]** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Rate limiter variant applies separate configured rise and fall limits. Use it when the signal can move faster in one direction than the other.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `grd_up` | Allowed upward rate of change | output units/s |
| Parameter | `grd_down` | Allowed downward rate of change | output units/s |
