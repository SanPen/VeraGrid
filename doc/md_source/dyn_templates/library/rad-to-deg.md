# rad -> deg

<!-- veragrid-block-introduction:start -->
**rad -> deg** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

rad -> deg converts angles from radians to degrees. Use it when a downstream block or report expects degrees.

$$
yo = yi \cdot \frac{180}{\pi}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Angle input | rad |
| Output | `yo` | Angle output | deg |
