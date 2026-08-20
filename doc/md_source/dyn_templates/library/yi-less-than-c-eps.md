# yi less than C eps

<!-- veragrid-block-introduction:start -->
**yi less than C eps** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

`yi less than C eps` compares the input against a constant with an epsilon margin on the low side.

$$
yo = (yi < C - eps)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal being compared | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
| Parameter | `C` | Constant threshold | model-dependent |
| Parameter | `eps` | Comparison margin | model-dependent |
