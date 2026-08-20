# Switch par 2->1 by sig

<!-- veragrid-block-introduction:start -->
**Switch par 2->1 by sig** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch chooses between two configured parameter values using a runtime selector signal. Use it when a live condition should choose which constant reaches the output.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `K1` | First configured candidate value | model-dependent |
| Parameter | `K2` | Second configured candidate value | model-dependent |
