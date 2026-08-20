# Sampled value

<!-- veragrid-block-introduction:start -->
**Sampled value** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Evaluates a symbolic source at every accepted solver boundary and copies its numeric value into a retained mode.

## Configuration

- **Output mode**: retained destination.
- **Source expression**: DAE variables, parameters, time-dependent expressions or previously updated modes.

## Runtime behavior

The value is piecewise constant between accepted updates. Order matters when the source reads a mode written by another procedural entry in the same block.
