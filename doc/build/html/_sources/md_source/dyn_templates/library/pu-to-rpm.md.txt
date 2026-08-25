# p.u. -> rpm

<!-- veragrid-block-introduction:start -->
**p.u. -> rpm** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

p.u. -> rpm converts per-unit speed to revolutions per minute using the configured electrical base values. Use it when a normalized speed signal must be shown or reused in mechanical units.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `speed` | Per-unit speed input | p.u. |
| Output | `n` | Rotational speed output | rpm |
| Parameter | `Zp` | Pole-pair or pole-count-related parameter | model-dependent |
| Parameter | `freqbase` | Base frequency | Hz |
