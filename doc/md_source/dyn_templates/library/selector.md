# Selector

<!-- veragrid-block-introduction:start -->
**Selector** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Selector outputs `y_true` when the condition is active and `y_false` otherwise. Use it for simple runtime branching between two signal paths.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Input | `y_true` | Output value used when the condition is true | model-dependent |
| Input | `y_false` | Output value used when the condition is false | model-dependent |
| Output | `yo` | Selected output | model-dependent |
