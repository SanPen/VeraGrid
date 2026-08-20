# Limit (3 parameter inputs)] (complex with prio)

<!-- veragrid-block-introduction:start -->
**Limit (3 parameter inputs)] (complex with prio)** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

This complex Limit variant constrains a `d`/`q` vector with axis priority but without separate minimum parameters. Use it when positive capability limits and axis precedence are the main concern.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `d` | Direct-axis input | model-dependent |
| Input | `q` | Quadrature-axis input | model-dependent |
| Input | `PRIORITISE_AXIS` | Axis-priority selector | selector or boolean |
| Output | `yo_d` | Limited direct-axis output | same as `d` |
| Output | `yo_q` | Limited quadrature-axis output | same as `q` |
| Parameter | `D_MAX` | Maximum direct-axis value | same as `d` |
| Parameter | `Q_MAX` | Maximum quadrature-axis value | same as `q` |
| Parameter | `MAG_MAX` | Maximum vector magnitude | same as vector magnitude |
