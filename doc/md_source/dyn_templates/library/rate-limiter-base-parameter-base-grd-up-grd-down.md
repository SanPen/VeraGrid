# Rate limiter base (parameter) [param: base/grd_up/grd_down]

This Rate limiter base variant uses fixed base, upward ramp, and downward ramp settings. Use it when rise and fall limits differ and both should be scaled from the same base.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `base` | Base scaling value | model-dependent |
| Parameter | `grd_up` | Allowed upward rate of change relative to the base | per second or model-dependent |
| Parameter | `grd_down` | Allowed downward rate of change relative to the base | per second or model-dependent |
