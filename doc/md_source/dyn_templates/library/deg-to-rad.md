# deg -> rad

<!-- veragrid-block-introduction:start -->
**deg -> rad** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

deg -> rad converts angles from degrees to radians. Use it when a downstream block expects angles in radians.

$$
yo = yi \cdot \frac{\pi}{180}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Angle input | deg |
| Output | `yo` | Angle output | rad |
