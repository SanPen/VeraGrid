# Hz -> p.u.

Hz -> p.u. converts frequency in hertz to per-unit frequency using the configured base frequency. Use it when control logic expects normalized frequency.

$$
fpu = \frac{Freq}{freqbase}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Freq` | Frequency input | Hz |
| Output | `fpu` | Frequency in per unit | p.u. |
| Parameter | `freqbase` | Base frequency | Hz |
