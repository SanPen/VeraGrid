# Backlash

<!-- veragrid-block-introduction:start -->
**Backlash** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model cannot represent. The active branch can change when a threshold is crossed.

## Typical use

- Use it to model physical saturation, insensitive regions, slew limits, or bounded commands.
- Choose thresholds in consistent units and inspect behavior exactly at switching boundaries.
<!-- veragrid-block-introduction:end -->

Backlash models a mechanical-style play zone where small reversals do not immediately change the output. Use it when gear slack or hysteretic motion should be represented.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after backlash behavior | same as `yi` |
| State | `Backlash__x` | Internal stored position for the backlash element | same as `yi` |
| Parameter | `db` | Backlash width | same as `yi` |
