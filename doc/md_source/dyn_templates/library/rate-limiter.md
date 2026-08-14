# Rate limiter

Rate limiter limits how quickly the output can increase. Use it to smooth abrupt upward changes in a command or reference.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `grd_up` | Allowed upward rate of change | output units/s |
