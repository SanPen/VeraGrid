# Moving average

<!-- veragrid-block-introduction:start -->
**Moving average** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Computes a discrete average of accepted source samples over a delayed time window and stores it in a retained mode.

## Configuration

- **Output mode**: retained average.
- **Source expression**: sampled history input.
- **Delay**: offset between current time and the end of the window.
- **Window**: averaging duration.

## Runtime behavior

If the window is non-positive, the logic returns the latest historical value at the delayed time. Otherwise it averages samples inside the window. This is an accepted-step average, not a continuous integral.
