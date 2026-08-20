# PI droop

<!-- veragrid-block-introduction:start -->
**PI droop** implements a feedback-control relation. Such blocks turn tracking error into an actuator command and may contain proportional, integral, filtering, or dynamic compensation terms. Their gains set closed-loop speed and damping rather than changing the underlying network physics directly.

## Typical use

- Use it inside voltage, current, power, speed, excitation, or governor control loops.
- Coordinate gains, limits, and time constants with the actuator and plant bandwidth.
<!-- veragrid-block-introduction:end -->

PI droop generates an output from a condition signal with pick-up and drop-out timing supplied as inputs.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Activation condition | boolean or logical flag |
| Input | `Tpick` | Pick-up delay input | s |
| Input | `Tdrop` | Drop-out delay input | s |
| Output | `yo` | Droop controller output | model-dependent |
