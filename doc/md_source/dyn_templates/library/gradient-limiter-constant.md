# Gradient limiter (constant)

<!-- veragrid-block-introduction:start -->
**Gradient limiter (constant)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Gradient limiter (constant) restricts how fast the output is allowed to rise or fall. Use it to prevent sudden ramps from propagating downstream.

$$
gradmin \le \frac{d yo}{dt} \le gradmax
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `gradmax` | Maximum upward gradient | output units/s |
| Parameter | `gradmin` | Maximum downward gradient | output units/s |
