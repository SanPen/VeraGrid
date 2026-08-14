# lim const

`lim const` limits an input using fixed parameter bounds. Use it when the permitted range is known when you configure the block.

$$
yo = \min(\max(yi, y_{min}), y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `y_max` | Upper bound | same as `yi` |
| Parameter | `y_min` | Lower bound | same as `yi` |
