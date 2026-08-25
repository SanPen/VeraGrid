# p.u. -> Hz

<!-- veragrid-block-introduction:start -->
**p.u. -> Hz** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

p.u. -> Hz converts per-unit frequency back to hertz using the configured base frequency. Use it when normalized frequency must be reported in physical units.

$$
Freq = fpu \cdot freqbase
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `fpu` | Per-unit frequency input | p.u. |
| Output | `Freq` | Frequency output | Hz |
| Parameter | `freqbase` | Base frequency | Hz |
