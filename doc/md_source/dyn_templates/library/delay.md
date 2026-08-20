# Delay

<!-- veragrid-block-introduction:start -->
**Delay** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

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
