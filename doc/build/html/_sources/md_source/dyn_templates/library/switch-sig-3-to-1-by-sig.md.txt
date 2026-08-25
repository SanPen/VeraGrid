# Switch sig 3->1 by sig

<!-- veragrid-block-introduction:start -->
**Switch sig 3->1 by sig** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch chooses one of three input signals using a runtime selector signal. Use it when one signal path must be selected from three live candidates.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `yi3` | Third candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | model-dependent |
| Output | `yo` | Selected output | model-dependent |
