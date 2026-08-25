# Switch par 1->2 by sig

<!-- veragrid-block-introduction:start -->
**Switch par 1->2 by sig** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch routes one configured parameter value to one of two outputs using a runtime selector signal. Use it when a live signal decides where a configured quantity goes.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
| Parameter | `K` | Configured value being routed | model-dependent |
