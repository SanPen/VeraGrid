# p.u. -> Hz

p.u. -> Hz converts per-unit frequency back to hertz using the configured base frequency. Use it when normalized frequency must be reported in physical units.

$$
Freq = fpu \cdot freqbase
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `fpu` | Per-unit frequency input | p.u. |
| Output | `Freq` | Frequency output | Hz |
| Parameter | `freqbase` | Base frequency | Hz |
