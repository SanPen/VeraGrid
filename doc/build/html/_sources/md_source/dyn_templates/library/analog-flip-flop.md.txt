# Analog flip-flop

<!-- veragrid-block-introduction:start -->
**Analog flip-flop** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Analog flip-flop stores a logical output state, driven by an analog trigger input together with explicit set and reset signals.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Analog trigger input | model-dependent |
| Input | `set` | Set command | boolean or logical flag |
| Input | `rst` | Reset command | boolean or logical flag |
| Output | `yo` | Latched output state | model-dependent |
