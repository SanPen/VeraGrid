# Timer (reset)

<!-- veragrid-block-introduction:start -->
**Timer (reset)** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Timer (reset) produces a timer output that restarts when the reset input is active. Use it for elapsed-time logic that must be cleared by an external reset signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `rst` | Reset signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Timer output | s or model-dependent |
