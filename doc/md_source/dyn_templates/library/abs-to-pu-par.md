# abs -> p.u. (par)

abs -> p.u. (par) converts an absolute-value signal to per unit using a configured base parameter. Use it when the normalization base is fixed for the block instance.

$$
yo = \frac{yi}{base}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Absolute input value | model-dependent |
| Output | `yo` | Per-unit output | p.u. |
| Parameter | `base` | Base value for normalization | same as `yi` |
