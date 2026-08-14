# abs -> p.u. (sig)

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
