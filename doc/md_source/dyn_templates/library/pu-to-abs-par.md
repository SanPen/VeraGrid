# p.u. -> abs (par)

<!-- veragrid-block-introduction:start -->
**p.u. -> abs (par)** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

p.u. -> abs (par) converts a per-unit signal to an absolute-value signal using a configured base parameter. Use it when the output scaling is fixed for the block instance.

$$
yo = yi \cdot base
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Per-unit input | p.u. |
| Output | `yo` | Absolute output | model-dependent |
| Parameter | `base` | Base value for conversion | same as `yo` |
