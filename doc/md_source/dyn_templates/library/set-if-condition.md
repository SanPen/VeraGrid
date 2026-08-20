# Set if condition

<!-- veragrid-block-introduction:start -->
**Set if condition** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Set if condition selects between two input values using a runtime condition. Use it when you want explicit conditional assignment behavior in the signal path.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Input | `y_true` | Value used when the condition is true | model-dependent |
| Input | `y_false` | Value used when the condition is false | model-dependent |
| Output | `yo` | Selected output | model-dependent |
