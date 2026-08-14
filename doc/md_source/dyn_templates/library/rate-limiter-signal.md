# Rate limiter (signal)

This Rate limiter variant reads the rise and fall limits from signals. Use it when the allowed ramp rates must change during simulation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Input | `grd_up` | Runtime upward rate limit | output units/s |
| Input | `grd_down` | Runtime downward rate limit | output units/s |
| Output | `yo` | Rate-limited output | model-dependent |
