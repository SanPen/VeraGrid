# Nm -> p.u.

<!-- veragrid-block-introduction:start -->
**Nm -> p.u.** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

Nm -> p.u. converts torque in newton-meters to per-unit torque using the configured base values. Use it when mechanical torque must be normalized for control blocks.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `M` | Torque input | Nm |
| Output | `m` | Torque in per unit | p.u. |
| Parameter | `freqbase` | Base frequency used by the conversion | Hz |
| Parameter | `Zp` | Pole-pair or pole-count-related parameter | model-dependent |
| Parameter | `Pel_base` | Electrical power base | W or model-dependent |
