# p.u. -> abs (par)

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
