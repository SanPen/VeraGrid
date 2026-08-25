# Set if condition (constant)

<!-- veragrid-block-introduction:start -->
**Set if condition (constant)** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Set if condition (constant) chooses between two configured constants using a runtime condition. Use it when the decision changes at runtime but the candidate outputs are fixed.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected constant output | model-dependent |
| Parameter | `K_true` | Constant used when the condition is true | model-dependent |
| Parameter | `K_false` | Constant used when the condition is false | model-dependent |
