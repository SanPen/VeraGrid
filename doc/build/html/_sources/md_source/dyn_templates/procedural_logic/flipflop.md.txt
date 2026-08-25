# Flip-flop

<!-- veragrid-block-introduction:start -->
**Flip-flop** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Implements a retained binary set/reset latch.

## Configuration

- **Output mode**: retained `0.0` or `1.0` latch state.
- **Set condition**: drives the state high.
- **Reset condition**: drives the state low.

## Runtime behavior

At initialization, Set determines the initial state. During operation, Set-only activates and Reset-only clears. When both conditions have the same truth value, the previous state is retained. Use explicit, mutually understandable conditions to avoid ambiguous control intent.
