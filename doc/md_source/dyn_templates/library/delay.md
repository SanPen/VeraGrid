# Delay

### Purpose

This block reproduces an input after one time delay.

### Behavior

- Receives one input signal.
- Outputs the same signal delayed in time.

## Characteristic equations

$$
y(t) = x(t-T_d)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal to be delayed | model-dependent |
| Output | `yo` | Delayed output signal | model-dependent |
| Parameter | `Td` | Delay time | s |

## How to use it

- Use this block when a transport-like delay or waiting behavior is needed in a dynamic model.
