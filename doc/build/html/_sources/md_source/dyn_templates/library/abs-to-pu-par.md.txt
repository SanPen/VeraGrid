# abs -> p.u. (par)

<!-- veragrid-block-introduction:start -->
**abs -> p.u. (par)** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

abs -> p.u. (par) converts an absolute-value signal to per unit using a configured base parameter. Use it when the normalization base is fixed for the block instance.

$$
yo = \frac{yi}{base}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Absolute input value | model-dependent |
| Output | `yo` | Per-unit output | p.u. |
| Parameter | `base` | Base value for normalization | same as `yi` |
