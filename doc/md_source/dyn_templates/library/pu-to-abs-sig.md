# p.u. -> abs (sig)

<!-- veragrid-block-introduction:start -->
**p.u. -> abs (sig)** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

p.u. -> abs (sig) converts a per-unit signal to an absolute-value signal using a runtime base input. Use it when the scaling base changes during simulation.

$$
yo = yi \cdot base
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Per-unit input | p.u. |
| Input | `base` | Runtime base value | same as `yo` |
| Output | `yo` | Absolute output | model-dependent |
