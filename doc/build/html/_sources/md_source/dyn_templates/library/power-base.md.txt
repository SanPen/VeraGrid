# Power base

<!-- veragrid-block-introduction:start -->
**Power base** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

Power base converts power-related inputs into an electrical power output using the configured nominal power. Use it when signals are expressed around a machine or plant base.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `pg` | Power-related input | model-dependent |
| Input | `sgnn` | Sign or scaling input | model-dependent |
| Input | `cosn` | Power-factor-related input | model-dependent |
| Output | `pelec` | Electrical power output | power |
| Parameter | `PN` | Nominal power base | power |
