# Time delay

<!-- veragrid-block-introduction:start -->
**Time delay** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Stores accepted source samples and exposes the value corresponding to an earlier simulation time.

## Configuration

- **Output mode**: retained delayed result.
- **Source expression**: signal sampled into the history.
- **Delay**: symbolic delay in seconds.

## Runtime behavior

A non-positive delay passes the current sample through. Positive delays use the available accepted-step history, so accuracy depends on the simulation step and event boundaries. Delays should remain non-negative during operation.
