# Switch sig 2->1 by sig (bool)

<!-- veragrid-block-introduction:start -->
**Switch sig 2->1 by sig (bool)** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch chooses between two input signals using a boolean runtime selector. Use it when the branch should react directly to a live logical signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `sw` | Boolean runtime selector | boolean or 0/1 |
| Output | `yo` | Selected output | model-dependent |
