# Limit (parameter) [param: eps/y_max/y_min]

This Limit variant clips the input between fixed lower and upper bounds and includes an epsilon tolerance. Use it when both limits are known at configuration time.

$$
yo = \min(\max(yi, y_{min}), y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `eps` | Small tolerance around the limit transition | same as `yi` |
| Parameter | `y_max` | Upper limit | same as `yi` |
| Parameter | `y_min` | Lower limit | same as `yi` |
