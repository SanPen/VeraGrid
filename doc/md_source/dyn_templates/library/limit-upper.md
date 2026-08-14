# Limit upper

Limit upper only enforces a maximum value. Use it when the signal must never exceed a configured ceiling.

$$
yo = \min(yi, y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Upper-limited output | same as `yi` |
| Parameter | `y_max` | Maximum allowed value | same as `yi` |
