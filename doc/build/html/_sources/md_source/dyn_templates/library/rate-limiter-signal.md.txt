# Rate limiter (signal)

<!-- veragrid-block-introduction:start -->
**Rate limiter (signal)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This Rate limiter variant reads the rise and fall limits from signals. Use it when the allowed ramp rates must change during simulation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Input | `grd_up` | Runtime upward rate limit | output units/s |
| Input | `grd_down` | Runtime downward rate limit | output units/s |
| Output | `yo` | Rate-limited output | model-dependent |
