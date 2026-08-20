# abs -> p.u. (sig)

<!-- veragrid-block-introduction:start -->
**abs -> p.u. (sig)** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

abs -> p.u. (sig) converts an absolute-value signal to per unit using a runtime base input. Use it when the normalization base must change during simulation.

$$
yo = \frac{yi}{base}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Absolute input value | model-dependent |
| Input | `base` | Runtime base value | same as `yi` |
| Output | `yo` | Per-unit output | p.u. |
