# Switch sig 1->2 by par (bool)

<!-- veragrid-block-introduction:start -->
**Switch sig 1->2 by par (bool)** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch sends one input signal to one of two outputs using a boolean parameter. Use it when the routing choice is fixed by configuration.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal to route | model-dependent |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
| Parameter | `sw` | Boolean selector for the destination | boolean or 0/1 |
