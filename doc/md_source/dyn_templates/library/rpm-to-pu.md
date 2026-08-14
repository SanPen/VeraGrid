# rpm -> p.u.

rpm -> p.u. converts revolutions per minute to per-unit speed using the configured electrical base values. Use it when a measured shaft speed must feed normalized control logic.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `n` | Rotational speed input | rpm |
| Output | `speed` | Per-unit speed output | p.u. |
| Parameter | `Zp` | Pole-pair or pole-count-related parameter | model-dependent |
| Parameter | `freqbase` | Base frequency | Hz |
