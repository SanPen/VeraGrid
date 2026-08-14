# Timer

### Purpose

This block measures elapsed time associated with one event or condition.

### Behavior

- Starts or continues timing when its condition is active.
- Can support reset, hold, or restart variants depending on the exact template.
- Outputs elapsed time or a timer-related logic signal.

## Characteristic equations

$$
\frac{d\tau}{dt} = 1
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `trigger` | Event or condition that activates timer behavior | boolean, 0/1, or model-dependent |
| Output | `yo` | Timer output or elapsed-time-related signal | model-dependent |
| Variable | `tau` | Internal elapsed-time state | s |
| Parameter | `Treset` | Reset-related timing parameter in reset-capable variants | s |

## How to use it

- Use this block in sequence logic, protection logic, and timing-based mode transitions.
