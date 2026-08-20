# Hz -> p.u.

<!-- veragrid-block-introduction:start -->
**Hz -> p.u.** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

Hz -> p.u. converts frequency in hertz to per-unit frequency using the configured base frequency. Use it when control logic expects normalized frequency.

$$
fpu = \frac{Freq}{freqbase}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Freq` | Frequency input | Hz |
| Output | `fpu` | Frequency in per unit | p.u. |
| Parameter | `freqbase` | Base frequency | Hz |
