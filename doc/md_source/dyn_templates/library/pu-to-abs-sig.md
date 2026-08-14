# p.u. -> abs (sig)

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
