# Switch par 1->1 by par

<!-- veragrid-block-introduction:start -->
**Switch par 1->1 by par** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

This switch passes one input through under parameter-controlled switching logic. Use it when switching behavior is configured entirely from block parameters.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Switched output | model-dependent |
| Parameter | `Enable` | Enable setting for the switch | boolean, 0/1, or model-dependent |
| Parameter | `p` | Associated configured value used by the block | model-dependent |
