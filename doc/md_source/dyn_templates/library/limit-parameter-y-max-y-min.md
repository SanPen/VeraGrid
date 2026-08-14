# Limit (parameter) [param: y_max/y_min]

This Limit variant clips the input between fixed lower and upper bounds without a separate epsilon parameter. Use it for straightforward parameter-based saturation.

$$
yo = \min(\max(yi, y_{min}), y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `y_max` | Upper limit | same as `yi` |
| Parameter | `y_min` | Lower limit | same as `yi` |
