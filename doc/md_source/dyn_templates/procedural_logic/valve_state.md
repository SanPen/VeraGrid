# Valve state

<!-- veragrid-block-introduction:start -->
**Valve state** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Purpose

Determines the retained conduction state of a controlled electrical valve from its type, gate command, antiparallel option, voltage and current.

## Configuration

- **Output mode**: retained conduction-path state.
- **Valve type**, **Gate command**, **Antiparallel enabled**: runtime control parameters.
- **Voltage deadband**, **Current deadband**: runtime numerical tolerances.
- **Valve voltage**, **Valve current**: measured DAE variables.

## Runtime behavior

The state machine applies valve-specific turn-on, turn-off and reverse-path rules at accepted boundaries. Deadbands prevent numerical chatter near zero. All references are mandatory and must identify symbols compiled into the same dynamic system.
