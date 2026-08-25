# Switch sig 1->1 by sig

<!-- veragrid-block-introduction:start -->
**Switch sig 1->1 by sig** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch passes one signal through under runtime signal-based switching logic. Use it when a live enable signal controls whether the path is active.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Input | `Enable` | Runtime enable signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Switched output | model-dependent |
| Parameter | `p` | Configured value used by the switch logic | model-dependent |
