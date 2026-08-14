# p.u. -> rpm

p.u. -> rpm converts per-unit speed to revolutions per minute using the configured electrical base values. Use it when a normalized speed signal must be shown or reused in mechanical units.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `speed` | Per-unit speed input | p.u. |
| Output | `n` | Rotational speed output | rpm |
| Parameter | `Zp` | Pole-pair or pole-count-related parameter | model-dependent |
| Parameter | `freqbase` | Base frequency | Hz |
