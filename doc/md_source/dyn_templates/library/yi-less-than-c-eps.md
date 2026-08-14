# yi less than C eps

`yi less than C eps` compares the input against a constant with an epsilon margin on the low side.

$$
yo = (yi < C - eps)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal being compared | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
| Parameter | `C` | Constant threshold | model-dependent |
| Parameter | `eps` | Comparison margin | model-dependent |
