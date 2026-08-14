# Limit (signal) [signal: y_max/y_min]

This Limit variant reads both bounds as signals without extra tolerance parameters. Use it when another part of the model computes the active operating window.

$$
yo = \min(\max(yi, y_{min}), y_{max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Input | `y_max` | Runtime upper bound | same as `yi` |
| Input | `y_min` | Runtime lower bound | same as `yi` |
| Output | `yo` | Limited output | same as `yi` |
