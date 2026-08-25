# Switch EMT

<!-- veragrid-block-introduction:start -->
**Switch EMT** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

Phase-selective EMT switching element for opening or closing a branch path. The
default model contains phases A, B, and C and leaves neutral absent.

## Behavior

The switch changes between a high closed conductance and a small open leakage
conductance. It can obtain its initial mode from the associated static switch or
from the configured default. When signal control is enabled, an external command
is compared with a threshold and drives the switching logic.

A short first-order current time constant regularizes the transition and avoids
an instantaneous discontinuity in the EMT equations.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `cmd` | Open or close command | bool |
| Terminal | `p` | Positive electrical terminal | model-dependent |
| Terminal | `n` | Negative electrical terminal | model-dependent |
| Parameter | `Ron` | Closed-state resistance | ohm |
| Parameter | `Roff` | Open-state resistance | ohm |

## Main settings

| Setting | Meaning |
| --- | --- |
| `signal_controlled` | Expose and use the external switching command |
| `seed_from_pf_active` | Initialize the mode from the static switch state |
| `initial_closed` | Fallback initial mode when static seeding is disabled |
| `closed conductance` | Conductance used while closed |
| `open conductance` | Leakage conductance used while open |
| `switch time constant` | Current-transition regularization time |

## How to use it

- Match enabled phases to the branch topology.
- Keep open conductance small but non-negative and closed conductance finite.
- Enable signal control only when a valid command block is connected.
