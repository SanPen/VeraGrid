# Signal Pair

<!-- veragrid-block-introduction:start -->
**Signal Pair** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Named signal routing pair used to connect non-local editor signals.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `from` | Named source signal | model-dependent |
| Output | `goto` | Routed destination signal | model-dependent |
| Parameter | `tag` | Shared routing identifier | text |
