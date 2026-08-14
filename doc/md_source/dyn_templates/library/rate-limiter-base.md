# Rate limiter base

Rate limiter base scales the rate limit from a configured base value. Use it when the permitted ramp should track a base quantity.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `base` | Base scaling value | model-dependent |
| Parameter | `grd_up` | Allowed upward rate of change relative to the base | per second or model-dependent |
