# Limit (parameter) (complex)

<!-- veragrid-block-introduction:start -->
**Limit (parameter) (complex)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This complex Limit variant constrains the `d` and `q` components so the vector magnitude stays within a configured maximum. Use it for dq-axis commands that must remain inside a circular capability boundary.

$$
\sqrt{yo_d^2 + yo_q^2} \le MAG_{MAX}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `d` | Direct-axis input | model-dependent |
| Input | `q` | Quadrature-axis input | model-dependent |
| Output | `yo_d` | Limited direct-axis output | same as `d` |
| Output | `yo_q` | Limited quadrature-axis output | same as `q` |
| Parameter | `MAG_MAX` | Maximum allowed vector magnitude | same as vector magnitude |
