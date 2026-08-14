# Rate limiter (parameter) [param: grd_down]

This Rate limiter variant applies a fixed downward ramp limit. Use it when decreasing too quickly would be problematic.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `grd_down` | Allowed downward rate of change | output units/s |
