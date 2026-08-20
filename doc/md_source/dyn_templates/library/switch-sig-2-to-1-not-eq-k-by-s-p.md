# Switch sig 2->1 (NOT EQ K) by s/p

<!-- veragrid-block-introduction:start -->
**Switch sig 2->1 (NOT EQ K) by s/p** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch chooses between two input signals based on whether the selector signal differs from a configured value `K`. Use it when the branch condition is an explicit not-equal comparison.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `K` | Comparison value used by the switch | model-dependent |
