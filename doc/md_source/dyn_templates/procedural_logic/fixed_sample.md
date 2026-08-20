# Fixed sample

<!-- veragrid-block-introduction:start -->
**Fixed sample** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Evaluates a condition once, on the first accepted runtime update, and stores the Boolean result (`0.0` or `1.0`) in a retained mode. Later updates leave that value unchanged.

## Configuration

- **Output mode**: retained mode receiving the sampled Boolean value.
- **Condition**: symbolic expression or comparison evaluated once.

## Runtime behavior

This is useful for selecting an operating branch from initial conditions. The output mode must exist and must not be written by another procedural entry. Put this entry before logic that consumes its output during the same boundary update.
