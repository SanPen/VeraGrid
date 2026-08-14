# Limit (signal) [signal: y_max/y_min; param: eps]

This Limit variant reads its upper and lower bounds as signals and uses a fixed epsilon tolerance. Use it when the allowable range changes during simulation.

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
| Parameter | `eps` | Small tolerance around the limit transition | same as `yi` |
