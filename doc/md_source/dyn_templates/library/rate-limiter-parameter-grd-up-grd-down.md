# Rate limiter (parameter) [param: grd_up/grd_down]

This Rate limiter variant applies separate configured rise and fall limits. Use it when the signal can move faster in one direction than the other.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `grd_up` | Allowed upward rate of change | output units/s |
| Parameter | `grd_down` | Allowed downward rate of change | output units/s |
