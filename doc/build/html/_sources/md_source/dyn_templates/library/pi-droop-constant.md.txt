# PI droop (constant)

<!-- veragrid-block-introduction:start -->
**PI droop (constant)** implements a feedback-control relation. Such blocks turn tracking error into an actuator command and may contain proportional, integral, filtering, or dynamic compensation terms. Their gains set closed-loop speed and damping rather than changing the underlying network physics directly.

## Typical use

- Use it inside voltage, current, power, speed, excitation, or governor control loops.
- Coordinate gains, limits, and time constants with the actuator and plant bandwidth.
<!-- veragrid-block-introduction:end -->

`PI droop (constant)` provides the same timed droop behavior as `PI droop`, but uses fixed pick-up and drop-out parameters.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Activation condition | boolean or logical flag |
| Output | `yo` | Droop controller output | model-dependent |
| Parameter | `Tpick` | Pick-up delay | s |
| Parameter | `Tdrop` | Drop-out delay | s |
