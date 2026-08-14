# Rate limiter base (parameter) [param: base/grd]

This Rate limiter base variant uses one symmetric ramp setting scaled by a base value. Use it when rising and falling should be limited equally.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `base` | Base scaling value | model-dependent |
| Parameter | `grd` | Symmetric allowed rate of change | per second or model-dependent |
