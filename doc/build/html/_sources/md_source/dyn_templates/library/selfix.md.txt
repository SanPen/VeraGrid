# Selfix

<!-- veragrid-block-introduction:start -->
**Selfix** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

### Purpose

This block keeps or fixes one selected signal path according to one runtime condition.

### Behavior

- Receives candidate signals and one runtime selection condition.
- Outputs the chosen signal.

### Characteristics

- Useful in supervisory logic when the active signal path depends on operating conditions.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `s1` | First candidate signal | model-dependent |
| Input | `s2` | Second candidate signal | model-dependent |
| Input | `sel` | Runtime selection signal | integer, boolean, or model-dependent |
| Output | `yo` | Selected output signal | model-dependent |

## How to use it

- Use this block when a signal path must be selected dynamically during simulation.
