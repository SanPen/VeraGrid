# Rate limiter (parameter) [param: grd]

This Rate limiter variant uses one symmetric configured ramp limit. Use it when the same rate cap should apply in both directions.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `grd` | Symmetric allowed rate of change | output units/s |
