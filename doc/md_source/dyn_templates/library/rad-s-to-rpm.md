# rad/s -> rpm

<!-- veragrid-block-introduction:start -->
**rad/s -> rpm** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

rad/s -> rpm converts angular speed from radians per second to revolutions per minute. Use it when a rotational speed signal must be shown in rpm.

$$
n = \omega \cdot \frac{60}{2\pi}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `omega` | Angular-speed input | rad/s |
| Output | `n` | Rotational speed output | rpm |
