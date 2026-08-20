# Reset on rising edge

<!-- veragrid-block-introduction:start -->
**Reset on rising edge** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Detects a false-to-true transition and assigns a symbolic value to an explicitly mutable target.

## Configuration

- **Target**: state variable or runtime parameter to mutate.
- **Rising-edge condition**: Boolean expression used by the edge detector.
- **Reset value**: expression assigned on the edge.

## Runtime behavior

The first update establishes the previous condition and does not create a synthetic edge. Later rising edges mutate the target once. This type writes a target directly rather than producing a retained output mode, so use it only where an imperative reset is required.
