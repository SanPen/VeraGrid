# Analog flip-flop

<!-- veragrid-block-introduction:start -->
**Analog flip-flop** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Implements a set/reset latch that captures and retains an analog input value.

## Configuration

- **Output mode**: retained analog value.
- **Input expression**: value captured when Set activates.
- **Set condition**: captures and holds the input.
- **Reset condition**: releases the active latch state.

## Runtime behavior

The input is sampled when the latch is initialized or transitions into the set state. It is not continuously tracked while held. Order matters if the input expression reads modes written earlier in the same update.
