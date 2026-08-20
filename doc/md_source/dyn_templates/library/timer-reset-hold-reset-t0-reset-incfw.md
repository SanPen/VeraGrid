# Timer (reset/hold reset/t0) (reset) incfw

<!-- veragrid-block-introduction:start -->
**Timer (reset/hold reset/t0) (reset) incfw** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

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
