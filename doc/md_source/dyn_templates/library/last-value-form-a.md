# Last value [form A]

<!-- veragrid-block-introduction:start -->
**Last value [form A]** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

`Last value [form A]` holds and repeats the most recently sampled input value.

$$
yo(t) = yi(t^-)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Incoming signal to store | model-dependent |
| Output | `yo` | Most recently stored value | model-dependent |
