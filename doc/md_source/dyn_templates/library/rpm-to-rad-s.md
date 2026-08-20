# rpm -> rad/s

<!-- veragrid-block-introduction:start -->
**rpm -> rad/s** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

rpm -> rad/s converts revolutions per minute to angular speed in radians per second. Use it when mechanical-speed data must drive blocks that work in SI angular units.

$$
\omega = n \cdot \frac{2\pi}{60}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `n` | Rotational speed input | rpm |
| Output | `omega` | Angular-speed output | rad/s |
