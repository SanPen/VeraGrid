# yi1 greater than yi2 eps

`yi1 greater than yi2 eps` outputs true when the first signal exceeds the second by more than `eps`.

$$
yo = (yi1 > yi2 + eps)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First signal | model-dependent |
| Input | `yi2` | Second signal | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
| Parameter | `eps` | Comparison margin | model-dependent |
