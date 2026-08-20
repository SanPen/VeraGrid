# Startup handover

<!-- veragrid-block-introduction:start -->
**Startup handover** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Switches a retained startup mode according to a runtime enable-time parameter.

## Configuration

- **Output mode**: retained startup/handover selector.
- **Enable-time parameter**: runtime parameter containing the transition time.

## Runtime behavior

Before the configured time the startup path remains selected; at the boundary the mode changes to the normal-operation path. The entry participates in event-boundary scheduling so the handover can occur at the requested time rather than only at the end of a larger step.
