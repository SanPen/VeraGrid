# rpm -> p.u.

<!-- veragrid-block-introduction:start -->
**rpm -> p.u.** converts an engineering quantity between unit systems or reference bases. These blocks do not add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values.

## Typical use

- Use it at interfaces where a model and its data source use different units or bases.
- Verify the nominal base quantity and angular-frequency convention used by both sides.
<!-- veragrid-block-introduction:end -->

rpm -> p.u. converts revolutions per minute to per-unit speed using the configured electrical base values. Use it when a measured shaft speed must feed normalized control logic.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `n` | Rotational speed input | rpm |
| Output | `speed` | Per-unit speed output | p.u. |
| Parameter | `Zp` | Pole-pair or pole-count-related parameter | model-dependent |
| Parameter | `freqbase` | Base frequency | Hz |
