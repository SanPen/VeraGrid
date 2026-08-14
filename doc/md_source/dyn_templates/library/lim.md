# lim

`lim` limits an input using runtime lower and upper bound signals. Use it when the allowed range must come from other blocks instead of fixed parameters.

$$
yo = \min(\max(yi, y_{min}), y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Input | `y_min` | Runtime lower bound | same as `yi` |
| Input | `y_max` | Runtime upper bound | same as `yi` |
| Output | `yo` | Limited output | same as `yi` |
