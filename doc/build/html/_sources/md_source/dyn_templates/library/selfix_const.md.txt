# Selfix const

<!-- veragrid-block-introduction:start -->
**Selfix const** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

### Purpose

This block keeps or fixes one selected signal path according to one constant selector parameter.

### Behavior

- Receives candidate signals.
- Uses one fixed selection parameter.
- Outputs the selected path.

### Characteristics

- Useful for fixed routing choices in reusable templates.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `s1` | First candidate signal | model-dependent |
| Input | `s2` | Second candidate signal | model-dependent |
| Output | `yo` | Selected output signal | model-dependent |
| Parameter | `sel` | Fixed selector parameter | integer or boolean |

## How to use it

- Use this block when the signal route should remain fixed for one template instance.
