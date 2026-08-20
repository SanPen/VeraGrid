# Delayed threshold latch

<!-- veragrid-block-introduction:start -->
**Delayed threshold latch** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Trips a retained mode after a monitored DAE variable stays beyond a fixed threshold for a specified time.

## Configuration

- **Monitored variable**: DAE signal being compared.
- **Output mode**: retained trip state.
- **Threshold**: numeric comparison threshold.
- **Delay**: non-negative trip delay.
- **Reset delay**: optional non-negative time after which the latch resets.

## Runtime behavior

The latch requests event boundaries at the scheduled trip or reset times. It is suited to protection and fault-control logic where a threshold must persist before action.
