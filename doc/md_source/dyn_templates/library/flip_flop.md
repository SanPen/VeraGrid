# Flip-flop

### Purpose

A flip-flop block stores one logical state and changes that state based on set/reset-like inputs.

### Behavior

- Receives logical or thresholded trigger inputs.
- Keeps memory of the last accepted logical state.
- Outputs one stored boolean-like or discrete state.

### Characteristics

- Useful in protection logic, interlocks, and event sequencing.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `set` | Input that activates or sets the stored state | boolean or 0/1 |
| Input | `reset` | Input that deactivates or resets the stored state | boolean or 0/1 |
| Output | `yo` | Stored logical output | boolean or 0/1 |
| Variable | `state` | Internal remembered logic state | boolean or 0/1 |

## How to use it

- Use it when a control scheme needs memory or latching behavior.
- Combine it with comparators, timers, or deadbands in logic chains.
