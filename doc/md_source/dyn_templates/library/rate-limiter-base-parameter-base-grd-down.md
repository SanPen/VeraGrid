# Rate limiter base (parameter) [param: base/grd_down]

This Rate limiter base variant uses fixed base and downward ramp settings. Use it when the falling rate must be constrained relative to a configured base.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `base` | Base scaling value | model-dependent |
| Parameter | `grd_down` | Allowed downward rate of change relative to the base | per second or model-dependent |
