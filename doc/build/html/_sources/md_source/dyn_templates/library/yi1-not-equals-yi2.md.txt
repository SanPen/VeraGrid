# yi1 not equals yi2

<!-- veragrid-block-introduction:start -->
**yi1 not equals yi2** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

`yi1 not equals yi2` outputs true when the two input signals differ.

$$
yo = (yi1 \ne yi2)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First signal | model-dependent |
| Input | `yi2` | Second signal | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
