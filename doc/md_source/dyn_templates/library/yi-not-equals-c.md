# yi not equals C

<!-- veragrid-block-introduction:start -->
**yi not equals C** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

`yi not equals C` outputs true when the input differs from the configured constant.

$$
yo = (yi \ne C)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal being compared | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
| Parameter | `C` | Constant comparison value | model-dependent |
