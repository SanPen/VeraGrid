# Pickup/dropoff relay

<!-- veragrid-block-introduction:start -->
**Pickup/dropoff relay** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Creates a binary relay with independent activation and deactivation delays.

## Configuration

- **Output mode**: retained relay state.
- **Condition**: requested relay state.
- **Pickup delay**: time the condition must remain true before activation.
- **Dropoff delay**: time the condition must remain false before deactivation.

## Runtime behavior

The logic schedules exact pending relay boundaries when possible. If the condition reverses before a delay completes, the pending transition is cancelled. Delay expressions are evaluated at runtime and should remain non-negative.
