# Limit lower (parameter)

Limit lower (parameter) only enforces a minimum value. Use it when the signal must never fall below a configured floor.

$$
yo = \max(yi, y_{min})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Lower-limited output | same as `yi` |
| Parameter | `y_min` | Minimum allowed value | same as `yi` |
