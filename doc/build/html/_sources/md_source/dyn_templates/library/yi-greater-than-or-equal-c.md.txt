# yi greater than or equal C

<!-- veragrid-block-introduction:start -->
**yi greater than or equal C** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

`yi greater than or equal C` outputs true when the input is at least the configured constant.

$$
yo = (yi \ge C)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal being compared | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
| Parameter | `C` | Constant threshold | model-dependent |
