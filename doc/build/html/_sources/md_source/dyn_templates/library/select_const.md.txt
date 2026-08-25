# Select const

<!-- veragrid-block-introduction:start -->
**Select const** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

### Purpose

This block selects one signal using a fixed selector parameter instead of a runtime selector input.

### Behavior

- Receives several candidate signals.
- Uses one parameter to choose which one is passed to the output.

### Characteristics

- Useful when the selection must be fixed for one model instance.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `s1` | First candidate input signal | model-dependent |
| Input | `s2` | Second candidate input signal | model-dependent |
| Output | `yo` | Selected output signal | model-dependent |
| Parameter | `sel` | Fixed selector deciding which input is used | integer or boolean |

## How to use it

- Use this block when the selected path is known at design time and should not change at runtime.
