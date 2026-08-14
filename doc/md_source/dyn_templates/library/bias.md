# Bias

### Purpose

This block adds one constant offset to a signal.

### Behavior

- Receives one signal.
- Adds one bias term.
- Outputs the shifted signal.

## Characteristic equations

$$
y = x + b
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Biased output signal | model-dependent |
| Parameter | `b` | Constant offset added to the input | model-dependent |

## How to use it

- Use this block when a signal must be shifted by a constant amount.
