# Timer (reset/hold reset/t0) (reset) incfw

This timer variant resets from `rst`, accepts a `t0` time input, and stores internal timing state. Use it when a timer must restart from a supplied time reference and preserve increment-forward timing behavior.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `rst` | Reset signal | boolean, 0/1, or model-dependent |
| Input | `t0` | Start-time or reference-time input | s |
| Output | `yo` | Timer output | s or model-dependent |
| State | `Timer (reset/hold reset/t0) _reset_incfw__x` | Internal timer state | s or model-dependent |
| Parameter | `flank` | Edge-selection setting for reset handling | selector or boolean |
| Parameter | `t_start_delay` | Delay before the timer starts counting | s |
